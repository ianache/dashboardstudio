"""
Email Executor Service - Core execution engine for email node operations.

This module provides the EmailExecutor class for secure email sending with
Jinja2 templating, HTML sanitization, and SMTP delivery.

Security Features:
    - Jinja2 SandboxedEnvironment prevents code injection
    - Auto-escaping prevents XSS vulnerabilities
    - nh3 HTML sanitization removes dangerous tags
    - DataSource-based credential resolution

Usage:
    from app.services.email_executor import EmailExecutor, email_executor
    from app.services.email_schemas import EmailConfig, EmailContent, EmailPayload
    
    # Direct usage
    executor = EmailExecutor()
    result = executor.render_template("Hello {{name}}!", {"name": "World"})
    
    # With DataSource
    payload = EmailPayload(...)
    result = executor.execute(payload, db_session)

Dependencies:
    - Jinja2>=3.1.6: Template engine with SandboxedEnvironment
    - nh3>=0.3.5: HTML sanitization (bleach replacement)
    - smtplib: SMTP protocol implementation

See Also:
    - email_schemas.py: Pydantic models for configuration
    - PITFALLS.md: Security considerations and best practices
"""

import json
import logging
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union

import nh3
from jinja2 import Undefined, UndefinedError
from jinja2.sandbox import SandboxedEnvironment

from app.services.email_schemas import EmailConfig, EmailContent, EmailPayload, EmailResult

logger = logging.getLogger(__name__)


class UndefinedSilently(Undefined):
    """Custom undefined handler that returns empty string silently.
    
    Unlike StrictUndefined which raises errors, this class silently
    returns empty strings for undefined variables, allowing templates
    to render gracefully even with missing data.
    
    Example:
        {{missing_var}} renders as empty string instead of error
    """
    
    __slots__ = ()
    
    def __str__(self) -> str:
        return ""
    
    def __repr__(self) -> str:
        return ""
    
    def __bool__(self) -> bool:
        return False
    
    def __getattr__(self, name: str) -> "UndefinedSilently":
        """Return self for any attribute access (handles nested undefined)."""
        return self.__class__(hint=name, obj=self, name=name)
    
    def __getitem__(self, key: Any) -> "UndefinedSilently":
        """Return self for any item access."""
        return self.__class__(hint=str(key), obj=self, name=str(key))
    
    def __iter__(self):
        """Return empty iterator for for-loop compatibility."""
        return iter([])
    
    def __len__(self) -> int:
        """Return 0 length."""
        return 0
    
    def __html__(self):
        """Return empty string for autoescape compatibility."""
        return ""


