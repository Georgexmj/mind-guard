from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import List, Optional, Sequence, Tuple
import os
import ctypes

import faiss
import numpy as np
from sqlalchemy.orm import Session

from app.models.rag import KnowledgeType, RagKnowledgeItem

_BASE_DIR = Path(__file__).resolve().parents[2]


def _contains_non_ascii(path: Path) -> bool:
    return any(ord(ch) > 127 for ch in str(path))


def _win_short_path(path: Path) -> Optional[Path]:
    if os.name != "nt":
        return None
    p = str(path)
    buf = ctypes.create_unicode_buffer(32768)
    out_len = ctypes.windll.kernel32.GetShortPathNameW(p, buf, len(buf))
    if out_len == 0:
        return None
    return Path(buf.value)


def _resolve_index_dir() -> Path:
    override = os.getenv("RAG_INDEX_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    default_dir = (_BASE_DIR / "models" / "rag_index").resolve()
    # Keep index inside project by default.
    # On Windows + non-ASCII paths, we handle FAISS I/O via short/relative paths.
    if os.name == "nt" and _contains_non_ascii(default_dir):
        default_dir.mkdir(parents=True, exist_ok=True)
        short_dir = _win_short_path(default_dir)
        if short_dir is not None and not _contains_non_ascii(short_dir):
            return short_dir
        return default_dir
    return default_dir


def _to_faiss_path(path: Path) -> str:
    # FAISS on Windows may fail for non-ASCII absolute paths.
    if os.name == "nt" and _contains_non_ascii(path):
        short = _win_short_path(path)
        if short is not None and not _contains_non_ascii(short):
            return str(short)
        try:
            rel = os.path.relpath(str(path), os.getcwd())
            if rel and all(ord(ch) < 128 for ch in rel):
                return rel
        except ValueError:
            pass
    return str(path)


_INDEX_DIR = _resolve_index_dir()
_INDEX_DIR.mkdir(parents=True, exist_ok=True)
_INDEX_PATH = _INDEX_DIR / "rag_faiss.index"
_IDS_PATH = _INDEX_DIR / "rag_faiss_ids.npy"

_DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class RagService:
    def __init__(self):
        self._model = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._ids: List[int] = []
        self._lock = Lock()

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(_DEFAULT_EMBEDDING_MODEL)
        return self._model

    @staticmethod
    def _to_search_text(item: RagKnowledgeItem) -> str:
        pieces = [
            f"type:{item.kb_type.value}",
            f"title:{item.title}",
            f"tags:{item.tags or ''}",
            f"content:{item.content}",
        ]
        if isinstance(item.metadata_json, dict) and item.metadata_json:
            meta_text = " ".join(f"{k}:{v}" for k, v in item.metadata_json.items())
            pieces.append(f"meta:{meta_text}")
        return "\n".join(pieces)

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self._load_model()
        emb = model.encode(list(texts), normalize_embeddings=True)
        return np.asarray(emb, dtype=np.float32)

    @staticmethod
    def _build_index_from_embeddings(embeddings: np.ndarray) -> faiss.IndexFlatIP:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        return index

    def _save_index(self):
        if self._index is None:
            raise RuntimeError("Index is not built")
        faiss.write_index(self._index, _to_faiss_path(_INDEX_PATH))
        np.save(_IDS_PATH, np.asarray(self._ids, dtype=np.int64))

    def _load_index_from_disk(self) -> bool:
        if not _INDEX_PATH.exists() or not _IDS_PATH.exists():
            return False
        self._index = faiss.read_index(_to_faiss_path(_INDEX_PATH))
        self._ids = np.load(_IDS_PATH).astype(np.int64).tolist()
        return True

    def rebuild(self, db: Session) -> Tuple[int, str, str]:
        with self._lock:
            items = (
                db.query(RagKnowledgeItem)
                .filter(RagKnowledgeItem.is_active == True)
                .order_by(RagKnowledgeItem.id.asc())
                .all()
            )
            if not items:
                self._index = None
                self._ids = []
                if _INDEX_PATH.exists():
                    _INDEX_PATH.unlink()
                if _IDS_PATH.exists():
                    _IDS_PATH.unlink()
                return 0, str(_INDEX_PATH), str(_IDS_PATH)

            texts = [self._to_search_text(item) for item in items]
            embeddings = self._encode(texts)
            self._index = self._build_index_from_embeddings(embeddings)
            self._ids = [item.id for item in items]
            self._save_index()
            return len(items), str(_INDEX_PATH), str(_IDS_PATH)

    def ensure_index_loaded(self):
        with self._lock:
            if self._index is None:
                self._load_index_from_disk()

    def search(
        self,
        db: Session,
        *,
        query: str,
        top_k: int,
        kb_type: Optional[KnowledgeType] = None,
        tag: Optional[str] = None,
    ) -> List[Tuple[RagKnowledgeItem, float]]:
        self.ensure_index_loaded()
        if self._index is None or not self._ids:
            return []

        q = (query or "").strip()
        if not q:
            return []

        q_emb = self._encode([q])
        search_k = min(max(top_k * 8, top_k), len(self._ids))
        scores, indices = self._index.search(q_emb, search_k)

        retrieved_ids = []
        score_map = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._ids):
                continue
            item_id = self._ids[idx]
            if item_id not in score_map:
                score_map[item_id] = float(score)
                retrieved_ids.append(item_id)

        if not retrieved_ids:
            return []

        rows = (
            db.query(RagKnowledgeItem)
            .filter(
                RagKnowledgeItem.id.in_(retrieved_ids),
                RagKnowledgeItem.is_active == True,
            )
            .all()
        )

        id_to_item = {row.id: row for row in rows}
        ordered_rows = []
        for item_id in retrieved_ids:
            item = id_to_item.get(item_id)
            if item is None:
                continue
            if kb_type is not None and item.kb_type != kb_type:
                continue
            if tag:
                tags = (item.tags or "").lower()
                if tag.lower() not in tags:
                    continue
            ordered_rows.append((item, score_map[item_id]))
            if len(ordered_rows) >= top_k:
                break

        return ordered_rows


rag_service = RagService()
