from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db, require_admin
from app.db.models.user import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/admin/users", tags=["admin/users"])

@router.get("/", response_model=list[UserOut])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(require_admin)
):
    result = await db.execute(select(User).limit(limit).offset(offset))
    return result.scalars().all()

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID, 
    data: UserUpdate, 
    db: AsyncSession = Depends(get_db), 
    admin=Depends(require_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"status": "deleted"}