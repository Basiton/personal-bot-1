"""
Admin Panel - FastAPI Web Interface
"""

import os
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

from database.models import Base, User, Referral, BroadcastMessage
from utils.config import Config

# Config
config = Config()

# Database
db_url = config.DATABASE_URL
if db_url.startswith('sqlite:///'):
    db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')

engine = None
AsyncSessionLocal = None

# FastAPI
app = FastAPI(title="MAX Bot Admin", version="1.0")


async def init_db():
    """Initialize database"""
    global engine, AsyncSessionLocal
    
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


async def get_db():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session


def check_auth(request: Request):
    """Check authentication"""
    password = request.headers.get('X-Admin-Password')
    if password != config.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    return True


@app.on_event("startup")
async def startup():
    """Startup event"""
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    if engine:
        await engine.dispose()


@app.get("/", response_class=HTMLResponse)
async def index():
    """Admin panel home page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MAX Bot Admin Panel</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                padding: 40px;
                max-width: 600px;
                width: 100%;
            }
            h1 { color: #333; margin-bottom: 10px; }
            p { color: #666; margin-bottom: 30px; font-size: 16px; }
            .stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-box {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-number { font-size: 32px; font-weight: bold; color: #667eea; }
            .stat-label { font-size: 12px; color: #999; margin-top: 5px; }
            .actions {
                display: flex;
                gap: 10px;
                flex-direction: column;
            }
            button {
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s;
            }
            .btn-primary {
                background: #667eea;
                color: white;
            }
            .btn-primary:hover { background: #5568d3; }
            .btn-secondary {
                background: #f0f0f0;
                color: #333;
            }
            .btn-secondary:hover { background: #e0e0e0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 MAX Bot Admin</h1>
            <p>Управление ботом и пользователями</p>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number" id="user-count">-</div>
                    <div class="stat-label">Пользователей</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number" id="referral-count">-</div>
                    <div class="stat-label">Рефералов</div>
                </div>
            </div>
            
            <div class="actions">
                <button class="btn-primary" onclick="loadStats()">📊 Статистика</button>
                <button class="btn-primary" onclick="loadUsers()">👥 Пользователи</button>
                <button class="btn-secondary" onclick="loadBroadcast()">📤 Рассылка</button>
            </div>
            
            <div id="content" style="margin-top: 30px;"></div>
        </div>
        
        <script>
            const apiBase = '/api';
            const password = prompt('Введи пароль админа:');
            
            if (!password) {
                alert('Доступ запрещен');
                window.location.href = '/';
            }
            
            async function fetchAPI(endpoint) {
                const response = await fetch(apiBase + endpoint, {
                    headers: {
                        'X-Admin-Password': password,
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.status === 401) {
                    alert('Неверный пароль');
                    window.location.href = '/';
                    return null;
                }
                
                return response.json();
            }
            
            async function loadStats() {
                const data = await fetchAPI('/stats');
                if (data) {
                    document.getElementById('user-count').innerText = data.total_users;
                    document.getElementById('referral-count').innerText = data.total_referrals;
                    document.getElementById('content').innerHTML = '<p>✅ Статистика загружена</p>';
                }
            }
            
            async function loadUsers() {
                const data = await fetchAPI('/users');
                if (data) {
                    let html = '<h3>Пользователи</h3><ul>';
                    data.users.forEach(user => {
                        html += `<li>${user.username} (${user.user_id}) - ${user.points} pts</li>`;
                    });
                    html += '</ul>';
                    document.getElementById('content').innerHTML = html;
                }
            }
            
            async function loadBroadcast() {
                document.getElementById('content').innerHTML = '<p>Рассылка недоступна в демо</p>';
            }
            
            // Load stats on page load
            loadStats();
        </script>
    </body>
    </html>
    """
    return html_content


@app.get("/api/stats")
async def get_stats(auth=Depends(check_auth), session: AsyncSession = Depends(get_db)):
    """Get statistics"""
    # Count users
    user_stmt = select(func.count(User.id))
    user_result = await session.execute(user_stmt)
    total_users = user_result.scalar() or 0
    
    # Count referrals
    ref_stmt = select(func.count(Referral.id))
    ref_result = await session.execute(ref_stmt)
    total_referrals = ref_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_referrals": total_referrals,
        "active_users": total_users,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/users")
async def get_users(auth=Depends(check_auth), session: AsyncSession = Depends(get_db)):
    """Get all users"""
    stmt = select(User).limit(100)
    result = await session.execute(stmt)
    users = result.scalars().all()
    
    return {
        "users": [
            {
                "user_id": user.user_id,
                "username": user.username,
                "points": user.points,
                "is_active": user.is_active,
                "joined_date": user.joined_date.isoformat()
            }
            for user in users
        ]
    }


@app.get("/api/user/{user_id}")
async def get_user_detail(
    user_id: str,
    auth=Depends(check_auth),
    session: AsyncSession = Depends(get_db)
):
    """Get user details"""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count referrals
    ref_stmt = select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    ref_result = await session.execute(ref_stmt)
    referral_count = ref_result.scalar() or 0
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "points": user.points,
        "referral_count": referral_count,
        "is_active": user.is_active,
        "joined_date": user.joined_date.isoformat(),
        "last_activity": user.last_activity.isoformat()
    }


@app.post("/api/broadcast")
async def create_broadcast(
    message: dict,
    auth=Depends(check_auth),
    session: AsyncSession = Depends(get_db)
):
    """Create broadcast message"""
    broadcast = BroadcastMessage(
        message_text=message.get('text', ''),
        total_count=0,
        sent_count=0,
        is_completed=False
    )
    session.add(broadcast)
    await session.commit()
    
    return {"status": "broadcast created", "id": broadcast.id}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "bot": config.BOT_NAME}


if __name__ == "__main__":
    import uvicorn
    
    port = config.ADMIN_PORT
    print(f"🚀 Admin panel starting on http://localhost:{port}")
    print(f"📝 Password: {config.ADMIN_PASSWORD}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
