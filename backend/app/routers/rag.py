from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.rag import KnowledgeType, RagKnowledgeItem
from app.models.user import User, UserRole
from app.schemas.rag import (
    RagKnowledgeItemCreate,
    RagKnowledgeItemOut,
    RagKnowledgeItemUpdate,
    RagRebuildResponse,
    RagSearchHit,
    RagSearchRequest,
    RagSearchResponse,
)
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])


def _ensure_manager(user: User):
    if user.role not in (UserRole.admin, UserRole.doctor):
        raise HTTPException(status_code=403, detail="Only admin/doctor can manage RAG knowledge base")


@router.get("/items", response_model=List[RagKnowledgeItemOut])
def list_items(
    kb_type: Optional[KnowledgeType] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_manager(current_user)
    q = db.query(RagKnowledgeItem)
    if kb_type is not None:
        q = q.filter(RagKnowledgeItem.kb_type == kb_type)
    if is_active is not None:
        q = q.filter(RagKnowledgeItem.is_active == is_active)
    return q.order_by(RagKnowledgeItem.updated_at.desc()).all()


@router.post("/items", response_model=RagKnowledgeItemOut)
def create_item(
    payload: RagKnowledgeItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_manager(current_user)
    item = RagKnowledgeItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=RagKnowledgeItemOut)
def update_item(
    item_id: int,
    payload: RagKnowledgeItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_manager(current_user)
    item = db.query(RagKnowledgeItem).filter(RagKnowledgeItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="RAG knowledge item not found")

    updates = payload.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)
    return item


@router.post("/rebuild", response_model=RagRebuildResponse)
def rebuild_index(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_manager(current_user)
    indexed_count, index_path, ids_path = rag_service.rebuild(db)
    return RagRebuildResponse(indexed_count=indexed_count, index_path=index_path, ids_path=ids_path)


@router.post("/search", response_model=RagSearchResponse)
def search_knowledge(
    payload: RagSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Any authenticated role can search knowledge to power explainable outputs.
    _ = current_user

    top_k = max(1, min(payload.top_k, 20))
    hits = rag_service.search(
        db,
        query=payload.query,
        top_k=top_k,
        kb_type=payload.kb_type,
        tag=payload.tag,
    )
    items = [
        RagSearchHit(
            id=item.id,
            kb_type=item.kb_type,
            title=item.title,
            content=item.content,
            tags=item.tags,
            score=score,
        )
        for item, score in hits
    ]
    return RagSearchResponse(
        query=payload.query,
        top_k=top_k,
        total_hits=len(items),
        hits=items,
    )

