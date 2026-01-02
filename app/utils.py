"""
Utility functions for RecipeHolder application.
Provides common helper functions used across modules.
"""
import re
import logging
from typing import Optional
from urllib.parse import urlparse
from slugify import slugify as python_slugify

logger = logging.getLogger(__name__)


def slugify(text: str, max_length: int = 200) -> str:
    """
    Convert text to a URL-safe slug.
    
    Args:
        text: Text to slugify
        max_length: Maximum length of slug
        
    Returns:
        URL-safe slug string
        
    Examples:
        >>> slugify("Chicken Curry (Pressure Cooker)")
        'chicken-curry-pressure-cooker'
        >>> slugify("Mom's Famous Apple Pie!")
        'moms-famous-apple-pie'
    """
    slug = python_slugify(text, max_length=max_length)
    return slug


def validate_url(url: str) -> bool:
    """
    Validate if string is a proper URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception as e:
        logger.warning(f"URL validation failed for '{url}': {e}")
        return False


def format_time(minutes: Optional[int]) -> str:
    """
    Format time in minutes to human-readable string.
    
    Args:
        minutes: Time in minutes
        
    Returns:
        Formatted time string (e.g., "1 hour 30 minutes")
        
    Examples:
        >>> format_time(30)
        '30 minutes'
        >>> format_time(90)
        '1 hour 30 minutes'
        >>> format_time(120)
        '2 hours'
    """
    if minutes is None or minutes <= 0:
        return ""
    
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    hour_str = f"{hours} hour{'s' if hours != 1 else ''}"
    
    if remaining_minutes == 0:
        return hour_str
    
    minute_str = f"{remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
    return f"{hour_str} {minute_str}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove any directory components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove any non-alphanumeric characters except dash, underscore, and dot
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Replace spaces with hyphens
    filename = filename.replace(' ', '-')
    
    # Remove multiple consecutive hyphens
    filename = re.sub(r'-+', '-', filename)
    
    # Remove leading/trailing hyphens and dots
    filename = filename.strip('-.')
    
    return filename


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain name from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name or None if invalid
        
    Examples:
        >>> extract_domain("https://www.example.com/recipe/123")
        'example.com'
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except Exception as e:
        logger.warning(f"Failed to extract domain from '{url}': {e}")
        return None


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length, adding suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)].rstrip() + suffix


def parse_time_string(time_str: str) -> Optional[int]:
    """
    Parse time string to minutes.
    Handles formats like: "1 hour 30 minutes", "45 minutes", "2 hours"
    
    Args:
        time_str: Time string to parse
        
    Returns:
        Total minutes or None if parsing fails
    """
    if not time_str:
        return None
    
    try:
        time_str = time_str.lower().strip()
        total_minutes = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)\s*(?:hour|hr|h)s?', time_str)
        if hour_match:
            total_minutes += int(hour_match.group(1)) * 60
        
        # Extract minutes
        minute_match = re.search(r'(\d+)\s*(?:minute|min|m)s?', time_str)
        if minute_match:
            total_minutes += int(minute_match.group(1))
        
        return total_minutes if total_minutes > 0 else None
    except Exception as e:
        logger.warning(f"Failed to parse time string '{time_str}': {e}")
        return None
