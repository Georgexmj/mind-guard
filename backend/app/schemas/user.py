from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.models.user import UserRole


class CommunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    province: str
    city: str


class CommunityCreate(BaseModel):
    name: str
    province: str
    city: str
    district: Optional[str] = None
    address: Optional[str] = None
    elder_count: int = 0


class UserCreate(BaseModel):
    phone: str
    name: str
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    education_years: Optional[int] = None
    role: UserRole = UserRole.elder
    community_id: Optional[int] = None
    password: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) < 8:
            raise ValueError("Phone number must be at least 8 digits")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    phone: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    name: str
    phone: str
    role: UserRole
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    education_years: Optional[int] = None
    community_id: Optional[int] = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    education_years: Optional[int] = None
    community_id: Optional[int] = None
    is_active: Optional[bool] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class BindFamilyRequest(BaseModel):
    elder_id: int
    family_id: int
    relationship: str
    notify_level: int = 1
    is_primary: bool = False
