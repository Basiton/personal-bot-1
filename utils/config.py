"""
Configuration Manager - Load from .env file
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    """Configuration class"""
    
    # Core
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    BOT_NAME = os.getenv('BOT_NAME', '')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/bot.db')
    
    # Admin
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    ADMIN_PORT = int(os.getenv('ADMIN_PORT', 8000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Features
    REQUIRED_CHANNEL = os.getenv('REQUIRED_CHANNEL', '')
    ENABLE_REFERRAL = os.getenv('ENABLE_REFERRAL', 'true').lower() == 'true'
    ENABLE_BROADCAST = os.getenv('ENABLE_BROADCAST', 'true').lower() == 'true'
    
    # Validation
    MIN_USERNAME_LENGTH = int(os.getenv('MIN_USERNAME_LENGTH', 3))
    MAX_USERNAME_LENGTH = int(os.getenv('MAX_USERNAME_LENGTH', 32))
    
    # API
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', 4096))
    
    # Rates
    POINTS_PER_REFERRAL = int(os.getenv('POINTS_PER_REFERRAL', 10))
    POINTS_PER_MESSAGE = int(os.getenv('POINTS_PER_MESSAGE', 1))
    
    def __init__(self):
        """Validate configuration"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN not set in .env")
        if not self.BOT_NAME:
            raise ValueError("BOT_NAME not set in .env")
    
    def to_dict(self) -> dict:
        """Get config as dictionary"""
        return {
            'BOT_TOKEN': self.BOT_TOKEN,
            'BOT_NAME': self.BOT_NAME,
            'DATABASE_URL': self.DATABASE_URL,
            'ADMIN_PASSWORD': '***' if self.ADMIN_PASSWORD else 'NOT SET',
            'LOG_LEVEL': self.LOG_LEVEL,
            'REQUIRED_CHANNEL': self.REQUIRED_CHANNEL,
        }
