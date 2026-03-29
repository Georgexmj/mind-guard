import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, Text, Date
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    elder = "elder"
    family = "family"
    doctor = "doctor"
    admin = "admin"


class Community(Base):
    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    province = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    district = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    elder_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="community")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    education_years = Column(Integer, nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.elder)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    community = relationship("Community", back_populates="users")
    assessment_sessions = relationship("AssessmentSession", back_populates="user")
    elder_relationships = relationship(
        "UserRelationship",
        foreign_keys="UserRelationship.elder_id",
        back_populates="elder",
    )
    family_relationships = relationship(
        "UserRelationship",
        foreign_keys="UserRelationship.family_id",
        back_populates="family_member",
    )


class UserRelationship(Base):
    __tablename__ = "user_relationships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    elder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    family_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    relationship = Column(String(50), nullable=False)  # e.g. "son", "daughter", "spouse"
    notify_level = Column(Integer, default=1)  # 1=all, 2=high_risk_only, 3=none
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    elder = relationship("User", foreign_keys=[elder_id], back_populates="elder_relationships")
    family_member = relationship("User", foreign_keys=[family_id], back_populates="family_relationships")
