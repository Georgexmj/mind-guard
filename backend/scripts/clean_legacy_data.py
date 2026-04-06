"""
Clean legacy mojibake/dirty demo data in MySQL.

Usage:
  python -m scripts.clean_legacy_data           # dry run
  python -m scripts.clean_legacy_data --apply   # apply updates
"""

from __future__ import annotations

import argparse
import re
from typing import Dict

from app.database import SessionLocal
from app.models.intervention import InterventionPlan, InterventionRecord
from app.models.user import Community, User


TEXT_FIX_MAP: Dict[str, str] = {
    "骞哥绀惧尯": "幸福社区",
    "闃冲厜绀惧尯": "阳光社区",
    "鍜岃皭绀惧尯": "和谐社区",
    "婀栧崡鐪?": "湖南省",
    "寮犲鐣屽競": "张家界市",
    "姘稿畾鍖?": "永定区",
    "绯荤粺绠＄悊鍛?": "系统管理员",
    "寮犲尰鐢?": "张医生",
    "鏉庡ザ濂?": "李奶奶",
    "鏉庡コ澹?": "李女士",
}


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value
    for src, dst in TEXT_FIX_MAP.items():
        text = text.replace(src, dst)

    # Remove replacement placeholders and control chars.
    text = text.replace("\ufffd", "").replace("�", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\?+$", "", text).strip()
    # Normalize repeated spaces.
    text = re.sub(r"\s{2,}", " ", text)
    return text


def maybe_update(obj, field: str, stats: dict) -> None:
    old = getattr(obj, field, None)
    if old is None:
        return
    new = normalize_text(old)
    if new != old:
        setattr(obj, field, new)
        stats["updated"] += 1


def run(apply: bool) -> None:
    db = SessionLocal()
    stats = {"updated": 0}
    try:
        communities = db.query(Community).all()
        for c in communities:
            maybe_update(c, "name", stats)
            maybe_update(c, "province", stats)
            maybe_update(c, "city", stats)
            maybe_update(c, "district", stats)
            maybe_update(c, "address", stats)

        users = db.query(User).all()
        for u in users:
            maybe_update(u, "name", stats)

        plans = db.query(InterventionPlan).all()
        for p in plans:
            maybe_update(p, "title", stats)
            maybe_update(p, "description", stats)
            maybe_update(p, "frequency", stats)

        records = db.query(InterventionRecord).all()
        for r in records:
            maybe_update(r, "notes", stats)

        if apply:
            db.commit()
            print(f"[APPLY] Updated fields: {stats['updated']}")
        else:
            db.rollback()
            print(f"[DRY-RUN] Would update fields: {stats['updated']}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="persist updates")
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
