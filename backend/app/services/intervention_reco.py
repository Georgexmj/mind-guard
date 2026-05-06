from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from app.models.assessment import AssessmentResult

DOMAIN_LABELS: Dict[str, str] = {
    "memory": "\u8bb0\u5fc6\u529b",
    "orientation": "\u5b9a\u5411\u529b",
    "language": "\u8bed\u8a00\u80fd\u529b",
    "attention": "\u6ce8\u610f\u529b",
    "visuospatial": "\u89c6\u7a7a\u95f4\u80fd\u529b",
    "executive": "\u6267\u884c\u529f\u80fd",
}

INTERVENTION_CATALOG: List[Dict[str, Any]] = [
    {
        "code": "memory_association",
        "title": "\u8bcd\u8bed\u8054\u60f3\u8bb0\u5fc6\u8bad\u7ec3",
        "category": "\u8ba4\u77e5\u8bad\u7ec3",
        "domain_weights": {"memory": 1.0, "attention": 0.35},
        "frequency": "\u6bcf\u59291\u6b21",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "orientation_calendar",
        "title": "\u65e5\u5386\u4e0e\u5730\u70b9\u5b9a\u5411\u7ec3\u4e60",
        "category": "\u5b9a\u5411\u8bad\u7ec3",
        "domain_weights": {"orientation": 1.0, "memory": 0.2},
        "frequency": "\u6bcf\u59291\u6b21",
        "duration_minutes": 12,
        "evidence_level": "B",
    },
    {
        "code": "attention_serial",
        "title": "\u4e13\u6ce8\u529b\u4e0e\u5e8f\u5217\u8ba1\u7b97\u8bad\u7ec3",
        "category": "\u6ce8\u610f\u529b\u8bad\u7ec3",
        "domain_weights": {"attention": 1.0, "executive": 0.25},
        "frequency": "\u6bcf\u59291\u6b21",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "language_fluency",
        "title": "\u8bed\u8a00\u6d41\u7545\u4e0e\u590d\u8ff0\u8bad\u7ec3",
        "category": "\u8bed\u8a00\u8bad\u7ec3",
        "domain_weights": {"language": 1.0, "memory": 0.25},
        "frequency": "\u6bcf\u59291\u6b21",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "visuospatial_clock",
        "title": "\u65f6\u949f\u7ed8\u5236\u4e0e\u89c6\u7a7a\u95f4\u8bad\u7ec3",
        "category": "\u89c6\u7a7a\u95f4\u8bad\u7ec3",
        "domain_weights": {"visuospatial": 1.0, "executive": 0.3},
        "frequency": "\u9694\u59291\u6b21",
        "duration_minutes": 12,
        "evidence_level": "C",
    },
    {
        "code": "executive_planning",
        "title": "\u6267\u884c\u529f\u80fd\u8ba1\u5212\u4efb\u52a1\u8bad\u7ec3",
        "category": "\u6267\u884c\u8bad\u7ec3",
        "domain_weights": {"executive": 1.0, "attention": 0.3},
        "frequency": "\u6bcf\u54685\u6b21",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "aerobic_walk",
        "title": "\u4e2d\u7b49\u5f3a\u5ea6\u6b65\u884c\u5e72\u9884",
        "category": "\u8fd0\u52a8\u5e72\u9884",
        "domain_weights": {"memory": 0.3, "attention": 0.4, "executive": 0.3},
        "frequency": "\u6bcf\u59291\u6b21",
        "duration_minutes": 30,
        "evidence_level": "A",
    },
    {
        "code": "social_engagement",
        "title": "\u793e\u4ea4\u4e92\u52a8\u4e0e\u60c5\u7eea\u6fc0\u6d3b",
        "category": "\u793e\u4ea4\u5e72\u9884",
        "domain_weights": {"language": 0.45, "orientation": 0.25, "executive": 0.3},
        "frequency": "\u6bcf\u54683\u6b21",
        "duration_minutes": 40,
        "evidence_level": "B",
    },
]


def safe_domain_scores(result: AssessmentResult) -> Dict[str, float]:
    raw = result.domain_scores if isinstance(result.domain_scores, dict) else {}
    return {
        "memory": float(raw.get("memory", 5.0)),
        "orientation": float(raw.get("orientation", 5.0)),
        "language": float(raw.get("language", 5.0)),
        "attention": float(raw.get("attention", 5.0)),
        "visuospatial": float(raw.get("visuospatial", 5.0)),
        "executive": float(raw.get("executive", 5.0)),
    }


def build_top5_from_result(result: AssessmentResult) -> List[Dict[str, Any]]:
    domain_scores = safe_domain_scores(result)
    deficits = {key: max(0.0, 10.0 - score) / 10.0 for key, score in domain_scores.items()}
    risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)

    risk_boost = {
        "high_risk": 1.16,
        "mild_risk": 1.08,
        "normal": 1.0,
    }.get(risk_level, 1.0)

    ranked: List[Dict[str, Any]] = []
    for item in INTERVENTION_CATALOG:
        weighted_gap = sum(
            deficits.get(domain, 0.0) * weight
            for domain, weight in item["domain_weights"].items()
        )
        priority_score = round(weighted_gap * 100.0 * risk_boost, 2)
        domain_labels = [DOMAIN_LABELS.get(d, d) for d in item["domain_weights"].keys()]
        sep = "\u3001"
        rationale = (
            f"\u5f53\u524d\u8bc4\u4f30\u663e\u793a\u201c{sep.join(domain_labels[:2])}\u201d\u76f8\u5bf9\u8584\u5f31\uff0c"
            "\u8be5\u5e72\u9884\u53ef\u9488\u5bf9\u6027\u6539\u5584\u76f8\u5173\u8ba4\u77e5\u529f\u80fd\u3002"
        )
        ranked.append(
            {
                **item,
                "target_domains": list(item["domain_weights"].keys()),
                "priority_score": priority_score,
                "rationale": rationale,
            }
        )

    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    top5 = ranked[:5]

    outputs: List[Dict[str, Any]] = []
    for idx, item in enumerate(top5, start=1):
        outputs.append(
            {
                "rank": idx,
                "code": item["code"],
                "title": item["title"],
                "category": item["category"],
                "target_domains": item["target_domains"],
                "frequency": item["frequency"],
                "duration_minutes": item["duration_minutes"],
                "rationale": item["rationale"],
                "priority_score": item["priority_score"],
                "evidence_level": item["evidence_level"],
            }
        )

    return outputs


def parse_frequency_expected_per_week(frequency: Optional[str]) -> float:
    if not frequency:
        return 7.0

    text = str(frequency).lower()
    digits = [int(ch) for ch in text if ch.isdigit()]
    number = digits[0] if digits else 1

    if "\u9694\u5929" in text or "every other day" in text:
        return max(1.0, 3.5 * number)
    if "\u6bcf\u5468" in text or "per week" in text or "weekly" in text:
        return max(1.0, float(number))
    if "\u6bcf\u5929" in text or "per day" in text or "daily" in text:
        return max(1.0, float(number * 7))
    return 7.0


def suggest_next_reassessment_date(risk_level: str, assessed_date: date) -> date:
    days = {"normal": 180, "mild_risk": 90, "high_risk": 30}.get(str(risk_level), 90)
    return assessed_date + timedelta(days=days)
