# Technology Stack: Email Node with Dynamic Templates

**Project:** Dashboard Studio - Email Node Implementation  
**Milestone:** v1.7 Email Node with Dynamic Templates  
**Researched:** 2026-05-16  
**Confidence:** HIGH

## Executive Summary

This document outlines the recommended technology stack additions for implementing an Email Node with dynamic templating support in the existing Dashboard Studio application. The stack builds upon the existing FastAPI backend and DataSource infrastructure (which already supports SMTP connections), adding minimal, well-established libraries for email composition, template rendering, and HTML sanitization.

**Key Decision:** Use standard library `smtplib` + `email.mime` for SMTP (since DataSource already manages connections), Jinja2 with SandboxedEnvironment for templating, and `nh3` for HTML sanitization.

---

## Recommended Stack

### 1. SMTP & Email Composition

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `smtplib` | Python stdlib | SMTP protocol client | Already available; battle-tested; integrates seamlessly with existing DataSource SMTP connections |
| `email.mime` | Python stdlib | MIME message construction | Standard library; supports multipart messages (HTML + text); attachments |
| `aiosmtplib` | ^3.0.0 | Async SMTP (optional upgrade) | Only if async email sending becomes a requirement; otherwise smtplib is sufficient |

**Decision Rationale:**

The Connection Management milestone already implemented SMTP DataSource support with connection pooling and credential management. Using `smtplib` directly is the simplest integration path:

1. **No additional dependencies** - smtplib is part of Python standard library
2. **Direct DataSource integration** - The existing DataSource system retrieves SMTP credentials; smtplib can use them directly
3. **Synchronous execution fits the flow runner** - The Python flow runner with APScheduler executes nodes synchronously
4. **Proven reliability** - smtplib has been part of Python since 1999 and handles all modern SMTP requirements (STARTTLS, AUTH, UTF-8)

**When to consider `aiosmtplib`:**
- If the flow runner is refactored to async/await
- If bulk email sending (1000s of emails) becomes a requirement
- If non-blocking email sending during flow execution is needed

### 2. Template Engines

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `Jinja2` | ^3.1.6 | Primary template engine | Industry standard; SandboxedEnvironment for security; rich feature set; excellent for complex templates with loops/conditionals |
| `chevron` | ^0.14.0 | Mustache syntax alternative | If strict `{{variable}}` Mustache compatibility is required; lighter weight; logic-less templates |

**Decision Rationale:**

**Jinja2 is the primary recommendation** for the following reasons:

1. **Rich expression support** - Handles complex scenarios like:
   - Array iteration for table generation: `{% for row in data %}`
   - Conditionals: `{% if user.is_active %}`
   - Filters: `{{ name \| title }}`, `{{ date \| format_date }}`
   - Custom functions for data transformation

2. **Security with SandboxedEnvironment** - Prevents code execution:
   ```python
   from jinja2.sandbox import SandboxedEnvironment
   env = SandboxedEnvironment()
   template = env.from_string("{{ user.name }}")
   ```

3. **Familiar syntax** - The `{{expression}}` syntax requested in the milestone is native to Jinja2

4. **Wide adoption** - Used by Flask, Ansible, SaltStack; extensive documentation and community

**Alternative: Chevron (Mustache)**
- Use if templates should be strictly logic-less (no conditionals/loops in templates)
- Simpler mental model for non-technical users
- Less powerful for complex table generation from arrays

**Template Syntax Comparison:**

| Feature | Jinja2 | Chevron (Mustache) |
|---------|--------|-------------------|
| Variables | `{{ user.name }}` | `{{ user.name }}` |
| Loops | `{% for item in items %}` | `{{#items}}` |
| Conditionals | `{% if condition %}` | Not supported |
| Filters | `{{ name \| upper }}` | Not supported |
| Partials | `{% include 'partial' %}` | `{{> partial}}` |

### 3. HTML Sanitization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `nh3` | ^0.3.5 | HTML sanitization | 20x faster than bleach; actively maintained; Rust-based; strict allow-list approach |

**Decision Rationale:**

**nh3 replaces the deprecated `bleach` library** (officially deprecated as of January 2023). Key advantages:

1. **Performance** - ~20x faster than bleach in benchmarks
2. **Security** - Rust-based ammonia library under the hood; memory-safe
3. **Active maintenance** - Regular releases (latest: April 2026)
4. **Flexible allow-list configuration**:
   ```python
   import nh3
   # Allow only safe email-friendly tags
   clean_html = nh3.clean(
       raw_html,
       tags={"p", "br", "strong", "em", "a", "ul", "ol", "li", "table", "tr", "td", "th"},
       attributes={"a": {"href"}, "*": {"class"}},
       url_schemes={"https", "http", "mailto"}
   )
   ```

**Security considerations:**
- Always sanitize HTML body content before sending
- Prevent XSS in email clients that execute JavaScript
- Strip potentially dangerous attributes (onerror, onclick, etc.)

