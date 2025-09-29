# server/utils/helpers.py
"""
General utility functions for the server
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string
    
    Args:
        dt: Datetime object
        format_string: Format string
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_string)


def parse_datetime(dt_string: str) -> Optional[datetime]:
    """Parse datetime from string
    
    Args:
        dt_string: Datetime string (ISO format)
        
    Returns:
        Datetime object or None if parsing fails
    """
    try:
        # Try ISO format first
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except:
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except:
                continue
        
        return None


def validate_email(email: str) -> bool:
    """Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system use
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or 'unnamed'


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks
    
    Args:
        items: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def get_date_range(view_type: str, reference_date: datetime = None) -> tuple:
    """Get start and end dates for a view type
    
    Args:
        view_type: 'day', 'week', or 'month'
        reference_date: Reference date (default: today)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    if reference_date is None:
        reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if view_type == 'day':
        start_date = reference_date
        end_date = start_date + timedelta(days=1)
    elif view_type == 'week':
        # Start on Monday
        start_date = reference_date - timedelta(days=reference_date.weekday())
        end_date = start_date + timedelta(days=7)
    elif view_type == 'month':
        # Start on first day of month
        start_date = reference_date.replace(day=1)
        # End on last day of month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
    else:
        # Default to week
        start_date = reference_date
        end_date = start_date + timedelta(days=7)
    
    return start_date, end_date


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} PB"


def calculate_duration(start: datetime, end: datetime) -> str:
    """Calculate human-readable duration between two datetimes
    
    Args:
        start: Start datetime
        end: End datetime
        
    Returns:
        Duration string (e.g., "2 hours 30 minutes")
    """
    delta = end - start
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    return " ".join(parts)
