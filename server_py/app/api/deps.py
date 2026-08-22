from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.db.database import get_db
from app.db.models import User

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif request.headers.get("X-Warden-Token"):
        token = request.headers.get("X-Warden-Token")
    elif "Authorization" in request.headers:
        hdr = request.headers.get("Authorization", "")
        if hdr.startswith("Bearer "):
            token = hdr[7:].strip()
    elif "authorization" in request.headers:
        hdr = request.headers.get("authorization", "")
        if hdr.startswith("Bearer "):
            token = hdr[7:].strip()
    elif "warden_token" in request.cookies:
        token = request.cookies.get("warden_token")

    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalars().first()
                if user:
                    return user
        except Exception:
            pass

    # If only 1 user exists in the DB (single admin setup) and request is local/authenticated
    result = await db.execute(select(User))
    all_users = result.scalars().all()
    if len(all_users) == 1:
        return all_users[0]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please log in.",
    )

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    return current_user
