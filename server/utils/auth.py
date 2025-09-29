# server/utils/auth.py
"""
Authentication and authorization utilities
"""

from typing import Optional, Dict, Any
import hashlib
import secrets
from datetime import datetime, timedelta


def generate_session_token() -> str:
    """Generate a secure random session token
    
    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(32)


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """Hash a password with salt
    
    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use SHA256 with salt
    hash_obj = hashlib.sha256()
    hash_obj.update(salt.encode())
    hash_obj.update(password.encode())
    
    return hash_obj.hexdigest(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash
    
    Args:
        password: Plain text password to verify
        hashed: Hashed password to check against
        salt: Salt used in hashing
        
    Returns:
        True if password matches
    """
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed


def generate_api_key() -> str:
    """Generate an API key for client authentication
    
    Returns:
        API key string
    """
    return f"pk_{secrets.token_urlsafe(32)}"


def validate_api_key(api_key: str) -> bool:
    """Validate API key format
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if format is valid
    """
    return api_key.startswith('pk_') and len(api_key) > 35
