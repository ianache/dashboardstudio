# Domain Pitfalls: Email Node with Dynamic Templates

**Domain:** Email Templating & SMTP Delivery  
**Project:** Dashboard Studio - v1.7 Email Node  
**Researched:** 2026-05-16  
**Confidence:** HIGH (based on official OWASP, Python docs, Campaign Monitor, and Litmus sources)

---

## Critical Pitfalls

Mistakes that cause security vulnerabilities, delivery failures, or major rewrites.

### Pitfall 1: Template Injection & XSS Vulnerabilities

**What goes wrong:** Dynamic templates using `{{expression}}` syntax can be exploited if user input is not properly escaped. Attackers can inject malicious HTML/JavaScript that executes when recipients open emails.

**Why it happens:** 
- Using raw string interpolation without context-aware escaping
- Allowing HTML in template variables without sanitization
- Not validating template expressions before evaluation

**Consequences:**
- Cross-site scripting (XSS) in email clients that support JavaScript
- Phishing attacks via injected malicious links
- Data exfiltration from email content
- Reputation damage if emails contain malware

**Prevention:**
1. **Always escape HTML entities** in template variables: convert `&` to `&amp;`, `<` to `&lt;`, `>` to `&gt;`, `"` to `&quot;`, `'` to `&#x27;`
2. **Use context-aware encoding** - HTML body context needs different escaping than HTML attribute context
3. **Validate template expressions** - whitelist allowed characters and patterns in `{{}}` expressions
4. **Sanitize HTML if allowing rich content** - use libraries like bleach (Python) or DOMPurify (JS)
5. **Never allow user input directly in dangerous contexts:**
   - `<script>` tags
   - Event handlers (`onclick`, `onerror`)
   - `javascript:` or `data:` URLs
   - CSS `expression()` or imports

**Detection:**
- Security audits showing unescaped user data in templates
- Penetration testing reveals script injection in email previews
- Template variables containing `<`, `>`, or quotes render without encoding

**Recommended Phase:** Phase 1 - Core Template Engine (Must address before any user-facing features)

---

### Pitfall 2: HTML Email Rendering Inconsistencies

**What goes wrong:** Emails look great in one client but broken in another. Outlook desktop especially uses Word as rendering engine instead of a browser engine.

**Why it happens:**
- Different email clients support different CSS properties
- Outlook 2007-2019 uses Microsoft Word rendering engine (not WebKit)
- Gmail strips certain CSS properties and `<style>` blocks
- Mobile clients have different viewport handling

**Consequences:**
- Broken layouts in major clients (Outlook has 10%+ market share)
- Unreadable emails on mobile devices
- Images displaying at wrong sizes
- Padding/margins ignored

**Prevention:**
1. **Use table-based layouts** - `<table>` tags are most reliable across clients; avoid `<div>`-based layouts for Outlook
2. **Inline CSS only** - many clients strip `<style>` tags; use inline `style=""` attributes
3. **Include width/height attributes on images** - Outlook ignores CSS dimensions; use HTML attributes
4. **Use conditional comments for Outlook-specific fixes:**
   ```html
   <!--[if mso]>
     <table role="presentation" cellspacing="0" cellpadding="0" border="0">
   <![endif]-->
   ```
5. **Test across clients** using tools like Litmus or Email on Acid
6. **Avoid unsupported features:**
   - Flexbox/Grid layouts (poor Outlook support)
   - CSS animations (limited support)
   - Custom fonts (use web-safe fonts as fallbacks)
   - Background images in Outlook without VML fallbacks

**Detection:**
- Emails render differently in test vs production
- Layout breaks when forwarded
- Images appear at actual size instead of specified dimensions
- Spacing inconsistency between clients

**Recommended Phase:** Phase 2 - Template Rendering System

---

### Pitfall 3: SMTP Rate Limiting & Delivery Failures

**What goes wrong:** Sending too many emails too quickly triggers rate limits from SMTP providers, causing rejected emails and potential blacklisting.

**Why it happens:**
- No throttling mechanism for bulk sends
- Connection pooling not implemented
- Retry logic absent or poorly implemented
- Not handling SMTP error codes properly

**Consequences:**
- Emails silently dropped
- SMTP account temporarily suspended
- IP/domain reputation damage
- Emails marked as spam
- Permanent blacklisting

**Prevention:**
1. **Implement rate limiting** - respect provider limits (common: 100-500 emails/hour for shared IPs)
2. **Use connection pooling** - reuse SMTP connections instead of opening/closing per email
3. **Implement exponential backoff** for retries:
   - 1st retry: 5 minutes
   - 2nd retry: 15 minutes
   - 3rd retry: 1 hour
4. **Handle SMTP error codes:**
   - `421` / `450` / `451` - Temporary failure, retry later
   - `550` / `551` - Permanent failure, don't retry
   - `452` - Mailbox full
   - `4xx` codes generally retryable, `5xx` generally not
