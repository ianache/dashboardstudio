"""
Email Schemas - Pydantic models for email node execution.

This module provides Pydantic models for email configuration, payload, content,
and results. It follows the same patterns as ODS executor but uses Pydantic
for better validation and serialization.

Usage:
    from app.services.email_schemas import (
        EmailConfig,
        EmailContent,
        EmailPayload,
        EmailResult,
    )
    
    config = EmailConfig(
        connection_id="conn-123",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        from_address="sender@example.com",
    )
"""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class EmailContent(BaseModel):
    """Email content with subject and body templates.
    
    Attributes:
        subject: Template string for email subject (can contain {{variables}})
        body: Template string for email body (can contain {{variables}} and Jinja2 syntax)
        format: Content format - "html" or "text"
    
    Example:
        content = EmailContent(
            subject="Welcome {{user.name}}!",
            body="<h1>Hello {{user.name}}</h1><p>Your order #{{order.id}} is ready.</p>",
            format="html"
        )
    """
    subject: str = Field(..., description="Email subject template")
    body: str = Field(..., description="Email body template")
    format: Literal["html", "text"] = Field(
        default="html",
        description="Content format: html or text"
    )

    @field_validator('subject')
    @classmethod
    def subject_not_empty(cls, v: str) -> str:
        """Validate subject is not empty."""
        if not v or not v.strip():
            raise ValueError("Email subject cannot be empty")
        return v.strip()

    @field_validator('body')
    @classmethod
    def body_not_empty(cls, v: str) -> str:
        """Validate body is not empty."""
        if not v or not v.strip():
            raise ValueError("Email body cannot be empty")
        return v


