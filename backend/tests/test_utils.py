"""Tests for utility functions"""
import pytest
from datetime import datetime
from backend.utils.helpers import (
    format_datetime,
    parse_datetime,
    validate_email,
    sanitize_filename,
    truncate_string,
)


class TestDateTimeHelpers:
    """Test datetime utility functions"""

    def test_format_datetime(self):
        """Test datetime formatting"""
        dt = datetime(2025, 1, 1, 12, 30, 45)
        formatted = format_datetime(dt)
        assert "2025" in formatted
        assert "12:30:45" in formatted

    def test_parse_datetime_iso(self):
        """Test parsing ISO format datetime"""
        dt_string = "2025-01-01T12:30:45+00:00"
        result = parse_datetime(dt_string)
        assert result is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1

    def test_parse_datetime_invalid(self):
        """Test parsing invalid datetime returns None"""
        result = parse_datetime("invalid-date")
        assert result is None


class TestEmailValidation:
    """Test email validation"""

    def test_validate_email_valid(self):
        """Test valid email addresses"""
        assert validate_email("user@example.com")
        assert validate_email("test.user@domain.co.uk")

    def test_validate_email_invalid(self):
        """Test invalid email addresses"""
        assert not validate_email("invalid")
        assert not validate_email("@example.com")
        assert not validate_email("user@")


class TestFilenameHelpers:
    """Test filename utility functions"""

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        result = sanitize_filename("test<file>name.txt")
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_filename_long(self):
        """Test long filename truncation"""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_truncate_string(self):
        """Test string truncation"""
        text = "This is a very long string"
        result = truncate_string(text, max_length=10)
        assert len(result) <= 13  # 10 + "..." length
        assert "..." in result
