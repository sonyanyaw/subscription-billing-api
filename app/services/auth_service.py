from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from datetime import datetime, timedelta

class AuthService:

    @staticmethod
    async def register_user(db: AsyncSession, email: str, password: str) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

        user = User(email=email, hashed_password=hash_password(password))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str):
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def create_tokens(db: AsyncSession, user: User):
        access_token = create_access_token(str(user.id))
        refresh_token_str = create_refresh_token(str(user.id))

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_password(refresh_token_str),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(refresh_token)
        await db.commit()

        return {"access_token": access_token, "refresh_token": refresh_token_str, "token_type": "bearer"}
    
    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token_str: str):
        payload = decode_token(refresh_token_str)
        if not payload:
            return None

        user_id = payload.get("sub")

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
        )
        tokens = result.scalars().all()

        valid_token = None
        for token in tokens:
            if verify_password(refresh_token_str, token.token_hash):
                valid_token = token
                break

        if not valid_token:
            return None

        valid_token.revoked = True

        access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)

        new_db_token = RefreshToken(
            user_id=user_id,
            token_hash=hash_password(new_refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(new_db_token)

        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }