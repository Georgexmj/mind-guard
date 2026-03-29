from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.user import UserCreate, TokenResponse, UserOut


def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """Look up a user by phone number."""
    return db.query(User).filter(User.phone == phone).first()


def register(db: Session, data: UserCreate) -> User:
    """
    Register a new user.
    Raises HTTPException 400 if phone already exists.
    """
    existing = get_user_by_phone(db, data.phone)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered",
        )

    user = User(
        phone=data.phone,
        name=data.name,
        birth_date=data.birth_date,
        gender=data.gender,
        education_years=data.education_years,
        role=data.role,
        community_id=data.community_id,
        password_hash=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, phone: str, password: str) -> TokenResponse:
    """
    Authenticate a user by phone and password.
    Returns TokenResponse with access_token, refresh_token, and user info.
    Raises HTTPException 401 on invalid credentials or inactive account.
    """
    user = get_user_by_phone(db, phone)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated",
        )

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    user_out = UserOut.model_validate(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_out,
    )


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    """
    Validate a refresh token and issue a new access token.
    Returns dict with new access_token.
    """
    from app.core.security import decode_token

    payload = decode_token(refresh_token)
    token_type = payload.get("type")
    user_id = payload.get("sub")

    if token_type != "refresh" or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {"sub": str(user.id), "role": user.role.value}
    new_access_token = create_access_token(data=token_data)
    return {"access_token": new_access_token, "token_type": "bearer"}