### 4. Integration Libraries

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `fastapi-mail` | ^1.6.4 | FastAPI integration (optional) | Only if refactoring to use a higher-level abstraction; currently not needed |

**Decision:** Skip `fastapi-mail` for now. The existing DataSource + smtplib approach is simpler and sufficient. Consider `fastapi-mail` only if:
- Email sending needs to happen outside the flow runner (direct API endpoints)
- Built-in template rendering with Jinja2 integration is desired
- Connection pooling at the email library level becomes necessary

---

## Installation

### Minimal Setup (Recommended)

```bash
# Core dependencies (only 2 external packages needed)
pip install Jinja2==3.1.6 nh3==0.3.5
```

### With Optional Async Support

```bash
# If async SMTP becomes a requirement
pip install Jinja2==3.1.6 nh3==0.3.5 aiosmtplib==3.0.0
```

### Requirements.txt Entry

```
# Email Node Dependencies
Jinja2>=3.1.6,<4.0.0      # Template engine with sandbox support
nh3>=0.3.5                # HTML sanitization (replaces deprecated bleach)
# Note: smtplib and email.mime are part of Python standard library
```

---

## Architecture Integration

### Existing Infrastructure Leverage

The Email Node will integrate with existing capabilities:

```
┌─────────────────────────────────────────────────────────────┐
│                    Flow Runner (Python)                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │  Email Node │───▶│   Jinja2    │───▶│  Template Engine │  │
│  │   Logic     │    │SandboxedEnv │    │  {{expressions}} │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │ DataSource  │───▶│  smtplib    │───▶│   SMTP Server   │  │
│  │  (SMTP)     │    │   client    │    │                 │  │
│  │  Credentials│    └─────────────┘    └─────────────────┘  │
│  └─────────────┘                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Input | Output |
|-----------|---------------|-------|--------|
| Email Node | Orchestrate sending, validate config | Node config, flow input | Email sent status |
| Jinja2 Sandbox | Render templates safely | Template string, data context | Rendered text/HTML |
| nh3 | Sanitize HTML content | Raw HTML | Sanitized HTML |
| DataSource | Retrieve SMTP credentials | Connection ID | SMTP config dict |
| smtplib | Send email via SMTP | Message, server config | Delivery status |

---

## Implementation Patterns

### Safe Template Rendering

```python
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import UndefinedError

class TemplateEngine:
    def __init__(self):
        # SandboxedEnvironment prevents code execution
        self.env = SandboxedEnvironment(
            autoescape=True,  # Auto-escape HTML
            undefined='strict'  # Raise error on undefined variables
        )
    
    def render(self, template_str: str, context: dict) -> str:
        try:
            template = self.env.from_string(template_str)
            return template.render(**context)
        except UndefinedError as e:
            # Handle missing variables gracefully
            raise TemplateRenderError(f"Template variable error: {e}")
```

### HTML Email Composition

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import nh3

def create_email_message(subject: str, body_html: str, body_text: str, 
                         from_addr: str, to_addrs: list) -> MIMEMultipart:
    # Sanitize HTML content
    safe_html = nh3.clean(
        body_html,
        tags={"p", "br", "strong", "em", "a", "ul", "ol", "li", 
              "table", "tr", "td", "th", "thead", "tbody", "h1", "h2", "h3"},
        attributes={
            "*": {"class"},
            "a": {"href"},
            "td": {"colspan", "rowspan"},
            "th": {"colspan", "rowspan"}
        },
        url_schemes={"https", "http", "mailto"}
    )
    
    # Create multipart message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)
    
    # Attach text and HTML parts
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(safe_html, 'html', 'utf-8'))
    
    return msg
```

### SMTP Integration with DataSource

```python
import smtplib
from typing import Dict

class EmailSender:
    def __init__(self, datasource_service):
        self.datasource = datasource_service
    
    def send(self, connection_id: str, message: MIMEMultipart) -> Dict:
        # Retrieve SMTP config from existing DataSource system
        smtp_config = self.datasource.get_connection(connection_id)
        
        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        
        try:
            # Enable TLS if port is 587
            if smtp_config['port'] == 587:
                server.starttls()
            
            # Authenticate
            server.login(smtp_config['username'], smtp_config['password'])
            
            # Send message
            server.send_message(message)
            
            return {'success': True, 'message_id': message['Message-ID']}
        finally:
            server.quit()
```

---

## Security Considerations

### Template Security

| Risk | Mitigation | Implementation |
|------|------------|----------------|
| Code execution in templates | Use SandboxedEnvironment | `from jinja2.sandbox import SandboxedEnvironment` |
| Access to private attributes | SandboxedEnvironment blocks `_` and `__` prefixed attrs | Built-in protection |
| Infinite loops in templates | Set reasonable max template size and render timeout | Monitor template execution time |
| Data exfiltration | Pass only necessary data to template context | Restrict context to flow input only |

