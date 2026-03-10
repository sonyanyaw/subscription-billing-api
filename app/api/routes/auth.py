from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token
from app.api.deps import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import TokenRefresh

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.register_user(db, user_in.email, user_in.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await AuthService.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tokens = await AuthService.create_tokens(db, user)
    return tokens

@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh(data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService.refresh_tokens(db, data.refresh_token)
    if not tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return tokens

@router.post("/login/form", response_model=Token, include_in_schema=False)  
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return await AuthService.create_tokens(db, user)