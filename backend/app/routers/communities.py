from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.user import Community
from app.schemas.user import CommunityOut, CommunityCreate

router = APIRouter(prefix="/api/v1/communities", tags=["Communities"])


@router.get("/", response_model=List[CommunityOut])
def list_communities(
    province: Optional[str] = Query(None, description="Filter by province"),
    city: Optional[str] = Query(None, description="Filter by city"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all communities. Accessible to all authenticated users."""
    query = db.query(Community)

    if province is not None:
        query = query.filter(Community.province == province)
    if city is not None:
        query = query.filter(Community.city == city)

    offset = (page - 1) * page_size
    communities = query.order_by(Community.name).offset(offset).limit(page_size).all()
    return communities


@router.post("/", response_model=CommunityOut, status_code=status.HTTP_201_CREATED)
def create_community(
    data: CommunityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    """Create a new community. Admin access only."""
    # Check for duplicate name in same city
    existing = (
        db.query(Community)
        .filter(Community.name == data.name, Community.city == data.city)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Community '{data.name}' already exists in {data.city}",
        )

    community = Community(
        name=data.name,
        province=data.province,
        city=data.city,
        district=data.district,
        address=data.address,
        elder_count=data.elder_count,
    )
    db.add(community)
    db.commit()
    db.refresh(community)
    return community
