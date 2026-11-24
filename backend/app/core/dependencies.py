import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user_model import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Р”РµРєРѕРґРёСЂСѓРµРј РІР°С€ JWT-С‚РѕРєРµРЅ (СѓР±РµРґРёС‚РµСЃСЊ, С‡С‚Рѕ Р°Р»РіРѕСЂРёС‚Рј СЃРѕРІРїР°РґР°РµС‚ СЃ С‚РµРј, С‡С‚Рѕ РІ create_access_token)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # РС‰РµРј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РІ Р±Р°Р·Рµ РґР°РЅРЅС‹С…
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise credentials_exception

    return user