class EmailPayload(BaseModel):
    """Payload for email node execution.
    
    This model represents the complete input for sending an email,
    including target configuration, content templates, and context data.
    
    Attributes:
        node_id: Unique identifier for the email node
        target: Target configuration dict with connection_id, to, cc, bcc
        content: EmailContent with subject and body templates
        metadata: Execution metadata (execution_id, flow_id, timestamp)
        template_context: Data dictionary for template rendering
    
    Example:
        payload = EmailPayload(
            node_id="email-node-123",
            target={
                "connection_id": "smtp-conn-456",
                "to": "recipient@example.com",
                "cc": "cc@example.com",
            },
            content=EmailContent(
                subject="Order {{order.id}} Confirmation",
                body="<p>Dear {{customer.name}},...</p>"
            ),
            metadata={
                "execution_id": "exec-789",
                "flow_id": "flow-abc",
                "timestamp": "2026-01-15T10:00:00Z"
            },
            template_context={
                "customer": {"name": "John Doe"},
                "order": {"id": "12345"}
            }
        )
    """
    node_id: str = Field(..., description="Unique node identifier")
    target: Dict[str, Any] = Field(
        ...,
        description="Target configuration: connection_id, to, cc, bcc"
    )
    content: EmailContent = Field(..., description="Email subject and body templates")
    metadata: Dict[str, Any] = Field(
        ...,
        description="Execution metadata: execution_id, flow_id, timestamp"
    )
    template_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data for template rendering (from upstream nodes)"
    )

    @field_validator('node_id')
    @classmethod
    def node_id_not_empty(cls, v: str) -> str:
        """Validate node_id is not empty."""
        if not v or not v.strip():
            raise ValueError("node_id cannot be empty")
        return v.strip()

    @field_validator('target')
    @classmethod
    def target_has_required_fields(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate target has required fields."""
        if 'connection_id' not in v:
            raise ValueError("target must contain 'connection_id'")
        if 'to' not in v:
            raise ValueError("target must contain 'to' recipient")
        if not v.get('to'):
            raise ValueError("target 'to' cannot be empty")
        return v


class EmailResult(BaseModel):
    """Result of an email sending operation.
    
    This model captures the outcome of email execution including
    success status, message ID, errors, and performance metrics.
    
    Attributes:
        success: True if email was sent successfully
        message_id: Optional SMTP message ID for tracking
        error: Error message if sending failed
        recipients_count: Number of recipients (to + cc + bcc)
        duration_ms: Execution time in milliseconds
    
    Example:
        # Success case
        result = EmailResult(
            success=True,
            message_id="<abc123@example.com>",
            recipients_count=3,
            duration_ms=1250
        )
        
        # Failure case
        result = EmailResult(
            success=False,
            error="SMTP authentication failed: Invalid credentials",
            duration_ms=500
        )
    """
    success: bool = Field(
        ...,
        description="True if email was sent successfully"
    )
    message_id: Optional[str] = Field(
        default=None,
        description="SMTP message ID for tracking"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if sending failed"
    )
    recipients_count: int = Field(
        default=0,
        ge=0,
        description="Number of recipients (to + cc + bcc)"
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Execution duration in milliseconds"
    )


class EmailConfig(BaseModel):
    """SMTP configuration for email sending.
    
    This model holds all SMTP connection settings needed to send emails.
    Credentials are resolved from encrypted DataSource storage.
    
    Attributes:
        connection_id: DataSource connection identifier
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_use_ssl: Use SSL/TLS encryption (default: True)
        smtp_user: SMTP authentication username
        smtp_password: SMTP authentication password
        from_address: Sender email address
        timeout: Connection timeout in seconds (default: 30)
    
    Example:
        config = EmailConfig(
            connection_id="smtp-gmail-123",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="myapp@gmail.com",
            smtp_password="app-specific-password",
            from_address="noreply@myapp.com",
            timeout=30
        )
    
    Security Notes:
        - Passwords should be stored encrypted in DataSource
        - Use app-specific passwords for Gmail and similar services
        - Consider using STARTTLS on port 587 instead of SSL on 465
    """
    connection_id: str = Field(
        ...,
        description="DataSource connection identifier"
    )
    smtp_host: str = Field(
        ...,
        description="SMTP server hostname"
    )
    smtp_port: int = Field(
        ...,
        gt=0,
        le=65535,
        description="SMTP server port (1-65535)"
    )
    smtp_use_ssl: bool = Field(
        default=True,
        description="Use SSL/TLS encryption"
    )
    smtp_user: str = Field(
        ...,
        description="SMTP authentication username"
    )
    smtp_password: str = Field(
        ...,
        description="SMTP authentication password"
    )
    from_address: str = Field(
        ...,
        description="Sender email address"
    )
    timeout: int = Field(
        default=30,
        gt=0,
        le=300,
        description="Connection timeout in seconds (1-300)"
    )

    @field_validator('connection_id')
    @classmethod
    def connection_id_not_empty(cls, v: str) -> str:
        """Validate connection_id is not empty."""
        if not v or not v.strip():
            raise ValueError("connection_id cannot be empty")
        return v.strip()

    @field_validator('smtp_host')
    @classmethod
    def smtp_host_not_empty(cls, v: str) -> str:
        """Validate smtp_host is not empty."""
        if not v or not v.strip():
            raise ValueError("smtp_host cannot be empty")
        return v.strip()

    @field_validator('smtp_user')
    @classmethod
    def smtp_user_not_empty(cls, v: str) -> str:
        """Validate smtp_user is not empty."""
        if not v or not v.strip():
            raise ValueError("smtp_user cannot be empty")
        return v.strip()

    @field_validator('smtp_password')
    @classmethod
    def smtp_password_not_empty(cls, v: str) -> str:
        """Validate smtp_password is not empty."""
        if not v:
            raise ValueError("smtp_password cannot be empty")
        return v

    @field_validator('from_address')
    @classmethod
    def from_address_not_empty(cls, v: str) -> str:
        """Validate from_address is not empty."""
        if not v or not v.strip():
            raise ValueError("from_address cannot be empty")
        return v.strip()

    @field_validator('from_address')
    @classmethod
    def from_address_valid_email(cls, v: str) -> str:
        """Basic email format validation."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip()):
            raise ValueError(f"from_address must be a valid email address: {v}")
        return v.strip()


# Type aliases for clarity
EmailAddress = str
EmailTemplate = str
