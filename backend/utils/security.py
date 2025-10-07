"""
Security utilities for the application

This module provides security-related utilities including CSRF protection,
input sanitization, and security headers.
"""

from __future__ import annotations

import re
import html
import secrets
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, session, abort, make_response, Response
import bleach


# CSRF Protection
class CSRFProtection:
    """
    CSRF (Cross-Site Request Forgery) protection

    Generates and validates CSRF tokens for state-changing requests.
    """

    TOKEN_LENGTH = 32
    SESSION_KEY = '_csrf_token'
    HEADER_NAME = 'X-CSRF-Token'
    FORM_FIELD = 'csrf_token'

    @staticmethod
    def generate_token() -> str:
        """
        Generate a new CSRF token

        Returns:
            Random token string
        """
        return secrets.token_hex(CSRFProtection.TOKEN_LENGTH)

    @staticmethod
    def get_token() -> str:
        """
        Get current CSRF token or generate new one

        Returns:
            CSRF token from session or new token
        """
        if CSRFProtection.SESSION_KEY not in session:
            session[CSRFProtection.SESSION_KEY] = CSRFProtection.generate_token()
        return session[CSRFProtection.SESSION_KEY]

    @staticmethod
    def validate_token(token: Optional[str] = None) -> bool:
        """
        Validate CSRF token

        Args:
            token: Token to validate (or get from request)

        Returns:
            True if token is valid
        """
        if token is None:
            # Try to get token from header or form
            token = request.headers.get(CSRFProtection.HEADER_NAME)
            if token is None:
                token = request.form.get(CSRFProtection.FORM_FIELD)

        if not token:
            return False

        session_token = session.get(CSRFProtection.SESSION_KEY)
        if not session_token:
            return False

        return secrets.compare_digest(token, session_token)


def csrf_protect(f):
    """
    Decorator to protect routes with CSRF validation

    Usage:
        @app.route('/api/data', methods=['POST'])
        @csrf_protect
        def create_data():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF for GET, HEAD, OPTIONS requests
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return f(*args, **kwargs)

        # Validate token
        if not CSRFProtection.validate_token():
            abort(403, description='CSRF token validation failed')

        return f(*args, **kwargs)
    return decorated_function


# Input Sanitization
class InputSanitizer:
    """
    Input sanitization utilities

    Provides methods to clean and validate user input.
    """

    # Allowed HTML tags for rich text (if needed)
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

    @staticmethod
    def sanitize_html(text: str, strip: bool = False) -> str:
        """
        Sanitize HTML input

        Args:
            text: HTML text to sanitize
            strip: If True, strip all HTML tags

        Returns:
            Sanitized HTML
        """
        if strip:
            return bleach.clean(text, tags=[], strip=True)

        return bleach.clean(
            text,
            tags=InputSanitizer.ALLOWED_TAGS,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True
        )

    @staticmethod
    def escape_html(text: str) -> str:
        """
        Escape HTML special characters

        Args:
            text: Text to escape

        Returns:
            HTML-escaped text
        """
        return html.escape(text)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe filesystem use

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')

        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '_', filename)

        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')

        return filename or 'unnamed'

    @staticmethod
    def sanitize_sql_like(text: str) -> str:
        """
        Sanitize text for SQL LIKE queries

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with escaped wildcards
        """
        # Escape SQL LIKE wildcards
        text = text.replace('%', r'\%')
        text = text.replace('_', r'\_')
        return text

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format

        Args:
            email: Email address to validate

        Returns:
            True if email is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_json_keys(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize dictionary keys to prevent injection

        Args:
            data: Dictionary to sanitize

        Returns:
            Dictionary with sanitized keys
        """
        sanitized = {}
        for key, value in data.items():
            # Only allow alphanumeric and underscore in keys
            safe_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))

            # Recursively sanitize nested dicts
            if isinstance(value, dict):
                sanitized[safe_key] = InputSanitizer.sanitize_json_keys(value)
            elif isinstance(value, list):
                sanitized[safe_key] = [
                    InputSanitizer.sanitize_json_keys(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[safe_key] = value

        return sanitized


# Security Headers
class SecurityHeaders:
    """
    Security headers for HTTP responses

    Implements common security headers to protect against various attacks.
    """

    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        """
        Get default security headers

        Returns:
            Dictionary of security headers
        """
        return {
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',

            # Enable XSS protection
            'X-XSS-Protection': '1; mode=block',

            # Prevent clickjacking
            'X-Frame-Options': 'SAMEORIGIN',

            # Enforce HTTPS (if using HTTPS)
            # 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',

            # Content Security Policy (customize as needed)
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self';"
            ),

            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',

            # Permissions policy
            'Permissions-Policy': (
                'geolocation=(), '
                'microphone=(), '
                'camera=()'
            ),
        }

    @staticmethod
    def apply_headers(response: Response) -> Response:
        """
        Apply security headers to response

        Args:
            response: Flask response object

        Returns:
            Response with security headers applied
        """
        headers = SecurityHeaders.get_default_headers()
        for header, value in headers.items():
            response.headers[header] = value
        return response


def apply_security_headers(f):
    """
    Decorator to apply security headers to response

    Usage:
        @app.route('/api/data')
        @apply_security_headers
        def get_data():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        return SecurityHeaders.apply_headers(response)
    return decorated_function


# Rate limiting helpers
class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


def check_rate_limit(
    key: str,
    max_requests: int,
    window_seconds: int,
    storage: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Check if rate limit has been exceeded

    Args:
        key: Unique key for rate limiting (e.g., IP address, user ID)
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds
        storage: Optional storage dict (defaults to session)

    Returns:
        True if request is allowed, False if rate limit exceeded
    """
    import time

    if storage is None:
        storage = session

    rate_key = f'rate_limit_{key}'
    now = time.time()

    # Get existing rate limit data
    rate_data = storage.get(rate_key, {'requests': [], 'window_start': now})

    # Remove old requests outside the window
    rate_data['requests'] = [
        req_time for req_time in rate_data['requests']
        if now - req_time < window_seconds
    ]

    # Check if limit exceeded
    if len(rate_data['requests']) >= max_requests:
        return False

    # Add current request
    rate_data['requests'].append(now)
    storage[rate_key] = rate_data

    return True


# Password utilities
class PasswordValidator:
    """
    Password validation utilities
    """

    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True

    @staticmethod
    def validate_password(password: str) -> tuple[bool, list[str]]:
        """
        Validate password strength

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(f'Password must be at least {PasswordValidator.MIN_LENGTH} characters')

        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')

        if PasswordValidator.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')

        if PasswordValidator.REQUIRE_DIGIT and not re.search(r'\d', password):
            errors.append('Password must contain at least one digit')

        if PasswordValidator.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')

        return len(errors) == 0, errors
