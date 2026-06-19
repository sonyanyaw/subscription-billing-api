from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.enums import UserRole
from app.db.session import AsyncSessionLocal
from app.core.security import decode_token
from app.db.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/form")

_USAGE_SKIP_PREFIXES = ("/auth", "/docs", "/openapi", "/health", "/static", "/webhooks")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("sub")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user

def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def check_usage_limit(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if any(request.url.path.startswith(p) for p in _USAGE_SKIP_PREFIXES):
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return

    payload = decode_token(auth_header[7:])
    if not payload:
        return

    user_id = payload.get("sub")
    if not user_id:
        return

    from app.services.usage_limiter import UsageLimiterService
    await UsageLimiterService.check_and_increment(db, user_id)
    await db.commit()