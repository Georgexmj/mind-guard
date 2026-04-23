import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, JSON, String, Text

from app.database import Base


class KnowledgeType(str, enum.Enum):
    rule = "rule"
    intervention = "intervention"
    template = "template"
    faq = "faq"


class RagKnowledgeItem(Base):
    __tablename__ = "rag_knowledge_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kb_type = Column(SAEnum(KnowledgeType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

