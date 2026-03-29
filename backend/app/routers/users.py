from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.deps import require_role
from app.models.user import User, UserRole, UserRelationship
from app.schemas.user import UserOut, UserUpdate, BindFamilyRequest

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    community_id: Optional[int] = Query(None, description="Filter by community"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    """List all users. Admin and doctor access only. Supports filtering and pagination."""
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)
    if community_id is not None:
        query = query.filter(User.community_id == community_id)

    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    return users


@router.get("/elders", response_model=List[UserOut])
def list_elders(
    community_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    """List elder users only. For doctor/admin dashboard."""
    query = db.query(User).filter(User.role == UserRole.elder)
    if community_id is not None:
        query = query.filter(User.community_id == community_id)

    offset = (page - 1) * page_size
    elders = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    return elders


@router.post("/bind-family", status_code=status.HTTP_201_CREATED)
def bind_family(
    data: BindFamilyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.family)),
):
    """Bind a family member to an elder user."""
    elder = db.query(User).filter(User.id == data.elder_id, User.role == UserRole.elder).first()
    if elder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Elder user with id {data.elder_id} not found",
        )

    family = db.query(User).filter(User.id == data.family_id, User.role == UserRole.family).first()
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Family user with id {data.family_id} not found",
        )

    # Check if already bound
    existing = (
        db.query(UserRelationship)
        .filter(
            UserRelationship.elder_id == data.elder_id,
            UserRelationship.family_id == data.family_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Family relationship already exists",
        )

    relationship = UserRelationship(
        elder_id=data.elder_id,
        family_id=data.family_id,
        relationship=data.relationship,
        notify_level=data.notify_level,
        is_primary=data.is_primary,
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    return {
        "id": relationship.id,
        "elder_id": relationship.elder_id,
        "family_id": relationship.family_id,
        "relationship": relationship.relationship,
        "is_primary": relationship.is_primary,
        "message": "Family binding created successfully",
    }


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a user's profile. Users can view their own; admin/doctor can view any."""
    if current_user.role not in (UserRole.admin, UserRole.doctor) and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user's profile. Users can update their own; admin can update any."""
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
