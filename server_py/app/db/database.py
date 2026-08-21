import os
import uuid
import time
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from passlib.context import CryptContext
from app.config import settings
from app.db.models import Base, User, Setting

DATABASE_URL = f"sqlite+aiosqlite:///{settings.db_path}"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize default admin if no users exist
    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(User))
        users = result.scalars().all()
        if not users:
            admin_id = str(uuid.uuid4())
            admin_user = User(
                id=admin_id,
                username="admin",
                password_hash=hash_password("admin"),
                role="admin",
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )
            session.add(admin_user)
            await session.commit()
            print(f"[Warden DB] Created initial admin user: admin / admin")
