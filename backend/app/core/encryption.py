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


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted string value.
    
    Args:
        encrypted_value: The encrypted string (base64 encoded)
        
    Returns:
        Decrypted string
        
    Raises:
        ValueError: If decryption fails
    """
    if not encrypted_value:
        return encrypted_value
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt value: {str(e)}")
