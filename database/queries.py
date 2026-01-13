"""
Database CRUD Operations
"""

from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ReferralLink, Referral, BroadcastMessage
from utils.link_generator import generate_short_code, extract_referral_code


async def add_user(session: AsyncSession, user_id: str, username: str = None) -> User:
    """Add new user"""
    try:
        # Check if user exists
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return existing_user
        
        # Create new user
        new_user = User(
            user_id=user_id,
            username=username or f"user_{user_id[:8]}",
            points=0,
            is_active=True
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        return new_user
    
    except Exception as e:
        await session.rollback()
        raise e


async def get_user(session: AsyncSession, user_id: str) -> User:
    """Get user by ID"""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession, limit: int = 100) -> list:
    """Get all users"""
    stmt = select(User).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_user_points(session: AsyncSession, user_id: str, points: int) -> User:
    """Update user points"""
    try:
        user = await get_user(session, user_id)
        if user:
            user.points += points
            user.last_activity = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
        return user
    
    except Exception as e:
        await session.rollback()
        raise e


async def create_referral_link(session: AsyncSession, user_id: str) -> ReferralLink:
    """Create referral link for user"""
    try:
        # Check if link already exists
        stmt = select(ReferralLink).where(
            ReferralLink.user_id == user_id,
            ReferralLink.is_active == True
        )
        result = await session.execute(stmt)
        existing_link = result.scalar_one_or_none()
        
        if existing_link:
            return existing_link
        
        # Create new link
        ref_code = generate_short_code()
        
        new_link = ReferralLink(
            user_id=user_id,
            ref_code=ref_code,
            is_active=True
        )
        session.add(new_link)
        await session.commit()
        await session.refresh(new_link)
        
        return new_link
    
    except Exception as e:
        await session.rollback()
        raise e


async def get_referral_link(session: AsyncSession, user_id: str) -> ReferralLink:
    """Get referral link by user ID"""
    stmt = select(ReferralLink).where(
        ReferralLink.user_id == user_id,
        ReferralLink.is_active == True
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_referral_link_by_code(session: AsyncSession, ref_code: str) -> ReferralLink:
    """Get referral link by code"""
    stmt = select(ReferralLink).where(
        ReferralLink.ref_code == ref_code,
        ReferralLink.is_active == True
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def log_referral(session: AsyncSession, referred_user_id: str, ref_code: str) -> bool:
    """Log referral"""
    try:
        # Find referral link by code
        ref_link = await get_referral_link_by_code(session, ref_code)
        
        if not ref_link:
            return False
        
        # Check if user already used this code
        stmt = select(Referral).where(
            Referral.referred_user_id == referred_user_id,
            Referral.ref_code_used == ref_code
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            return False  # Already used
        
        # Create referral record
        new_referral = Referral(
            referrer_id=ref_link.user_id,
            referred_user_id=referred_user_id,
            ref_code_used=ref_code,
            points_awarded=10
        )
        session.add(new_referral)
        
        # Update referrer points
        referrer = await get_user(session, ref_link.user_id)
        if referrer:
            referrer.points += 10
            referrer.last_activity = datetime.utcnow()
        
        # Update referral link uses count
        ref_link.uses_count += 1
        
        # Register referred user if not exists
        referred_user = await get_user(session, referred_user_id)
        if not referred_user:
            await add_user(session, referred_user_id)
        
        await session.commit()
        return True
    
    except Exception as e:
        await session.rollback()
        raise e


async def get_user_stats(session: AsyncSession, user_id: str) -> dict:
    """Get user statistics"""
    user = await get_user(session, user_id)
    
    if not user:
        return {}
    
    # Count referrals
    stmt = select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    result = await session.execute(stmt)
    referral_count = result.scalar() or 0
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "points": user.points,
        "referrals": referral_count,
        "joined_date": user.joined_date.strftime("%Y-%m-%d"),
        "is_active": user.is_active
    }


async def get_top_referrers(session: AsyncSession, limit: int = 10) -> list:
    """Get top referrers by points"""
    stmt = select(User).order_by(desc(User.points)).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_referral_count(session: AsyncSession, user_id: str) -> int:
    """Get referral count for user"""
    stmt = select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    result = await session.execute(stmt)
    return result.scalar() or 0


async def create_broadcast(session: AsyncSession, message_text: str) -> BroadcastMessage:
    """Create broadcast message"""
    try:
        # Count total users
        stmt = select(func.count(User.id))
        result = await session.execute(stmt)
        total_users = result.scalar() or 0
        
        broadcast = BroadcastMessage(
            message_text=message_text,
            total_count=total_users,
            sent_count=0,
            is_completed=False
        )
        session.add(broadcast)
        await session.commit()
        await session.refresh(broadcast)
        
        return broadcast
    
    except Exception as e:
        await session.rollback()
        raise e


async def get_pending_broadcasts(session: AsyncSession) -> list:
    """Get pending broadcasts"""
    stmt = select(BroadcastMessage).where(
        BroadcastMessage.is_completed == False
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def mark_broadcast_completed(session: AsyncSession, broadcast_id: int):
    """Mark broadcast as completed"""
    try:
        broadcast = await session.get(BroadcastMessage, broadcast_id)
        if broadcast:
            broadcast.is_completed = True
            await session.commit()
    
    except Exception as e:
        await session.rollback()
        raise e


async def get_user_count(session: AsyncSession) -> int:
    """Get total user count"""
    stmt = select(func.count(User.id))
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_active_user_count(session: AsyncSession, days: int = 7) -> int:
    """Get active users count (last N days)"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stmt = select(func.count(User.id)).where(User.last_activity >= cutoff_date)
    result = await session.execute(stmt)
    return result.scalar() or 0
