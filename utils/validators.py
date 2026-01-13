"""
Input Validators - Sanitize and validate user input
"""

import re
import html
from typing import Optional, List


def is_valid_username(username: str, min_length: int = 3, max_length: int = 32) -> bool:
    """Validate username format"""
    if not username or not isinstance(username, str):
        return False
    
    # Check length
    if not (min_length <= len(username) <= max_length):
        return False
    
    # Allow letters, numbers, underscore
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


def is_valid_referral_code(code: str) -> bool:
    """Validate referral code"""
    if not code or not isinstance(code, str):
        return False
    
    # Length check
    if not (3 <= len(code) <= 20):
        return False
    
    # Alphanumeric + underscore
    pattern = r'^[A-Za-z0-9_]+$'
    return bool(re.match(pattern, code))


def is_valid_chat_id(chat_id: str) -> bool:
    """Validate chat ID format"""
    if not chat_id or not isinstance(chat_id, str):
        return False
    
    # Should be numeric or string
    return chat_id.replace('-', '').isdigit() or len(chat_id) > 0


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_message(text: str, max_length: int = 4096) -> str:
    """Sanitize message text - remove dangerous content"""
    if not text:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Remove null bytes
    text = text.replace('\0', '')
    
    # Remove control characters (except newline, tab)
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()


def sanitize_username(username: str) -> str:
    """Sanitize username"""
    if not username:
        return "user"
    
    # Remove special chars
    username = re.sub(r'[^a-zA-Z0-9_]', '', username)
    
    # Limit length
    username = username[:32]
    
    # Must not be empty
    return username if username else "user"


def validate_message_format(text: str) -> bool:
    """Validate message format"""
    if not text or not isinstance(text, str):
        return False
    
    # Must not be only whitespace
    return bool(text.strip())


def is_safe_string(text: str) -> bool:
    """Check if string is safe (no SQL injection, XSS, etc.)"""
    if not text:
        return False
    
    # Check for SQL injection patterns
    dangerous_sql = [
        "' OR '1'='1",
        "'; DROP TABLE",
        "UNION SELECT",
        "exec(",
        "eval(",
        "system(",
    ]
    
    text_upper = text.upper()
    for pattern in dangerous_sql:
        if pattern in text_upper:
            return False
    
    return True


def validate_input_length(text: str, min_length: int = 1, max_length: int = 4096) -> bool:
    """Validate input length"""
    if not text:
        return min_length == 0
    
    return min_length <= len(text) <= max_length


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    if not url:
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    if not text:
        return ""
    
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def unescape_markdown(text: str) -> str:
    """Unescape markdown special characters"""
    if not text:
        return ""
    
    # Remove escape backslashes
    text = text.replace('\\', '')
    return text


def validate_command(command: str) -> bool:
    """Validate bot command format"""
    if not command:
        return False
    
    # Must start with /
    if not command.startswith('/'):
        return False
    
    # Must be alphanumeric after /
    return bool(re.match(r'^/[a-z0-9_]+$', command, re.IGNORECASE))


def get_command_name(text: str) -> Optional[str]:
    """Extract command name from message"""
    if not text:
        return None
    
    # Format: /command or /command@botname
    match = re.match(r'^/([a-z0-9_]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    
    return None


def validate_batch_input(items: List[str], max_items: int = 100) -> bool:
    """Validate batch input"""
    if not items or not isinstance(items, list):
        return False
    
    if len(items) > max_items:
        return False
    
    # All items must be strings
    return all(isinstance(item, str) for item in items)


def sanitize_batch(items: List[str]) -> List[str]:
    """Sanitize list of items"""
    if not items:
        return []
    
    return [sanitize_message(item) for item in items]
