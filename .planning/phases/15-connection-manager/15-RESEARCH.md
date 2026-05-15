# Phase 15: Centralized Connection Manager - Research

**Researched:** 2026-05-14
**Domain:** Data Integration / Infrastructure
**Confidence:** HIGH

## Summary

This phase focuses on consolidating how external connections (Email, Databases, APIs, etc.) are managed in dashboardstudio. Currently, `DataSource` uses flat columns which are insufficient for complex configurations (like JWT acquisition or specialized SMTP settings). We are moving to a unified `connection_config` JSON column that stores protocol-specific settings while maintaining a standard structure for extensibility.

**Primary recommendation:** Use Pydantic's discriminated unions for schema validation and implement a recursive encryption helper to protect sensitive fields within the JSON structure.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.x | Schema validation | Industry standard for FastAPI applications, supports Discriminated Unions. |
| SQLAlchemy | 2.x | ORM / Migration | Used in current backend, supports JSON columns natively. |
| Cryptography | Latest | Encryption | Already integrated in `app.core.encryption`, reliable for sensitive data. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| sqlalchemy-utils | Optional | Extra types | Can provide enhanced JSON support if needed, though standard JSON is usually enough. |

## Architecture Patterns

### Recommended JSON Structure (Discriminator Pattern)
The `connection_config` should follow a polymorphic structure where fields vary by `type`.

```typescript
{
  "host": string,
  "port": number,
  "auth": {
    "username"?: string,
    "password"?: string, // Encrypted
    "token"?: string     // Encrypted
  },
  "options": Record<string, any>, // Extensibility point
  "extra_params": Record<string, any> // Future-proofing
}
```

### Pattern 1: Discriminated Unions for Pydantic
Define a base model and specific models for each connection type. This allows the API to validate the JSON body based on the `type` field.

```python
# Source: Pydantic Documentation
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field

class SmtpConfig(BaseModel):
    type: Literal['smtp']
    host: str
    port: int
    use_ssl: bool
    email: str
    password: str  # To be encrypted

class HttpConfig(BaseModel):
    type: Literal['http']
    url: str
    username: Optional[str]
    password: Optional[str] # To be encrypted

ConnectionConfig = Annotated[Union[SmtpConfig, HttpConfig], Field(discriminator='type')]
```

### Anti-Patterns to Avoid
- **Hardcoding Fields in Model:** Don't add `smtp_host`, `db_port` to the `DataSource` table. Keep them in the JSON blob.
- **PlainText Secrets in JSON:** Never store the JSON blob without encrypting sensitive keys.
- **Manual Encryption in Every Endpoint:** Avoid repeating encryption logic; use a centralized utility that knows which keys are sensitive.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Connection String Parsing | Custom regex | `sqlalchemy.engine.url.make_url` | Handles all edge cases (escaped chars, optional ports) for DB URLs. |
| JSON Schema Validation | Manual dict checks | Pydantic Models | Provides automatic error messages and type coercion. |
| Secret Management | Custom obfuscation | `cryptography.fernet` | Already implemented and secure in the project. |

## Common Pitfalls

### Pitfall 1: Migration of Existing Data
**What goes wrong:** Existing `DataSource` records have `connection_url`. If we switch to JSON without migrating, existing flows break.
**How to avoid:** Use a migration script that parses `connection_url` into the new JSON structure.

### Pitfall 2: Schema Versioning
**What goes wrong:** Adding a required field to a connection type breaks existing saved configurations.
**How to avoid:** Make new fields optional or provide default values in the Pydantic schemas.

## Code Examples

### Unified Encryption Utility
This should be added to `backend/app/core/encryption.py`:

```python
# Verified pattern for recursive JSON encryption
SENSITIVE_KEYS = {"password", "api_key", "client_secret", "token", "api_token"}

def process_sensitive_fields(data: Any, action: str = "encrypt") -> Any:
    """Recursively encrypt/decrypt sensitive fields in a JSON-compatible structure."""
    if isinstance(data, list):
        return [process_sensitive_fields(item, action) for item in data]
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in SENSITIVE_KEYS and isinstance(value, str) and value:
                if action == "encrypt":
                    result[key] = encrypt_value(value)
                else:
                    try:
                        result[key] = decrypt_value(value)
                    except Exception:
                        result[key] = value # Or handle error
            else:
                result[key] = process_sensitive_fields(value, action)
        return result
    
    return data
```

## Proposed Connection Schemas

### 1. Email (SMTP)
```json
{
  "host": "smtp.gmail.com",
  "port": 587,
  "use_ssl": true,
  "email": "user@example.com",
  "password": "...",
  "options": {
    "use_tls": true,
    "timeout": 30
  }
}
```

### 2. Database (Generic)
```json
{
  "host": "localhost",
  "port": 5432,
  "username": "admin",
  "password": "...",
  "database": "analytics",
  "schema": "public",
  "options": {
    "ssl_mode": "prefer",
    "pool_size": 10
  }
}
```

### 3. FTP / SFTP
```json
{
  "host": "files.example.com",
  "port": 22,
  "username": "user",
  "password": "...",
  "protocol": "sftp",
  "schema": null,
  "options": {
    "passive_mode": true
  }
}
```

### 4. HTTP (Basic)
```json
{
  "url": "https://api.example.com/v1",
  "username": "api_user",
  "password": "...",
  "options": {
    "headers": {
      "Accept": "application/json",
      "User-Agent": "DashboardStudio/1.0"
    }
  }
}
```

### 5. JWT (Token Acquisition)
```json
{
  "token_url": "https://auth.example.com/token",
  "username": "service_user",
  "password": "...",
  "client_id": "client_abc",
  "client_secret": "...",
  "grant_type": "password",
  "options": {
    "scopes": ["read", "write"]
  }
}
```

## Open Questions

1. **Should we keep flat columns?**
   - Recommendation: Keep them as `nullable=True` for backward compatibility during Phase 15, then deprecate and remove in a future phase.
2. **How to handle connection testing?**
   - Recommendation: Implement a "Strategy Pattern" where each connection type has a `test_connection(config)` method.

## Sources

### Primary (HIGH confidence)
- `backend/app/core/encryption.py` - Current encryption implementation.
- `backend/app/models/models.py` - Existing `DataSource` structure.
- [Pydantic Docs](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions) - Standard for polymorphic JSON.

### Secondary (MEDIUM confidence)
- [Airflow Connection Docs](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection/index.html) - Industry practice for centralized connections.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH
- Architecture: HIGH
- Pitfalls: MEDIUM

**Research date:** 2026-05-14
**Valid until:** 2026-06-14
