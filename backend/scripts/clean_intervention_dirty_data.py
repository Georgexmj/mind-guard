"""
Clean dirty intervention demo data such as "????" placeholders.

Usage:
  python -m scripts.clean_intervention_dirty_data           # dry run
  python -m scripts.clean_intervention_dirty_data --apply   # apply updates
"""

from __future__ import annotations

import argparse
import re

from app.database import SessionLocal
from app.models.intervention import InterventionAdherenceTicket, InterventionPlan


DIRTY_TEXT_RE = re.compile(r"(\?{2,}|�|锟)", re.IGNORECASE)

DOMAIN_LABELS = {
    "memory": "记忆",
    "orientation": "定向",
    "attention": "注意",
    "language": "语言",
    "visuospatial": "视空间",
    "executive": "执行功能",
}


def is_dirty_text(value: str | None) -> bool:
    return bool(value and DIRTY_TEXT_RE.search(value.strip()))


def split_domains(domain_focus: str | None) -> list[str]:
    if not domain_focus:
        return []
    return [part.strip() for part in domain_focus.split(",") if part.strip()]


def build_plan_title(domain_focus: str | None) -> str:
    labels = [DOMAIN_LABELS.get(code, code) for code in split_domains(domain_focus)]
    if not labels:
        return "AI-认知训练计划"
    if len(labels) == 1:
        return f"AI-{labels[0]}训练"
    return f"AI-{labels[0]}与{labels[1]}训练"


def build_plan_description(domain_focus: str | None) -> str:
    labels = [DOMAIN_LABELS.get(code, code) for code in split_domains(domain_focus)]
    if not labels:
        return "个体化认知训练计划。"
    return f"当前评估显示“{'、'.join(labels)}”相对薄弱，该干预可针对性改善相关认知功能。"


def normalize_domain_focus(domain_focus: str | None) -> str:
    domains = split_domains(domain_focus)
    if domains:
        return ",".join(domains)
    return "memory,attention"


def run(apply: bool) -> None:
    db = SessionLocal()
    updated_plans = 0
    updated_tickets = 0

    try:
        plans = db.query(InterventionPlan).all()
        for plan in plans:
            touched = False

            if is_dirty_text(plan.title):
                plan.title = build_plan_title(plan.domain_focus)
                touched = True

            if is_dirty_text(plan.description) or not (plan.description or "").strip():
                plan.description = build_plan_description(plan.domain_focus)
                touched = True

            if is_dirty_text(plan.frequency) or not (plan.frequency or "").strip():
                plan.frequency = "每天1次"
                touched = True

            if not split_domains(plan.domain_focus):
                plan.domain_focus = normalize_domain_focus(plan.domain_focus)
                touched = True

            if touched:
                updated_plans += 1

        tickets = db.query(InterventionAdherenceTicket).all()
        for ticket in tickets:
            touched = False

            if is_dirty_text(ticket.followup_note):
                ticket.followup_note = None
                touched = True

            if is_dirty_text(ticket.latest_interruption_reason):
                ticket.latest_interruption_reason = None
                touched = True

            if touched:
                updated_tickets += 1

        if apply:
            db.commit()
            print(f"[APPLY] updated_plans={updated_plans}, updated_tickets={updated_tickets}")
        else:
            db.rollback()
            print(f"[DRY-RUN] updated_plans={updated_plans}, updated_tickets={updated_tickets}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="persist updates")
    args = parser.parse_args()
    run(apply=args.apply)


if __name__ == "__main__":
    main()
