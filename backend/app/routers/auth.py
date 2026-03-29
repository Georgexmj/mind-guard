from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenResponse, RefreshTokenRequest
from app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    user = auth_service.register(db, data)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with phone and password; returns JWT tokens."""
    return auth_service.login(db, data.phone, data.password)


@router.post("/refresh", response_model=dict)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    Returns: {access_token, token_type}
    """
    return auth_service.refresh_access_token(db, data.refresh_token)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user
