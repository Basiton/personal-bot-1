#!/usr/bin/env python3
"""
MAX Messenger Bot - Polling Mode (Local Development)
Работает без вебхука, БЕЗ СЕРВЕРА
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from maxapi import MaxAPI, Message, Update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database.models import Base, User
from database.queries import (
    add_user, get_user, create_referral_link, 
    log_referral, get_user_stats, get_top_referrers,
    get_all_users, update_user_points
)
from utils.config import Config
from utils.validators import (
    is_valid_username, is_valid_referral_code,
    sanitize_message, validate_chat_id
)
from utils.link_generator import (
    generate_referral_link, extract_referral_code,
    generate_short_code
)

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
config = Config()

# Database setup
engine = None
AsyncSessionLocal = None
bot = None


async def init_db():
    """Initialize database"""
    global engine, AsyncSessionLocal
    
    db_url = config.DATABASE_URL
    if db_url.startswith('sqlite:///'):
        db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
    
    engine = create_async_engine(
        db_url,
        echo=False,
        future=True
    )
    
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database initialized")


async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session


async def handle_start(chat_id: str, username: str = None):
    """Handle /start command"""
    try:
        # Check user exists
        async with AsyncSessionLocal() as session:
            user = await get_user(session, chat_id)
            
            if not user:
                # New user - register
                new_user = await add_user(
                    session, 
                    chat_id, 
                    username or f"user_{chat_id[:8]}"
                )
                logger.info(f"✅ New user registered: {chat_id}")
            
            # Send welcome
            message = (
                "👋 Добро пожаловать!\n\n"
                "Это бот MAX Messenger.\n\n"
                "Команды:\n"
                "/help - справка\n"
                "/ref - реф-ссылка\n"
                "/stats - статистика"
            )
            
            await bot.send_message(
                chat_id=chat_id,
                text=message
            )
            logger.info(f"✅ Welcome sent to {chat_id}")
    
    except Exception as e:
        logger.error(f"❌ Error in /start: {e}")


async def handle_help(chat_id: str):
    """Handle /help command"""
    try:
        message = (
            "📖 Справка\n\n"
            "/start - начать\n"
            "/help - эта справка\n"
            "/ref - получить реф-ссылку\n"
            "/stats - посмотреть статистику\n\n"
            "Введи реф-код для бонуса!"
        )
        
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"✅ Help sent to {chat_id}")
    
    except Exception as e:
        logger.error(f"❌ Error in /help: {e}")


async def handle_ref(chat_id: str):
    """Handle /ref command"""
    try:
        async with AsyncSessionLocal() as session:
            user = await get_user(session, chat_id)
            
            if user:
                ref_link = generate_referral_link(
                    user.user_id,
                    config.BOT_NAME
                )
                
                message = (
                    f"🔗 Твоя реф-ссылка:\n\n"
                    f"`{ref_link}`\n\n"
                    f"Приглашай друзей и получай баллы!"
                )
                
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
                logger.info(f"✅ Ref link sent to {chat_id}")
    
    except Exception as e:
        logger.error(f"❌ Error in /ref: {e}")


async def handle_stats(chat_id: str):
    """Handle /stats command"""
    try:
        async with AsyncSessionLocal() as session:
            stats = await get_user_stats(session, chat_id)
            
            message = (
                f"📊 Твоя статистика:\n\n"
                f"👤 ID: {chat_id}\n"
                f"⭐ Баллы: {stats.get('points', 0)}\n"
                f"👥 Рефералов: {stats.get('referrals', 0)}\n"
                f"📅 Дата присоединения: {stats.get('joined_date', 'N/A')}\n"
            )
            
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"✅ Stats sent to {chat_id}")
    
    except Exception as e:
        logger.error(f"❌ Error in /stats: {e}")


async def handle_message(update: Update):
    """Handle incoming message"""
    try:
        if not update.message:
            return
        
        chat_id = str(update.message.chat_id)
        username = update.message.from_user.username if update.message.from_user else None
        text = update.message.text or ""
        
        if not validate_chat_id(chat_id):
            logger.warning(f"⚠️ Invalid chat_id: {chat_id}")
            return
        
        logger.info(f"📨 Message from {chat_id}: {text[:50]}")
        
        # Register user if not exists
        async with AsyncSessionLocal() as session:
            user = await get_user(session, chat_id)
            if not user:
                await add_user(session, chat_id, username or f"user_{chat_id[:8]}")
        
        # Handle commands
        if text.startswith('/start'):
            await handle_start(chat_id, username)
        
        elif text.startswith('/help'):
            await handle_help(chat_id)
        
        elif text.startswith('/ref'):
            await handle_ref(chat_id)
        
        elif text.startswith('/stats'):
            await handle_stats(chat_id)
        
        # Handle referral code
        elif len(text.strip()) > 0 and is_valid_referral_code(text.strip()):
            ref_code = text.strip()
            async with AsyncSessionLocal() as session:
                result = await log_referral(session, chat_id, ref_code)
                if result:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="✅ Код принят! +10 баллов"
                    )
                    logger.info(f"✅ Referral logged: {chat_id} from {ref_code}")
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="❌ Код не найден"
                    )
        
        # Echo
        else:
            sanitized = sanitize_message(text)
            await bot.send_message(
                chat_id=chat_id,
                text=f"📝 Ты написал: {sanitized}"
            )
    
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")


async def polling_loop():
    """Main polling loop"""
    global bot
    
    await init_db()
    
    bot = MaxAPI(token=config.BOT_TOKEN)
    
    logger.info("╔════════════════════════════════════════╗")
    logger.info("║   MAX MESSENGER BOT - POLLING MODE     ║")
    logger.info("║      (LOCAL DEVELOPMENT)               ║")
    logger.info("╚════════════════════════════════════════╝")
    logger.info("")
    logger.info("============================================")
    logger.info(f"🤖 Bot: {config.BOT_NAME}")
    logger.info(f"💾 Database: {config.DATABASE_URL}")
    logger.info("✅ Database initialized")
    logger.info("✅ Bot initialized: " + config.BOT_NAME)
    logger.info("🚀 Bot started in polling mode")
    logger.info("⏳ Waiting for messages...")
    logger.info("============================================")
    logger.info("")
    logger.info("✅ БОТ ЗАПУЩЕН В РЕЖИМЕ РАЗРАБОТКИ")
    logger.info("📲 Можешь писать в MAX мессенджер")
    logger.info("🛑 Ctrl+C для остановки")
    logger.info("")
    
    offset = 0
    
    while True:
        try:
            updates = await bot.get_updates(offset=offset, timeout=30)
            
            if updates:
                for update in updates:
                    try:
                        await handle_message(update)
                        offset = update.update_id + 1
                    except Exception as e:
                        logger.error(f"❌ Error processing update: {e}")
                        offset = update.update_id + 1
        
        except Exception as e:
            logger.error(f"❌ Polling error: {e}")
            await asyncio.sleep(5)


async def main():
    """Main function"""
    try:
        await polling_loop()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
