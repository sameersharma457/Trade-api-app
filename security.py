import hashlib
import secrets
import string
from typing import Optional


def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_string(text: str, salt: Optional[str] = None) -> str:
    """Hash a string with optional salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{text}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return secrets.token_urlsafe(32)


def validate_input_safety(text: str) -> bool:
    """Basic input validation for safety"""
    dangerous_patterns = [
        '<script>', '</script>', 'javascript:', 'data:',
        'SELECT', 'DROP', 'DELETE', 'INSERT', 'UPDATE',
        '../', '../..', '\\x', '%2e%2e'
    ]
    
    text_lower = text.lower()
    return not any(pattern.lower() in text_lower for pattern in dangerous_patterns)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    
    safe_chars = string.ascii_letters + string.digits + '-_.'
    sanitized = ''.join(c for c in filename if c in safe_chars)
    
   
    return sanitized[:100] if sanitized else 'file'
