from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.deps import require_role
from app.models.user import User, UserRole, UserRelationship, WechatBinding
from app.schemas.user import (
    BindFamilyRequest,
    FamilyRelationshipOut,
    FamilyUnbindOut,
    UserOut,
    UserUpdate,
    WechatBindingByCodeCreate,
    WechatBindingByCodeOut,
    WechatBindingOut,
    WechatBindingUpsert,
)
from app.services.wechat_service import exchange_code_for_openid

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


def _relation_to_out(row: UserRelationship) -> FamilyRelationshipOut:
    return FamilyRelationshipOut(
        id=row.id,
        elder_id=row.elder_id,
        elder_name=row.elder.name if row.elder else None,
        family_id=row.family_id,
        family_name=row.family_member.name if row.family_member else None,
        relationship=row.relationship,
        notify_level=row.notify_level,
        is_primary=row.is_primary,
        created_at=row.created_at,
    )


def _wechat_binding_to_out(row: WechatBinding) -> WechatBindingOut:
    return WechatBindingOut(
        id=row.id,
        user_id=row.user_id,
        openid=row.openid,
        unionid=row.unionid,
        is_active=row.is_active,
        last_sent_at=row.last_sent_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


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
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
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


@router.get("/family-relationships", response_model=List[FamilyRelationshipOut])
def list_family_relationships(
    elder_id: Optional[int] = Query(None),
    family_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    q = db.query(UserRelationship)
    if elder_id is not None:
        q = q.filter(UserRelationship.elder_id == elder_id)
    if family_id is not None:
        q = q.filter(UserRelationship.family_id == family_id)
    rows = q.order_by(UserRelationship.created_at.desc()).all()
    return [_relation_to_out(row) for row in rows]


@router.delete("/family-relationships/{relation_id}", response_model=FamilyUnbindOut)
def unbind_family(
    relation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    row = db.query(UserRelationship).filter(UserRelationship.id == relation_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Family relationship not found")
    db.delete(row)
    db.commit()
    return FamilyUnbindOut(deleted_id=relation_id, message="Family relationship removed")


@router.get("/wechat-bindings", response_model=List[WechatBindingOut])
def list_wechat_bindings(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.family, UserRole.elder)),
):
    q = db.query(WechatBinding)
    if current_user.role in (UserRole.admin, UserRole.doctor):
        if user_id is not None:
            q = q.filter(WechatBinding.user_id == user_id)
    else:
        q = q.filter(WechatBinding.user_id == current_user.id)
    rows = q.order_by(WechatBinding.created_at.desc()).all()
    return [_wechat_binding_to_out(row) for row in rows]


@router.post("/wechat-bindings", response_model=WechatBindingOut, status_code=status.HTTP_201_CREATED)
def upsert_wechat_binding(
    data: WechatBindingUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.family, UserRole.elder)),
):
    if current_user.role not in (UserRole.admin, UserRole.doctor) and data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only own binding can be updated")

    user = db.query(User).filter(User.id == data.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    row = db.query(WechatBinding).filter(WechatBinding.user_id == data.user_id).first()
    if row is None:
        row = WechatBinding(
            user_id=data.user_id,
            openid=data.openid.strip(),
            unionid=(data.unionid or "").strip() or None,
            is_active=data.is_active,
        )
        db.add(row)
    else:
        row.openid = data.openid.strip()
        row.unionid = (data.unionid or "").strip() or None
        row.is_active = data.is_active

    db.commit()
    db.refresh(row)
    return _wechat_binding_to_out(row)


@router.post("/wechat-bindings/by-code", response_model=WechatBindingByCodeOut, status_code=status.HTTP_201_CREATED)
def upsert_wechat_binding_by_code(
    data: WechatBindingByCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.family, UserRole.elder)),
):
    if current_user.role not in (UserRole.admin, UserRole.doctor) and data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only own binding can be updated")

    user = db.query(User).filter(User.id == data.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        wechat_info = exchange_code_for_openid(data.code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Wechat code exchange failed: {exc}")

    openid = (wechat_info.get("openid") or "").strip()
    if not openid:
        raise HTTPException(status_code=400, detail="Wechat openid missing")

    row = db.query(WechatBinding).filter(WechatBinding.user_id == data.user_id).first()
    if row is None:
        row = db.query(WechatBinding).filter(WechatBinding.openid == openid).first()

    if row is None:
        row = WechatBinding(
            user_id=data.user_id,
            openid=openid,
            unionid=(wechat_info.get("unionid") or "").strip() or None,
            is_active=data.is_active,
        )
        db.add(row)
    else:
        row.user_id = data.user_id
        row.openid = openid
        row.unionid = (wechat_info.get("unionid") or "").strip() or None
        row.is_active = data.is_active

    db.commit()
    db.refresh(row)
    out = _wechat_binding_to_out(row)
    return WechatBindingByCodeOut(**out.model_dump(), mode=str(wechat_info.get("mode") or "unknown"))


@router.delete("/wechat-bindings/{binding_id}", response_model=FamilyUnbindOut)
def remove_wechat_binding(
    binding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.family, UserRole.elder)),
):
    row = db.query(WechatBinding).filter(WechatBinding.id == binding_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Wechat binding not found")
    if current_user.role not in (UserRole.admin, UserRole.doctor) and row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only own binding can be removed")
    db.delete(row)
    db.commit()
    return FamilyUnbindOut(deleted_id=binding_id, message="Wechat binding removed")


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