### Email Security

| Risk | Mitigation | Implementation |
|------|------------|----------------|
| XSS in email HTML | Sanitize with nh3 | `nh3.clean(html, tags={...}, attributes={...})` |
| Header injection | Validate email addresses | Regex validation or email-validator library |
| Open redirect in links | Restrict URL schemes | `url_schemes={"https", "http", "mailto"}` |
| Information disclosure | Use Bcc for bulk emails | Support Bcc field in configuration |

### SMTP Security

| Risk | Mitigation | Implementation |
|------|------------|----------------|
| Credential exposure | Use existing encrypted DataSource storage | Leverage Connection Management milestone |
| Man-in-the-middle | Enforce TLS/STARTTLS | Port 587 + starttls() or port 465 with SSL |
| Server spoofing | Validate certificates | Ensure proper SSL context configuration |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Chosen |
|----------|-------------|-------------|----------------|
| SMTP Library | smtplib (stdlib) | fastapi-mail | Adds unnecessary abstraction; DataSource already handles connection management |
| SMTP Library | smtplib (stdlib) | aiosmtplib | Flow runner is synchronous; async adds complexity without benefit |
| Template Engine | Jinja2 | Chevron (Mustache) | Jinja2 more powerful for complex table generation; Chevron lacks conditionals/loops |
| HTML Sanitizer | nh3 | bleach | bleach officially deprecated (Jan 2023); nh3 is 20x faster and actively maintained |

---

## Integration Complexity Assessment

| Component | Complexity | Effort | Notes |
|-----------|------------|--------|-------|
| SMTP DataSource Integration | Low | 1-2 days | Existing Connection Management milestone provides foundation |
| Template Engine Integration | Low | 1 day | Jinja2 SandboxedEnvironment is drop-in replacement for standard Environment |
| HTML Sanitization | Low | 0.5 days | nh3 has simple API: `nh3.clean(html, tags={...})` |
| Email Node UI | Medium | 2-3 days | Property panel for subject, body, template variables; Monaco editor for templates |
| Testing | Medium | 2 days | Unit tests for template rendering, sanitization, SMTP integration |

**Total Estimated Effort: 1-2 weeks** (including testing and documentation)

---

## Sources

- **smtplib**: https://docs.python.org/3/library/smtplib.html (Official Python docs - HIGH confidence)
- **aiosmtplib**: https://aiosmtplib.readthedocs.io/en/stable/ (Official docs - HIGH confidence)
- **Jinja2**: https://jinja.palletsprojects.com/en/3.1.x/ (Official Pallets project docs - HIGH confidence)
- **Jinja2 Sandbox**: https://jinja.palletsprojects.com/en/3.1.x/sandbox/ (Official docs - HIGH confidence)
- **nh3**: https://nh3.readthedocs.io/en/latest/ (Official docs - HIGH confidence)
- **nh3 PyPI**: https://pypi.org/project/nh3/ (Version 0.3.5, April 2026 - HIGH confidence)
- **chevron**: https://pypi.org/project/chevron/ (Version 0.14.0 - MEDIUM confidence - last update 2021)
- **fastapi-mail**: https://pypi.org/project/fastapi-mail/ (Version 1.6.4, May 2026 - HIGH confidence)
- **email.mime**: https://docs.python.org/3/library/email.mime.html (Official Python docs - HIGH confidence)
- **bleach deprecation**: https://bleach.readthedocs.io/en/latest/ (Official notice - HIGH confidence)

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| SMTP Libraries | HIGH | Official Python stdlib documentation; mature and stable |
| Template Engine | HIGH | Jinja2 is industry standard; official Pallets documentation |
| HTML Sanitization | HIGH | nh3 is actively maintained; official docs and benchmarks |
| Integration Approach | HIGH | Builds on existing validated DataSource infrastructure |
| Security Model | HIGH | SandboxedEnvironment is well-documented and proven |

---

## Roadmap Implications

### Phase Ordering Recommendation

1. **Email Node Core** (Week 1)
   - SMTP DataSource integration using smtplib
   - Basic email sending (text only)
   - Integration with flow runner

2. **Template Engine** (Week 1-2)
   - Jinja2 SandboxedEnvironment integration
   - Subject and body templating with `{{expression}}` syntax
   - Context passing from node input

3. **HTML Support** (Week 2)
   - HTML email composition with email.mime
   - nh3 sanitization integration
   - Table generation from arrays using Jinja2 loops

4. **Testing & Polish** (Week 2)
   - Security testing (template injection, XSS)
   - SMTP integration testing with various providers (Gmail, Outlook, etc.)
   - UI/UX refinement

### Defer to Later Milestones

- **Async email sending** - Not needed with current APScheduler flow runner
- **Email attachments** - Can be added later; requires file storage integration
- **Email templates library** - Users can save templates in flow configurations
- **Email tracking** (open rates, click tracking) - Requires external service integration