class EmailExecutor:
    """Core executor for email sending operations.
    
    This class provides secure email template rendering and SMTP delivery
    with the following security features:
    
    1. SandboxedEnvironment: Prevents code injection in templates
    2. Auto-escaping: Prevents XSS in rendered HTML
    3. HTML sanitization: Removes dangerous tags with nh3
    4. Email validation: Validates recipient addresses
    
    Key Methods:
        render_template(): Securely render Jinja2 templates
        sanitize_html(): Clean HTML with nh3
        validate_email_addresses(): Validate recipient emails
        send_email(): Send via SMTP with multipart support
        execute(): Main entry point with DataSource resolution
    
    Thread Safety:
        This class is stateless except for the Jinja environment which is
        read-only after initialization. Safe for concurrent use.
    
    Example:
        executor = EmailExecutor()
        
        # Render template
        html = executor.render_template(
            "<p>Hello {{user.name}}</p>",
            {"user": {"name": "John"}}
        )
        
        # Send email (mocked for testing)
        config = EmailConfig(...)
        content = EmailContent(subject="Test", body=html)
        result = executor.send_email(config, content, ["to@example.com"], {})
    """
    
    # nh3 allowed tags - balanced for email client compatibility
    ALLOWED_TAGS = {
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'strike', 'del',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li',
        'a', 'img',
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
        'div', 'span', 'blockquote', 'pre', 'code',
        'hr', 'sub', 'sup'
    }
    
    # nh3 allowed attributes - mapping of tag -> set of allowed attributes
    ALLOWED_ATTRIBUTES = {
        'a': {'href', 'title'},
        'img': {'src', 'alt', 'width', 'height'},
        'th': {'colspan', 'rowspan', 'headers'},
        'td': {'colspan', 'rowspan', 'headers'},
        '*': {'style', 'class', 'id', 'align', 'valign', 'border', 'cellpadding', 'cellspacing'},
    }
    
    # Email validation regex per PITFALLS.md
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(self):
        """Initialize EmailExecutor with Jinja2 SandboxedEnvironment.
        
        Creates a sandboxed environment with:
        - Auto-escaping enabled for XSS prevention
        - UndefinedSilently for graceful handling of missing variables
        - Optimized configuration for email templating
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize SandboxedEnvironment for security
        # SandboxedEnvironment prevents access to unsafe Python functions
        self.env = SandboxedEnvironment(
            autoescape=True,  # Critical: auto-escape HTML to prevent XSS
            undefined=UndefinedSilently,  # Return empty string for undefined vars
            trim_blocks=True,  # Remove first newline after block
            lstrip_blocks=True,  # Strip leading whitespace
            enable_async=False,  # We don't need async template rendering
        )
        
        self.logger.debug("EmailExecutor initialized with SandboxedEnvironment")
    
    def render_template(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template string with the given context.
        
        Uses SandboxedEnvironment for security and handles undefined
        variables gracefully by returning empty strings.
        
        Args:
            template_str: Jinja2 template with {{variables}} and {%control%}
            context: Dictionary of data to populate template variables
        
        Returns:
            Rendered template string with all variables substituted
        
        Raises:
            ValueError: If template syntax is invalid
        
        Example:
            executor = EmailExecutor()
            result = executor.render_template(
                "Hello {{user.name}}!",
                {"user": {"name": "John"}}
            )
            # Returns: "Hello John!"
        
        Security:
            - SandboxedEnvironment prevents code injection
            - Auto-escaping prevents XSS in output
        """
        try:
            template = self.env.from_string(template_str)
            return template.render(**context)
        except UndefinedError as e:
            # This shouldn't happen with UndefinedSilently, but handle gracefully
            self.logger.warning(f"Template rendered with undefined: {e}")
            return template_str
        except Exception as e:
            # Re-raise with clear context for debugging
            error_msg = f"Template rendering failed: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def validate_email_addresses(self, addresses: List[str]) -> List[str]:
        """Validate and normalize email addresses.
        
        Validates each email against RFC-compliant pattern, normalizes
domain to lowercase, and filters out invalid addresses.
        
        Args:
            addresses: List of email address strings
        
        Returns:
            List of valid, normalized email addresses
        
        Example:
            executor = EmailExecutor()
            valid = executor.validate_email_addresses([
                "User@EXAMPLE.COM",
                "invalid-email",
                "good@test.org"
            ])
            # Returns: ["User@example.com", "good@test.org"]
        
        Notes:
            - Domain is lowercased for consistency
            - Local part preserves case (per RFC)
            - Invalid emails are logged as warnings and filtered out
        """
        if not addresses:
            return []
        
        valid_addresses = []
        
        for addr in addresses:
            if not addr or not isinstance(addr, str):
                continue
                
            addr = addr.strip()
            if not addr:
                continue
            
            # Validate with regex
            if not self.EMAIL_PATTERN.match(addr):
                self.logger.warning(f"Invalid email address filtered: {addr}")
                continue
            
            # Normalize domain to lowercase
            if '@' in addr:
                local, domain = addr.rsplit('@', 1)
                normalized = f"{local}@{domain.lower()}"
                valid_addresses.append(normalized)
            else:
                # Shouldn't happen due to regex, but handle defensively
                self.logger.warning(f"Email missing @ symbol: {addr}")
        
        return valid_addresses
    
    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML content using nh3.
        
        Removes dangerous tags and attributes while preserving safe
        HTML for email rendering. This is a critical security measure
        to prevent XSS and other injection attacks.
        
        Args:
            html: Raw HTML string that may contain dangerous content
        
        Returns:
            Sanitized HTML safe for email rendering
        
        Example:
            executor = EmailExecutor()
            safe = executor.sanitize_html(
                "<script>alert('xss')</script><p>Safe content</p>"
            )
            # Returns: "<p>Safe content</p>" (script removed)
        
        Security:
            - Removes <script>, <style>, and other dangerous tags
            - Strips event handlers (onclick, onerror, etc.)
            - Preserves safe formatting tags for email
        """
        if not html:
            return ""
        
        try:
            sanitized = nh3.clean(
                html,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                strip_comments=True,  # Remove HTML comments
            )
            return sanitized
        except Exception as e:
            self.logger.error(f"HTML sanitization failed: {e}")
            # Fallback: return escaped text
            import html as html_module
            return html_module.escape(html)
    
    def _create_plain_text_fallback(self, html: str) -> str:
        """Create plain text fallback from HTML content.
        
        Simple conversion that removes HTML tags and converts
        common elements to text equivalents.
        
        Args:
            html: HTML content
        
        Returns:
            Plain text version
        """
        import html as html_module
        
        # Remove style and script blocks first
        text = re.sub(r'<(script|style)[^>]*>[^<]*</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert block elements to newlines
        text = re.sub(r'</(p|div|h[1-6]|li|tr)>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        text = html_module.unescape(text)
        
        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces
        
        return text.strip()
    
    def send_email(
        self,
        config: EmailConfig,
        content: EmailContent,
        to: List[str],
        context: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> EmailResult:
        """Send an email using SMTP.
        
        Renders templates, sanitizes HTML, creates multipart message,
        and sends via SMTP with proper error handling.
        
        Args:
            config: SMTP configuration with credentials
            content: EmailContent with subject and body templates
            to: Primary recipient list
            context: Template rendering context
            cc: Optional CC recipients
            bcc: Optional BCC recipients
        
        Returns:
            EmailResult with success status and delivery info
        
        Example:
            config = EmailConfig(
                connection_id="conn-123",
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                smtp_user="me@gmail.com",
                smtp_password="app-password",
                from_address="me@gmail.com"
            )
            content = EmailContent(
                subject="Hello {{name}}",
                body="<p>Welcome, {{name}}!</p>"
            )
            result = executor.send_email(
                config, content,
                to=["friend@example.com"],
                context={"name": "John"}
            )
        
        Security:
            - Templates are auto-escaped during rendering
            - HTML body is sanitized with nh3
            - SMTP password is never logged
        """
        start_time = time.time()
        
        try:
            # Validate recipients
            to_valid = self.validate_email_addresses(to or [])
            cc_valid = self.validate_email_addresses(cc or [])
            bcc_valid = self.validate_email_addresses(bcc or [])
            
            all_recipients = to_valid + cc_valid + bcc_valid
            
            if not all_recipients:
                return EmailResult(
                    success=False,
                    error="No valid recipients provided",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            if not to_valid:
                return EmailResult(
                    success=False,
                    error="No valid 'to' recipients provided",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # Render templates
            subject = self.render_template(content.subject, context)
            body_html = self.render_template(content.body, context)
            
            # Sanitize HTML if format is html
            if content.format == "html":
                body_html = self.sanitize_html(body_html)
                body_text = self._create_plain_text_fallback(body_html)
            else:
                body_text = body_html
                body_html = None
            
            # Create multipart message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = config.from_address
            msg['To'] = ', '.join(to_valid)
            
            if cc_valid:
                msg['Cc'] = ', '.join(cc_valid)
            
            # Attach plain text part
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            
            # Attach HTML part if available
            if body_html:
                msg.attach(MIMEText(body_html, 'html', 'utf-8'))
            
            # Send via SMTP
            recipients = to_valid + cc_valid + bcc_valid
            
            # Determine if we should use implicit SSL (SMTP_SSL) or STARTTLS
            # Port 465 is the standard implicit SSL port.
            if config.smtp_use_ssl and config.smtp_port == 465:
                smtp_server_class = smtplib.SMTP_SSL
            else:
                smtp_server_class = smtplib.SMTP

            with smtp_server_class(config.smtp_host, config.smtp_port, timeout=config.timeout) as server:
                # For non-465 ports with SSL enabled, we start TLS explicitly (STARTTLS)
                if config.smtp_use_ssl and config.smtp_port != 465:
                    server.starttls()
                
                server.login(config.smtp_user, config.smtp_password)
                server.send_message(msg, to_addrs=recipients)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.logger.info(
                f"Email sent successfully to {len(recipients)} recipients "
                f"via {config.smtp_host} in {duration_ms}ms"
            )
            
            return EmailResult(
                success=True,
                message_id=msg.get('Message-ID'),
                recipients_count=len(recipients),
                duration_ms=duration_ms
            )
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                error=error_msg,
                recipients_count=0,
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            error_msg = f"Email sending failed: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                error=error_msg,
                recipients_count=0,
                duration_ms=int((time.time() - start_time) * 1000)
            )
    
    def execute(self, payload: EmailPayload, db: Any) -> EmailResult:
        """Execute email sending from node payload.
        
        Main entry point for email node execution. Resolves SMTP credentials
        from encrypted DataSource, renders templates, and sends email.
        
        Args:
            payload: EmailPayload with node configuration and templates
            db: Database session for DataSource resolution
        
        Returns:
            EmailResult with execution status
        
        Example:
            # From Deno service signal handler
            payload = EmailPayload(
                node_id="email-123",
                target={"connection_id": "smtp-456", "to": "user@test.com"},
                content=EmailContent(subject="Hi", body="<p>Hello</p>"),
                metadata={"execution_id": "exec-789", "flow_id": "flow-abc", "timestamp": "..."},
                template_context={"user": {"name": "John"}}
            )
            result = executor.execute(payload, db_session)
        
        Flow:
            1. Query DataSource by connection_id
            2. Decrypt connection_url to get SMTP config
            3. Build EmailConfig from credentials
            4. Send email with rendered templates
            5. Return EmailResult
        
        Error Handling:
            - Returns error result if DataSource not found
            - Returns error result if credentials invalid
            - Catches all exceptions and returns EmailResult
        """
        start_time = time.time()
        
        try:
            # Import models here to avoid circular imports
            from app.models.models import DataSource
            from app.core.encryption import process_sensitive_fields
            
            # Resolve DataSource
            connection_id = payload.target.get('connection_id')
            if not connection_id:
                return EmailResult(
                    success=False,
                    error="No connection_id specified in target",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            ds = db.query(DataSource).filter(DataSource.id == connection_id).first()
            
            if not ds:
                return EmailResult(
                    success=False,
                    error=f"DataSource not found: {connection_id}",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # Parse and decrypt connection config
            try:
                raw_config = json.loads(ds.connection_url)
                config_dict = process_sensitive_fields(raw_config, action="decrypt")
            except json.JSONDecodeError as e:
                return EmailResult(
                    success=False,
                    error=f"Invalid DataSource configuration format: {e}",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            except Exception as e:
                return EmailResult(
                    success=False,
                    error=f"Failed to decrypt DataSource configuration: {e}",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # Build EmailConfig from DataSource
            try:
                email_config = EmailConfig(
                    connection_id=connection_id,
                    smtp_host=config_dict.get('host', config_dict.get('smtp_host', '')),
                    smtp_port=int(config_dict.get('port', config_dict.get('smtp_port', 587))),
                    smtp_use_ssl=config_dict.get('use_ssl', config_dict.get('smtp_use_ssl', True)),
                    smtp_user=config_dict.get('user', config_dict.get('smtp_user', config_dict.get('email', ''))),
                    smtp_password=config_dict.get('password', config_dict.get('smtp_password', '')),
                    from_address=config_dict.get('from_address', config_dict.get('from', config_dict.get('user', config_dict.get('email', '')))),
                    timeout=int(config_dict.get('timeout', 30))
                )
            except Exception as e:
                return EmailResult(
                    success=False,
                    error=f"Invalid SMTP configuration: {e}",
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            
            # Extract recipients
            to = payload.target.get('to', [])
            if isinstance(to, str):
                to = [to]
            
            cc = payload.target.get('cc', [])
            if isinstance(cc, str):
                cc = [cc]
            
            bcc = payload.target.get('bcc', [])
            if isinstance(bcc, str):
                bcc = [bcc]
            
            # Build context from metadata and template_context
            context = {
                **payload.metadata,
                **payload.template_context
            }
            
            # Send email
            return self.send_email(
                config=email_config,
                content=payload.content,
                to=to,
                cc=cc,
                bcc=bcc,
                context=context
            )
            
        except Exception as e:
            error_msg = f"Email execution failed: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                error=error_msg,
                duration_ms=int((time.time() - start_time) * 1000)
            )


# Singleton instance for convenience
email_executor = EmailExecutor()
