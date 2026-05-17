# Research Summary: Email Node with Dynamic Templates

**Project:** Dashboard Studio v1.7  
**Milestone:** Email Node with Dynamic Templates  
**Research Date:** 2026-05-17  
**Confidence:** HIGH

---

## Key Findings

### 1. Stack Requirements: Minimal Additions Needed

**Template Engine:** Jinja2 with `SandboxedEnvironment` (NOT Handlebars as initially suggested)
- Provides `{{expression}}` syntax as requested
- Sandboxed execution prevents code injection
- Rich ecosystem with loop/conditional support
- Version: `Jinja2>=3.1.6,<4.0.0`

**HTML Sanitization:** `nh3` (replaces deprecated `bleach`)
- 20x faster than bleach, actively maintained
- Rust-based for memory safety
- Version: `nh3>=0.3.5`

**SMTP:** Python standard library (`smtplib` + `email.mime`)
- No third-party libraries needed
- DataSource infrastructure already manages SMTP connections

**Integration Complexity: LOW** — leverages existing EXEC_ODS pattern

### 2. Template Engine Decision

**Chosen: Jinja2 SandboxedEnvironment**

Rationale:
- Already available in Python backend
- SandboxedEnvironment prevents security risks
- Supports loops (`{% for %}`) for table generation
- Conditionals (`{% if %}`) for dynamic content
- Auto-escaping by default (XSS prevention)

**Syntax Examples:**
```jinja2
{# Subject #}
Reporte de Ventas - {{ fecha }}

{# Body with variables #}
Hola {{ usuario.nombre }},

{# Table generation #}
<table>
  <tr><th>Producto</th><th>Cantidad</th></tr>
  {% for item in productos %}
  <tr>
    <td>{{ item.nombre }}</td>
    <td>{{ item.cantidad }}</td>
  </tr>
  {% endfor %}
</table>
```

### 3. Feature Complexity

**v1 (Current Milestone) — Table Stakes:**
1. Variable substitution: `{{ variable }}`
2. Nested object access: `{{ user.profile.name }}`
3. HTML escaping by default (security)
4. Iteration with `{% for %}` for tables/lists
5. Conditionals with `{% if %}` / `{% else %}`
6. Subject and body templating
7. Manual HTML table generation via loops

**v2 (Future Enhancement):**
1. Built-in table helper for simplified syntax
2. Date/number formatting filters
3. Template preview in UI
4. MJML integration for responsive emails

### 4. Architecture Pattern

**Signal-Based Integration (Following EXEC_ODS Pattern):**

```
Deno runner.ts (email node)
    → EXEC_EMAIL:{node_id}:{connection_id}
    → EXEC_EMAIL_PAYLOAD:{json}
    → DenoService intercepts
    → EmailExecutor.render_and_send()
    → SMTP via DataSource
    → Results streamed to UI
```

**Key Components:**
- `email_schemas.py` — Pydantic models for email configuration
- `email_executor.py` — Template rendering and SMTP sending
- `runner.ts` modifications — EXEC_EMAIL signal emission
- `deno_service.py` — Signal interception and delegation

**Template Compilation:**
- Compile templates once per node execution
- Cache compiled templates for reuse
- Render with input data context

### 5. Top Pitfalls & Mitigations

| Pitfall | Risk | Mitigation | Phase |
|---------|------|-----------|-------|
| **Template Injection (XSS)** | CRITICAL | Auto-escaping + SandboxedEnvironment | 1 |
| **Outlook Rendering** | HIGH | Table-based layouts + inline CSS | 2 |
| **SMTP Rate Limiting** | HIGH | Exponential backoff + queue | 3 |
| **UTF-8 Encoding** | MEDIUM | Explicit charset headers | 1 |
| **Large Template Data** | MEDIUM | Size limits (100 rows max) | 2 |
| **Missing Variables** | MEDIUM | Default values + strict mode option | 1 |

### 6. Security Requirements

**Template Security:**
- SandboxedEnvironment prevents arbitrary code execution
- Auto-escaping of all variables in HTML context
- Raw output only with explicit `| safe` filter (not recommended)
- Input validation for email addresses

**SMTP Security:**
- Credentials via encrypted DataSource (already implemented)
- No credentials in Deno payload
- TLS/SSL enforcement for SMTP connections

**HTML Email Security:**
- `nh3` sanitization of rendered HTML
- Removal of script tags, event handlers
- CSS whitelist for email-safe properties

---

## Files Generated

| File | Purpose |
|------|---------|
| `.planning/research/STACK.md` | Technology stack and dependencies |
| `.planning/research/FEATURES.md` | Feature landscape and template syntax |
| `.planning/research/ARCHITECTURE.md` | Integration architecture |
| `.planning/research/PITFALLS.md` | 11 identified pitfalls with prevention |

---

## Dependencies to Add

```toml
[project]
dependencies = [
    # ... existing ...
    "Jinja2>=3.1.6,<4.0.0",  # Template engine
    "nh3>=0.3.5",            # HTML sanitization
]
```

---

## Open Questions for Requirements Phase

1. Should we support plain text fallback for HTML emails?
2. Error handling: strict (fail on missing vars) vs lenient (empty string)?
3. Maximum email body size limit?
4. Attachment support in v1 or v2?
5. HTML editor in UI: rich text (Quill) or plain textarea?

---

**Next Step:** Define requirements based on this research → Create ROADMAP.md