5. **Monitor reputation metrics:**
   - Bounce rates (keep < 5%)
   - Complaint rates (keep < 0.1%)
6. **Use queue-based architecture** - decouple email generation from sending

**Detection:**
- SMTP error logs showing `421 Service not available`
- Increasing bounce rates
- Emails not arriving despite successful API responses
- SMTP provider warnings about rate limits

**Recommended Phase:** Phase 3 - SMTP Delivery Engine

---

### Pitfall 4: Character Encoding Issues

**What goes wrong:** Special characters (accents, emoji, non-Latin scripts) display incorrectly or cause encoding errors.

**Why it happens:**
- Not specifying charset in email headers
- Mixing encodings between template and data
- Python 2/3 string handling confusion
- Email clients defaulting to wrong encoding

**Consequences:**
- Garbled text for international users
- "Mojibake" ( garbled characters like "Ã©" instead of "é")
- Email clients showing ??? for special characters
- Template rendering failures

**Prevention:**
1. **Always use UTF-8 encoding:**
   - Set `Content-Type: text/html; charset=utf-8`
   - Use `email.policy.EmailPolicy(utf8=True)` in Python
2. **Use Python's email library correctly:**
   ```python
   from email.message import EmailMessage
   from email.policy import EmailPolicy
   
   msg = EmailMessage(policy=EmailPolicy(utf8=True))
   msg.set_content(body, subtype='html')
   ```
3. **Encode headers properly** using RFC 2047 for non-ASCII in headers
4. **Normalize input** - convert all template data to Unicode before processing
5. **Test with international content** - include é, ñ, 中文, emojis in test cases

**Detection:**
- Special characters appear as question marks or boxes
- Email headers missing charset specification
- `UnicodeEncodeError` or `UnicodeDecodeError` in logs
- Different rendering between web preview and actual email

**Recommended Phase:** Phase 1 - Core Template Engine

---

### Pitfall 5: Memory Issues with Large Template Data

**What goes wrong:** Processing large datasets in templates (e.g., rendering tables with thousands of rows) causes memory exhaustion.

**Why it happens:**
- Loading entire datasets into memory for template rendering
- Recursive template processing without depth limits
- Creating massive HTML strings without streaming
- No limits on template output size

**Consequences:**
- Server crashes from OOM (Out of Memory)
- Slow performance affecting other requests
- Denial of service vulnerability
- Timeouts causing email delivery failures

**Prevention:**
1. **Implement output size limits** - reject templates generating > 1MB HTML
2. **Limit iteration depth** - cap loops in templates (max 1000 iterations)
3. **Use streaming for large data** - process rows in chunks
4. **Implement pagination helpers** in template engine
5. **Add resource limits:**
   - Maximum template execution time (30 seconds)
   - Maximum memory per template render (50MB)
   - Maximum number of variables in scope (1000)
6. **Sample data for preview** - show first 100 rows with "...and 900 more" message

**Detection:**
- Memory usage spikes during email generation
- Template processing timeouts
- OOM errors in logs
- Slow response times on template-heavy flows

**Recommended Phase:** Phase 2 - Template Rendering System

---

### Pitfall 6: Email Address Validation Pitfalls

**What goes wrong:** Invalid or malformed email addresses cause delivery failures or security issues.

**Why it happens:**
- Overly strict regex rejecting valid addresses
- Not normalizing email addresses consistently
- Case sensitivity issues in local part
- Not validating domain exists (MX records)

**Consequences:**
- Legitimate users can't receive emails
- Bounces from invalid addresses hurt sender reputation
- Account enumeration vulnerabilities
- Confusion from visually similar addresses (homoglyph attacks)

**Prevention:**
1. **Use well-tested libraries** instead of custom regex:
   - Python: `email-validator` library
   - Avoid overly strict validation
2. **Normalize consistently:**
   - Domain part: always lowercase
   - Local part: preserve case (technically case-sensitive per RFC)
3. **Check for common issues:**
   - Multiple @ symbols
   - Spaces in address
   - Invalid characters
4. **Consider MX record validation** (optional, with timeouts)
5. **Be aware of homoglyph attacks** - Cyrillic а vs Latin a
6. **Always verify ownership** via confirmation email before trusting address

**Detection:**
- High bounce rates from validation bypass
- Support tickets about "valid email rejected"
- Users with duplicate accounts due to case differences

**Recommended Phase:** Phase 1 - Core Template Engine (input validation)

---

### Pitfall 7: SPF/DKIM/DMARC Authentication Failures

**What goes wrong:** Emails fail authentication checks and go to spam folders.

**Why it happens:**
- SPF record doesn't include SMTP server IP
- DKIM signatures not configured
- DMARC policy not set
- "From" domain doesn't match authenticated domain

**Consequences:**
- Emails consistently land in spam/junk
- Brand reputation damage
- Failed authentication visible to recipients
- Potential domain blacklisting

