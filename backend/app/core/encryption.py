"""Encryption utilities for sensitive data like API tokens."""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from app.core.config import get_settings


def _get_fernet() -> Fernet:
    """Get Fernet instance with key derived from settings."""
    settings = get_settings()
    # Derive a 32-byte key from the configured encryption key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'dashboardstudio_fixed_salt',  # Fixed salt for consistent encryption
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.encryption_key.encode()))
    return Fernet(key)


def encrypt_value(value: str) -> str:
    """Encrypt a string value.
    
    Args:
        value: The string to encrypt
        
    Returns:
        Encrypted string (base64 encoded)
    """
    if not value:
        return value
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


from typing import Any

# Keys to automatically encrypt/decrypt in configuration dictionaries
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
                        result[key] = value # Fallback if decryption fails
            else:
                result[key] = process_sensitive_fields(value, action)
        return result
    
    return data
