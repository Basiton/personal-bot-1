"""
Database Models - SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    referrals = relationship("Referral", back_populates="referrer")
    referral_links = relationship("ReferralLink", back_populates="user")


class ReferralLink(Base):
    """Referral link model"""
    __tablename__ = "referral_links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    ref_code = Column(String, unique=True, index=True, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    uses_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="referral_links")


class Referral(Base):
    """Referral log model"""
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    referred_user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    ref_code_used = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    points_awarded = Column(Integer, default=10)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals")


class BroadcastMessage(Base):
    """Broadcast message model"""
    __tablename__ = "broadcast_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_text = Column(Text, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    sent_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)


class AdminUser(Base):
    """Admin user model"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class BotStatistics(Base):
    """Bot statistics model"""
    __tablename__ = "bot_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    total_referrals = Column(Integer, default=0)
    total_points_distributed = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow, index=True)