**Prevention:**
1. **Configure SPF record:**
   ```
   v=spf1 include:_spf.google.com include:sendgrid.net ~all
   ```
2. **Enable DKIM signing** through your SMTP provider
3. **Set up DMARC policy:**
   ```
   _dmarc.example.com TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
   ```
4. **Ensure "From" domain aligns** with authenticated domain
5. **Monitor authentication results** via DMARC reports
6. **Use consistent "From" addresses** - don't spoof different domains

**Detection:**
- Emails consistently in spam folders
- Authentication failure headers in received emails
- DMARC reports showing failures
- Spam filter testing tools flagging authentication

**Recommended Phase:** Phase 3 - SMTP Delivery Engine (documentation/requirement)

---

### Pitfall 8: Template Syntax Errors & Evaluation Failures

**What goes wrong:** Malformed `{{expression}}` syntax or undefined variables cause template rendering to fail.

**Why it happens:**
- No validation of template syntax before saving
- Missing variables in template context
- Nested expressions causing infinite recursion
- Special characters breaking expression parsing

**Consequences:**
- Emails not sent due to render errors
- Raw template syntax shown to users
- Missing content in critical emails
- Unpredictable behavior from partial renders

**Prevention:**
1. **Validate templates on save** - parse and check syntax before storing
2. **Implement graceful degradation:**
   - Undefined variables render as empty string, not error
   - Invalid expressions show warning, not crash
3. **Use try/except around template evaluation**
4. **Provide preview functionality** with sample data
5. **Limit expression complexity:**
   - No nested `{{}}` expressions
   - Restricted operator set
   - No function calls in expressions (unless explicitly allowed)
6. **Escape special characters** in template delimiters

**Detection:**
- TemplateSyntaxError exceptions in logs
- User complaints about "{{variable}} showing in emails"
- Missing content in generated emails
- Preview showing errors

**Recommended Phase:** Phase 1 - Core Template Engine

---

## Moderate Pitfalls

### Pitfall 9: Image Display Issues

**What goes wrong:** Images don't display or show broken image icons.

**Prevention:**
- Always include `width` and `height` HTML attributes (not just CSS)
- Provide `alt` text for accessibility and image blocking
- Use absolute URLs (not relative) for hosted images
- Consider image size limits (large images trigger spam filters)
- Test with images disabled

**Recommended Phase:** Phase 2 - Template Rendering System

---

### Pitfall 10: Reply-To and Bounce Handling

**What goes wrong:** Replies go to wrong address or bounces aren't handled.

**Prevention:**
- Set proper `Reply-To` header for user responses
- Use `Return-Path` for bounce handling
- Implement VERP (Variable Envelope Return Path) for tracking bounces
- Monitor bounce rates and suppress invalid addresses

**Recommended Phase:** Phase 3 - SMTP Delivery Engine

---

### Pitfall 11: Email Size Limits

**What goes wrong:** Large emails (big images, attachments) rejected by servers.

**Prevention:**
- Keep HTML body under 100KB
- Optimize/compress images before embedding
- Warn users about attachment size limits (typically 10-25MB)
- Use links to hosted content instead of attachments when possible

**Recommended Phase:** Phase 2 - Template Rendering System

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Phase 1: Template Engine** | XSS via unescaped variables | Implement auto-escaping by default; require explicit `safe` filter for HTML |
| **Phase 1: Template Engine** | Character encoding issues | Force UTF-8 throughout; test with international characters |
| **Phase 1: Template Engine** | Template syntax errors | Validate on save; graceful handling of undefined vars |
| **Phase 2: Template Rendering** | Large data memory issues | Implement size limits; pagination helpers; streaming |
| **Phase 2: Template Rendering** | HTML rendering inconsistencies | Use table layouts; inline CSS; test across clients |
| **Phase 3: SMTP Delivery** | Rate limiting/blacklisting | Implement throttling; exponential backoff; queue-based sending |
| **Phase 3: SMTP Delivery** | Authentication failures | Document SPF/DKIM requirements; validate From alignment |
| **Phase 3: SMTP Delivery** | Delivery errors not handled | Implement proper error handling for SMTP codes; retry logic |

---

## Sources

- [OWASP Cross-Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) - **HIGH confidence**
- [OWASP Email Validation and Verification Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Email_Validation_and_Verification_Cheat_Sheet.html) - **HIGH confidence**
- [Python email module documentation](https://docs.python.org/3/library/email.html) - **HIGH confidence**
- [Python smtplib documentation](https://docs.python.org/3/library/smtplib.html) - **HIGH confidence**
- [Campaign Monitor CSS Support Guide](https://www.campaignmonitor.com/css/) - **HIGH confidence**
- [Litmus Outlook Email Rendering Guide](https://www.litmus.com/blog/a-guide-to-rendering-differences-in-microsoft-outlook-clients) - **HIGH confidence**
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html) - **HIGH confidence** (for URL validation patterns)
