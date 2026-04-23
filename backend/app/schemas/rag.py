from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.rag import KnowledgeType


class RagKnowledgeItemCreate(BaseModel):
    kb_type: KnowledgeType
    title: str
    content: str
    tags: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_active: bool = True


class RagKnowledgeItemUpdate(BaseModel):
    kb_type: Optional[KnowledgeType] = None
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RagKnowledgeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kb_type: KnowledgeType
    title: str
    content: str
    tags: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    kb_type: Optional[KnowledgeType] = None
    tag: Optional[str] = None


class RagSearchHit(BaseModel):
    id: int
    kb_type: KnowledgeType
    title: str
    content: str
    tags: Optional[str] = None
    score: float


class RagSearchResponse(BaseModel):
    query: str
    top_k: int
    total_hits: int
    hits: List[RagSearchHit]


class RagRebuildResponse(BaseModel):
    indexed_count: int
    index_path: str
    ids_path: str

