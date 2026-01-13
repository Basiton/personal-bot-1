"""
Referral Link Generator
"""

import hashlib
import secrets
import string
from typing import Optional, Tuple
from urllib.parse import quote, unquote


def generate_short_code(length: int = 8) -> str:
    """Generate short referral code"""
    chars = string.ascii_letters + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(length))
    return code.upper()


def generate_referral_link(user_id: str, bot_name: str, code: str = None) -> str:
    """Generate referral link for sharing"""
    if not code:
        code = generate_short_code()
    
    # Format: t.me/botname?start=CODE
    return f"https://t.me/{bot_name}?start={code}"


def generate_payload(user_id: str, ref_code: str) -> str:
    """Generate payload for deep linking"""
    payload = f"ref_{ref_code}_{user_id}"
    return payload


def extract_referral_code(payload: str) -> Optional[str]:
    """Extract referral code from payload"""
    if not payload:
        return None
    
    # Try to extract from format: ref_CODE_userid
    parts = payload.split('_')
    if len(parts) >= 2 and parts[0] == 'ref':
        return parts[1]
    
    return None


def is_valid_referral_format(ref_code: str) -> bool:
    """Check if referral code has valid format"""
    if not ref_code:
        return False
    
    # Allow alphanumeric and underscore
    allowed = set(string.ascii_letters + string.digits + '_')
    return all(c in allowed for c in ref_code) and 3 <= len(ref_code) <= 20


def hash_user_id(user_id: str) -> str:
    """Hash user ID for tracking"""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def generate_tracking_link(
    bot_name: str, 
    user_id: str, 
    campaign: str = "organic"
) -> str:
    """Generate tracking link with campaign parameter"""
    code = generate_short_code()
    # Format: t.me/botname?start=CODE_campaign
    return f"https://t.me/{bot_name}?start={code}_{campaign}"


def parse_start_parameter(start_param: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse start parameter to extract referral code and metadata"""
    if not start_param:
        return None, None
    
    # Format: CODE or CODE_metadata
    parts = start_param.split('_')
    code = parts[0] if parts else None
    metadata = parts[1] if len(parts) > 1 else None
    
    return code, metadata


def generate_custom_link(
    bot_name: str, 
    ref_code: str, 
    custom_text: str = None
) -> str:
    """Generate custom referral link with text"""
    link = f"https://t.me/{bot_name}?start={ref_code}"
    if custom_text:
        link = f"{link} ({custom_text})"
    return link


def validate_referral_code(code: str) -> bool:
    """Validate referral code"""
    if not code:
        return False
    
    # Must be alphanumeric and between 3-20 chars
    if not (3 <= len(code) <= 20):
        return False
    
    # Check if alphanumeric
    return code.replace('_', '').isalnum()


def encode_payload(data: dict) -> str:
    """Encode dictionary as URL-safe payload"""
    import json
    json_str = json.dumps(data)
    return quote(json_str)


def decode_payload(payload: str) -> dict:
    """Decode URL-safe payload to dictionary"""
    import json
    try:
        json_str = unquote(payload)
        return json.loads(json_str)
    except:
        return {}
