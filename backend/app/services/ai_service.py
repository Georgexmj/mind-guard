"""
Enhanced multimodal analysis service.

Compared with the earlier MVP mock, this version adds:
1) Explicit per-modality feature extraction (questionnaire/voice/drawing/behavior)
2) Modality quality evaluation and missing-modality handling
3) Confidence estimation with data quality gating
4) More structured explainability payload (feature SHAP-like values + modality contributions)
"""

import re
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.assessment import (
    AssessmentResult,
    AssessmentResponse,
    AssessmentSession,
    Question,
    QuestionDomain,
    RiskLevel,
)
from app.models.rag import KnowledgeType
from app.services.deep_model_service import get_deep_model_service
from app.services.notification_service import create_assessment_notifications
from app.services.rag_service import rag_service


DOMAIN_MAX_MMSE_POINTS = {
    "memory": 6,
    "orientation": 10,
    "language": 8,
    "attention": 5,
    "visuospatial": 1,
    "executive": 0,  # retained for unified domain view
}

DOMAIN_LABELS = {
    "memory": "记忆力",
    "orientation": "定向力",
    "language": "语言能力",
    "attention": "注意力",
    "visuospatial": "视空间能力",
    "executive": "执行功能",
}
DOMAIN_ORDER = [d.value for d in QuestionDomain]

MMSE_SUBITEM_MAX_POINTS = {
    "orientation_time": 5,
    "orientation_place": 5,
    "registration": 3,
    "attention_calculation": 5,
    "delayed_recall": 3,
    "naming": 2,
    "repetition": 1,
    "three_step_command": 3,
    "reading": 1,
    "writing": 1,
    "figure_copy": 1,
}

MOCA_SUBITEM_MAX_POINTS = {
    "trail_making": 1,
    "visuospatial": 4,
    "naming": 3,
    "attention": 6,
    "language": 3,
    "abstraction": 2,
    "delayed_recall": 5,
    "orientation": 6,
}

# Requirement FR-05-3: illiterate elders get MoCA +1.
MOCA_EDUCATION_CORRECTION_THRESHOLD = 0
MOCA_EDUCATION_CORRECTION_POINTS = 1.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _count_words(text: str) -> int:
    if not text:
        return 0
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    latin_words = re.findall(r"[A-Za-z]+", text)
    digits = re.findall(r"\d+", text)
    # For Chinese speech transcripts, counting Chinese characters is a practical proxy.
    return len(chinese_chars) + len(latin_words) + len(digits)


def _extract_voice_features(
    responses: List[AssessmentResponse],
    questions: Dict[int, Question],
) -> Dict[str, Any]:
    total = 0
    valid = 0
    word_counts: List[int] = []
    durations: List[float] = []
    pauses: List[float] = []
    has_audio_file = 0

    for resp in responses:
        q = questions.get(resp.question_id)
        if q is None:
            continue
        q_type = q.q_type.value if hasattr(q.q_type, "value") else str(q.q_type)
        answer_data = _safe_dict(resp.answer_data)
        answer_type = str(answer_data.get("answer_type", "")).lower()
        if q_type != "voice" and answer_type != "voice":
            continue

        total += 1
        text = (resp.answer_text or "").strip()
        words = _count_words(text)
        if words > 0:
            valid += 1
            word_counts.append(words)

        # Collect optional duration fields from multiple possible payload names.
        duration_sec = _to_float(answer_data.get("duration_sec"), -1.0)
        if duration_sec < 0:
            duration_ms = _to_float(answer_data.get("duration_ms"), -1.0)
            if duration_ms >= 0:
                duration_sec = duration_ms / 1000.0
        if duration_sec >= 0:
            durations.append(duration_sec)

        pause_count = _to_float(answer_data.get("pause_count"), 0.0)
        pauses.append(max(0.0, pause_count))

        if any(answer_data.get(k) for k in ("voice_file", "filePath", "audio_path", "audio_url")):
            has_audio_file += 1

    if total == 0:
        return {
            "available": False,
            "sample_count": 0,
            "quality": 0.55,  # neutral when modality not collected
            "word_richness": 0.5,
            "avg_words": 0.0,
            "avg_duration_sec": 0.0,
            "pause_density": 0.0,
            "audio_file_ratio": 0.0,
        }

    coverage = valid / total
    avg_words = float(np.mean(word_counts)) if word_counts else 0.0
    avg_duration_sec = float(np.mean(durations)) if durations else 0.0
    pause_density = float(np.mean(pauses)) / max(avg_duration_sec, 8.0) if pauses else 0.0
    audio_file_ratio = has_audio_file / total

    word_richness = _clamp(avg_words / 18.0, 0.0, 1.0)
    duration_score = _clamp(avg_duration_sec / 25.0, 0.0, 1.0) if durations else 0.5
    pause_score = _clamp(1.0 - pause_density * 1.8, 0.2, 1.0)
    quality = (
        coverage * 0.45
        + word_richness * 0.25
        + duration_score * 0.15
        + pause_score * 0.10
        + audio_file_ratio * 0.05
    )
    quality = float(_clamp(quality, 0.0, 1.0))

    return {
        "available": True,
        "sample_count": total,
        "quality": round(quality, 4),
        "word_richness": round(word_richness, 4),
        "avg_words": round(avg_words, 2),
        "avg_duration_sec": round(avg_duration_sec, 2),
        "pause_density": round(pause_density, 4),
        "audio_file_ratio": round(audio_file_ratio, 4),
    }


def _extract_drawing_features(
    responses: List[AssessmentResponse],
    questions: Dict[int, Question],
) -> Dict[str, Any]:
    total = 0
    valid = 0
    stroke_counts: List[float] = []
    point_counts: List[float] = []
    has_image = 0

    for resp in responses:
        q = questions.get(resp.question_id)
        if q is None:
            continue
        q_type = q.q_type.value if hasattr(q.q_type, "value") else str(q.q_type)
        answer_data = _safe_dict(resp.answer_data)
        answer_type = str(answer_data.get("answer_type", "")).lower()
        if q_type != "drawing" and answer_type != "drawing":
            continue

        total += 1
        if answer_data.get("skipped"):
            continue

        strokes_payload = _safe_dict(answer_data.get("strokes"))
        stroke_count = _to_float(strokes_payload.get("stroke_count"), -1.0)
        if stroke_count < 0:
            # Fallback for raw list shape: {"strokes": [...]}
            raw_strokes = strokes_payload.get("strokes")
            if isinstance(raw_strokes, list):
                stroke_count = float(len(raw_strokes))
        point_count = _to_float(strokes_payload.get("total_points"), 0.0)

        if stroke_count > 0:
            valid += 1
            stroke_counts.append(stroke_count)
            point_counts.append(point_count)

        if answer_data.get("image_data"):
            has_image += 1

    if total == 0:
        return {
            "available": False,
            "sample_count": 0,
            "quality": 0.55,  # neutral when modality not collected
            "structure_score": 0.5,
            "avg_strokes": 0.0,
            "avg_points": 0.0,
            "image_ratio": 0.0,
        }

    coverage = valid / total
    avg_strokes = float(np.mean(stroke_counts)) if stroke_counts else 0.0
    avg_points = float(np.mean(point_counts)) if point_counts else 0.0
    image_ratio = has_image / total

    stroke_score = _clamp((avg_strokes - 3.0) / 20.0, 0.0, 1.0) if stroke_counts else 0.3
    point_score = _clamp((avg_points - 50.0) / 350.0, 0.0, 1.0) if point_counts else 0.3
    structure_score = _clamp(stroke_score * 0.55 + point_score * 0.45, 0.0, 1.0)
    quality = (
        coverage * 0.45
        + structure_score * 0.35
        + image_ratio * 0.20
    )
    quality = float(_clamp(quality, 0.0, 1.0))

    return {
        "available": True,
        "sample_count": total,
        "quality": round(quality, 4),
        "structure_score": round(structure_score, 4),
        "avg_strokes": round(avg_strokes, 2),
        "avg_points": round(avg_points, 2),
        "image_ratio": round(image_ratio, 4),
    }


def _extract_behavior_features(responses: List[AssessmentResponse]) -> Dict[str, Any]:
    reaction_times = [
        float(r.reaction_time_ms)
        for r in responses
        if r.reaction_time_ms is not None and r.reaction_time_ms > 0
    ]

    if not reaction_times:
        return {
            "available": False,
            "sample_count": 0,
            "quality": 0.55,  # neutral when behavior telemetry absent
            "avg_reaction_ms": 0.0,
            "std_reaction_ms": 0.0,
            "slow_ratio": 0.0,
            "fast_ratio": 0.0,
            "stability_score": 0.5,
        }

    avg_rt = float(np.mean(reaction_times))
    std_rt = float(np.std(reaction_times))
    slow_ratio = sum(1 for rt in reaction_times if rt > 45000) / len(reaction_times)
    fast_ratio = sum(1 for rt in reaction_times if rt < 500) / len(reaction_times)

    stability_score = _clamp(1.0 - std_rt / 30000.0, 0.0, 1.0)
    speed_score = _clamp(1.0 - abs(avg_rt - 6500.0) / 12000.0, 0.0, 1.0)
    quality = (
        stability_score * 0.45
        + speed_score * 0.30
        + (1.0 - slow_ratio) * 0.15
        + (1.0 - fast_ratio) * 0.10
    )
    quality = float(_clamp(quality, 0.0, 1.0))

    return {
        "available": True,
        "sample_count": len(reaction_times),
        "quality": round(quality, 4),
        "avg_reaction_ms": round(avg_rt, 1),
        "std_reaction_ms": round(std_rt, 1),
        "slow_ratio": round(slow_ratio, 4),
        "fast_ratio": round(fast_ratio, 4),
        "stability_score": round(stability_score, 4),
    }


def _extract_questionnaire_features(
    responses: List[AssessmentResponse],
    questions: Dict[int, Question],
) -> Dict[str, Any]:
    total = 0
    scorable = 0
    scores: List[float] = []
    choice_correct = 0
    choice_total = 0
    scale_values: List[float] = []

    for resp in responses:
        q = questions.get(resp.question_id)
        if q is None:
            continue
        q_type = q.q_type.value if hasattr(q.q_type, "value") else str(q.q_type)
        if q_type in ("voice", "drawing"):
            continue

        total += 1
        if resp.score is not None:
            scorable += 1
            scores.append(float(resp.score))
        elif resp.is_correct is not None:
            scorable += 1
            scores.append(1.0 if bool(resp.is_correct) else 0.0)

        if q_type == "choice":
            choice_total += 1
            if bool(resp.is_correct):
                choice_correct += 1
        if q_type == "scale" and resp.answer_text is not None:
            scale_raw = _to_float(resp.answer_text, 5.0)
            scale_values.append(_clamp(scale_raw / 10.0, 0.0, 1.0))

    if total == 0:
        return {
            "available": False,
            "sample_count": 0,
            "quality": 0.55,  # neutral
            "choice_accuracy": 0.5,
            "avg_score": 0.5,
            "scale_mean": 0.5,
            "coverage": 0.0,
        }

    coverage = scorable / total
    choice_accuracy = (choice_correct / choice_total) if choice_total else 0.5
    avg_score = float(np.mean(scores)) if scores else 0.5
    scale_mean = float(np.mean(scale_values)) if scale_values else 0.5

    quality = (
        coverage * 0.55
        + avg_score * 0.35
        + _clamp(choice_accuracy, 0.0, 1.0) * 0.10
    )
    quality = float(_clamp(quality, 0.0, 1.0))

    return {
        "available": True,
        "sample_count": total,
        "quality": round(quality, 4),
        "choice_accuracy": round(choice_accuracy, 4),
        "avg_score": round(avg_score, 4),
        "scale_mean": round(scale_mean, 4),
        "coverage": round(coverage, 4),
    }


def _extract_multimodal_features(
    responses: List[AssessmentResponse],
    questions: Dict[int, Question],
) -> Dict[str, Dict[str, Any]]:
    return {
        "questionnaire": _extract_questionnaire_features(responses, questions),
        "voice": _extract_voice_features(responses, questions),
        "drawing": _extract_drawing_features(responses, questions),
        "behavior": _extract_behavior_features(responses),
    }


def _calculate_domain_scores(
    responses: List[AssessmentResponse],
    questions: Dict[int, Question],
    modality_features: Dict[str, Dict[str, Any]],
) -> Dict[str, float]:
    """
    Compute six-domain scores (0~10) using:
    - direct task score aggregation
    - modality-derived adjustments
    - data quality penalties for missing/low-quality modalities
    """
    domain_values: Dict[str, List[float]] = {d.value: [] for d in QuestionDomain}

    for resp in responses:
        q = questions.get(resp.question_id)
        if q is None:
            continue
        domain_key = q.domain.value if hasattr(q.domain, "value") else str(q.domain)
        if resp.score is not None:
            domain_values[domain_key].append(float(resp.score))
        elif resp.is_correct is not None:
            domain_values[domain_key].append(1.0 if bool(resp.is_correct) else 0.0)

    questionnaire = modality_features["questionnaire"]
    voice = modality_features["voice"]
    drawing = modality_features["drawing"]
    behavior = modality_features["behavior"]

    domain_scores: Dict[str, float] = {}
    for domain in QuestionDomain:
        key = domain.value
        if domain_values[key]:
            base = float(np.mean(domain_values[key])) * 10.0
        else:
            # Neutral baseline when no direct responses for the domain.
            base = 6.2

        # Cross-modality enrichment.
        if key == "memory":
            base += (voice["word_richness"] - 0.5) * 2.0
            base += (questionnaire["choice_accuracy"] - 0.5) * 1.2
        elif key == "language":
            base += (voice["word_richness"] - 0.5) * 2.5
            base += (questionnaire["avg_score"] - 0.5) * 1.0
        elif key == "attention":
            attentiveness = 1.0 - (behavior["slow_ratio"] + behavior["fast_ratio"])
            base += (attentiveness - 0.5) * 2.0
            base += (behavior["stability_score"] - 0.5) * 1.1
        elif key == "visuospatial":
            base += (drawing["structure_score"] - 0.5) * 2.7
        elif key == "executive":
            base += (drawing["structure_score"] - 0.5) * 1.3
            base += (behavior["stability_score"] - 0.5) * 1.2
        elif key == "orientation":
            base += (questionnaire["choice_accuracy"] - 0.5) * 1.6
            base += (questionnaire["coverage"] - 0.5) * 0.6

        # Low-quality modality penalties.
        if key in ("memory", "language") and voice["quality"] < 0.45:
            base -= (0.45 - voice["quality"]) * 4.5
        if key in ("visuospatial", "executive") and drawing["quality"] < 0.45:
            base -= (0.45 - drawing["quality"]) * 4.0
        if key in ("attention", "executive") and behavior["quality"] < 0.45:
            base -= (0.45 - behavior["quality"]) * 3.8

        # Controlled noise for realism.
        base += float(np.random.normal(0, 0.22))
        domain_scores[key] = round(_clamp(base, 0.0, 10.0), 2)

    return domain_scores


def _calculate_mmse_score(domain_scores: Dict[str, float]) -> float:
    total = 0.0
    for domain, points in DOMAIN_MAX_MMSE_POINTS.items():
        if points <= 0:
            continue
        total += (domain_scores.get(domain, 5.0) / 10.0) * points
    return round(_clamp(total, 0.0, 30.0), 1)


def _score_by_ratio(ratio: float, max_points: int) -> float:
    return float(int(round(_clamp(ratio, 0.0, 1.0) * max_points)))


def _weighted_ratio(*parts: tuple[float, float]) -> float:
    if not parts:
        return 0.5
    denominator = sum(weight for _, weight in parts) or 1.0
    numerator = sum(_clamp(value, 0.0, 1.0) * weight for value, weight in parts)
    return _clamp(numerator / denominator, 0.0, 1.0)


def _domain_ratio(domain_scores: Dict[str, float], key: str, default: float = 0.5) -> float:
    return _clamp(_to_float(domain_scores.get(key), default * 10.0) / 10.0, 0.0, 1.0)


def _build_standardized_scale_scores(
    domain_scores: Dict[str, float],
    modality_features: Dict[str, Dict[str, Any]],
    education_years: Optional[int],
) -> Dict[str, Any]:
    """
    Build standardized MMSE(11 subitems) and MoCA(8 subitems) structures.
    Scoring is calibrated from multimodal domain evidence and clamped to each
    scale's official point caps.
    """
    questionnaire = modality_features["questionnaire"]
    voice = modality_features["voice"]
    drawing = modality_features["drawing"]
    behavior = modality_features["behavior"]

    orientation = _domain_ratio(domain_scores, "orientation")
    memory = _domain_ratio(domain_scores, "memory")
    language = _domain_ratio(domain_scores, "language")
    attention = _domain_ratio(domain_scores, "attention")
    visuospatial = _domain_ratio(domain_scores, "visuospatial")
    executive = _domain_ratio(domain_scores, "executive")

    choice_accuracy = _clamp(_to_float(questionnaire.get("choice_accuracy"), 0.5), 0.0, 1.0)
    questionnaire_avg = _clamp(_to_float(questionnaire.get("avg_score"), 0.5), 0.0, 1.0)
    questionnaire_coverage = _clamp(_to_float(questionnaire.get("coverage"), 0.5), 0.0, 1.0)
    word_richness = _clamp(_to_float(voice.get("word_richness"), 0.5), 0.0, 1.0)
    drawing_structure = _clamp(_to_float(drawing.get("structure_score"), 0.5), 0.0, 1.0)
    behavior_stability = _clamp(_to_float(behavior.get("stability_score"), 0.5), 0.0, 1.0)

    mmse_subscores = {
        "orientation_time": _score_by_ratio(
            _weighted_ratio((orientation, 0.85), (behavior_stability, 0.15)),
            MMSE_SUBITEM_MAX_POINTS["orientation_time"],
        ),
        "orientation_place": _score_by_ratio(
            _weighted_ratio((orientation, 0.8), (questionnaire_coverage, 0.2)),
            MMSE_SUBITEM_MAX_POINTS["orientation_place"],
        ),
        "registration": _score_by_ratio(
            _weighted_ratio((memory, 0.65), (questionnaire_avg, 0.2), (word_richness, 0.15)),
            MMSE_SUBITEM_MAX_POINTS["registration"],
        ),
        "attention_calculation": _score_by_ratio(
            _weighted_ratio((attention, 0.7), (behavior_stability, 0.3)),
            MMSE_SUBITEM_MAX_POINTS["attention_calculation"],
        ),
        "delayed_recall": _score_by_ratio(
            _weighted_ratio((memory, 0.8), (word_richness, 0.2)),
            MMSE_SUBITEM_MAX_POINTS["delayed_recall"],
        ),
        "naming": _score_by_ratio(
            _weighted_ratio((language, 0.7), (choice_accuracy, 0.3)),
            MMSE_SUBITEM_MAX_POINTS["naming"],
        ),
        "repetition": _score_by_ratio(
            _weighted_ratio((language, 0.6), (word_richness, 0.4)),
            MMSE_SUBITEM_MAX_POINTS["repetition"],
        ),
        "three_step_command": _score_by_ratio(
            _weighted_ratio((language, 0.65), (questionnaire_avg, 0.35)),
            MMSE_SUBITEM_MAX_POINTS["three_step_command"],
        ),
        "reading": _score_by_ratio(
            _weighted_ratio((language, 0.55), (questionnaire_coverage, 0.45)),
            MMSE_SUBITEM_MAX_POINTS["reading"],
        ),
        "writing": _score_by_ratio(
            _weighted_ratio((language, 0.55), (questionnaire_coverage, 0.45)),
            MMSE_SUBITEM_MAX_POINTS["writing"],
        ),
        "figure_copy": _score_by_ratio(
            _weighted_ratio((visuospatial, 0.6), (drawing_structure, 0.4)),
            MMSE_SUBITEM_MAX_POINTS["figure_copy"],
        ),
    }
    mmse_score = round(
        _clamp(sum(mmse_subscores.values()), 0.0, float(sum(MMSE_SUBITEM_MAX_POINTS.values()))),
        1,
    )

    moca_subscores = {
        "trail_making": _score_by_ratio(
            _weighted_ratio((executive, 0.5), (attention, 0.3), (behavior_stability, 0.2)),
            MOCA_SUBITEM_MAX_POINTS["trail_making"],
        ),
        "visuospatial": _score_by_ratio(
            _weighted_ratio((visuospatial, 0.65), (drawing_structure, 0.35)),
            MOCA_SUBITEM_MAX_POINTS["visuospatial"],
        ),
        "naming": _score_by_ratio(
            _weighted_ratio((language, 0.7), (choice_accuracy, 0.3)),
            MOCA_SUBITEM_MAX_POINTS["naming"],
        ),
        "attention": _score_by_ratio(
            _weighted_ratio((attention, 0.7), (behavior_stability, 0.3)),
            MOCA_SUBITEM_MAX_POINTS["attention"],
        ),
        "language": _score_by_ratio(
            _weighted_ratio((language, 0.7), (word_richness, 0.3)),
            MOCA_SUBITEM_MAX_POINTS["language"],
        ),
        "abstraction": _score_by_ratio(
            _weighted_ratio((executive, 0.6), (language, 0.2), (attention, 0.2)),
            MOCA_SUBITEM_MAX_POINTS["abstraction"],
        ),
        "delayed_recall": _score_by_ratio(
            _weighted_ratio((memory, 0.8), (word_richness, 0.2)),
            MOCA_SUBITEM_MAX_POINTS["delayed_recall"],
        ),
        "orientation": _score_by_ratio(
            _weighted_ratio((orientation, 0.85), (questionnaire_coverage, 0.15)),
            MOCA_SUBITEM_MAX_POINTS["orientation"],
        ),
    }
    moca_score = round(
        _clamp(sum(moca_subscores.values()), 0.0, float(sum(MOCA_SUBITEM_MAX_POINTS.values()))),
        1,
    )

    edu_years = education_years if education_years is not None else 999
    correction_applied = edu_years <= MOCA_EDUCATION_CORRECTION_THRESHOLD
    correction_points = MOCA_EDUCATION_CORRECTION_POINTS if correction_applied else 0.0
    moca_score_corrected = round(_clamp(moca_score + correction_points, 0.0, 30.0), 1)

    return {
        "mmse_subscores": mmse_subscores,
        "mmse_score": mmse_score,
        "moca_subscores": moca_subscores,
        "moca_score": moca_score,
        "moca_score_corrected": moca_score_corrected,
        "education_correction_applied": correction_applied,
        "education_correction_points": correction_points,
    }


def _build_clinical_report(
    risk_level: RiskLevel,
    domain_scores: Dict[str, float],
    scale_payload: Dict[str, Any],
    confidence: float,
) -> Dict[str, Any]:
    mmse_score = _to_float(scale_payload.get("mmse_score"), 0.0)
    moca_raw = _to_float(scale_payload.get("moca_score"), 0.0)
    moca_corrected = _to_float(scale_payload.get("moca_score_corrected"), moca_raw)
    correction_applied = bool(scale_payload.get("education_correction_applied"))
    correction_points = _to_float(scale_payload.get("education_correction_points"), 0.0)

    if mmse_score >= 24:
        mmse_band = "MMSE在常模范围内（>=24）"
    elif mmse_score >= 18:
        mmse_band = "MMSE提示轻中度认知下降（18-23）"
    else:
        mmse_band = "MMSE提示明显认知受损（<18）"

    if moca_corrected >= 26:
        moca_band = "MoCA在常模范围内（>=26）"
    elif moca_corrected >= 18:
        moca_band = "MoCA提示存在认知下降风险（18-25）"
    else:
        moca_band = "MoCA提示中高风险认知受损（<18）"

    weak_domains = sorted(domain_scores.items(), key=lambda item: item[1])[:3]
    weak_domain_items = [
        {
            "domain": domain,
            "score": round(_to_float(score), 2),
            "label": DOMAIN_LABELS.get(domain, domain),
        }
        for domain, score in weak_domains
    ]
    weak_domain_labels = "、".join(item["label"] for item in weak_domain_items)

    risk_summary_map = {
        RiskLevel.normal: "整体认知状态目前处于低风险区间。",
        RiskLevel.mild_risk: "存在轻度认知风险，建议尽快门诊复评。",
        RiskLevel.high_risk: "存在较高认知风险，建议尽快转诊专科进一步评估。",
    }

    return {
        "risk_summary": risk_summary_map.get(risk_level, risk_summary_map[RiskLevel.mild_risk]),
        "scale_interpretation": {
            "mmse": mmse_band,
            "moca": moca_band,
            "education_correction_note": (
                f"已按教育年限规则应用 MoCA +{int(correction_points)} 校正。"
                if correction_applied
                else "未触发教育年限校正。"
            ),
        },
        "score_snapshot": {
            "mmse_score": mmse_score,
            "moca_score_raw": moca_raw,
            "moca_score_corrected": moca_corrected,
            "confidence_percent": round(confidence * 100, 1),
        },
        "weak_domains": weak_domain_items,
        "clinical_note": f"当前薄弱认知域主要集中在：{weak_domain_labels}。",
    }


def _collect_rag_knowledge_ids(
    db,
    *,
    queries: List[str],
    kb_type: Optional[KnowledgeType] = None,
    top_k_per_query: int = 2,
) -> List[int]:
    """
    Retrieve knowledge ids from FAISS RAG index for explainable traceability.
    Best-effort: any retrieval/runtime error falls back to empty ids.
    """
    out: List[int] = []
    seen = set()
    try:
        for query in queries:
            q = (query or "").strip()
            if not q:
                continue
            hits = rag_service.search(
                db,
                query=q,
                top_k=max(1, top_k_per_query),
                kb_type=kb_type,
                tag=None,
            )
            for item, _score in hits:
                if item.id in seen:
                    continue
                seen.add(item.id)
                out.append(item.id)
    except Exception:
        return []
    return out


def _build_rag_recommendation_items(
    db,
    *,
    risk_level: RiskLevel,
    weak_labels: str,
    quality_issues: List[str],
) -> List[Dict[str, Any]]:
    if risk_level == RiskLevel.normal:
        actions = [
            f"保持规律作息、适度社交与运动，重点训练：{weak_labels}。",
            "建议6个月后完成一次复评。",
        ]
    elif risk_level == RiskLevel.mild_risk:
        actions = [
            f"围绕薄弱域（{weak_labels}）开展认知训练，持续1-3个月。",
            "建议社区随访并预约门诊复评。",
        ]
    else:
        actions = [
            f"针对薄弱域（{weak_labels}）立即启动家属协同干预。",
            "建议尽快转诊神经内科/记忆门诊进一步评估。",
        ]

    if quality_issues:
        actions.append(
            f"数据质量提示：{','.join(quality_issues)} 模态质量偏低，建议下次在安静环境重测并补全语音/绘图任务。"
        )

    items: List[Dict[str, Any]] = []
    for action in actions:
        ids = _collect_rag_knowledge_ids(
            db,
            queries=[action, weak_labels],
            kb_type=None,
            top_k_per_query=2,
        )
        items.append(
            {
                "action": action,
                "knowledge_ids": ids,
            }
        )
    return items


def _generate_probabilities(
    domain_scores: Dict[str, float],
    mmse_score: float,
    modality_features: Dict[str, Dict[str, Any]],
) -> Dict[str, float]:
    """
    Produce NC/MCI/AD probabilities with quality-aware smoothing.
    """
    weak_ratio = sum(1 for v in domain_scores.values() if v < 5.0) / 6.0
    severe_ratio = sum(1 for v in domain_scores.values() if v < 3.8) / 6.0
    overall_domain = float(np.mean(list(domain_scores.values()))) / 10.0

    impairment_by_domain = _clamp(1.0 - overall_domain, 0.0, 1.0)
    impairment_by_mmse = _clamp((24.0 - mmse_score) / 14.0, 0.0, 1.0)
    impairment_index = (
        impairment_by_domain * 0.45
        + impairment_by_mmse * 0.35
        + weak_ratio * 0.12
        + severe_ratio * 0.08
    )

    ad_prob = _clamp(0.04 + 0.92 * (impairment_index ** 1.85), 0.01, 0.96)
    mci_prob = _clamp(
        0.10 + 0.70 * impairment_index * (1.0 - impairment_index) + 0.14 * weak_ratio,
        0.02,
        0.90,
    )
    nc_prob = max(0.01, 1.0 - ad_prob - mci_prob)

    raw = np.array([nc_prob, mci_prob, ad_prob], dtype=float)
    raw = raw / raw.sum()

    quality_mean = float(np.mean([m["quality"] for m in modality_features.values()]))
    # Low quality -> distribution should be less extreme (closer to uniform).
    flatten_weight = _clamp((0.62 - quality_mean) * 1.2, 0.0, 0.45)
    raw = raw * (1.0 - flatten_weight) + np.array([1 / 3, 1 / 3, 1 / 3]) * flatten_weight
    raw = raw / raw.sum()

    return {
        "nc": round(float(raw[0]), 4),
        "mci": round(float(raw[1]), 4),
        "ad": round(float(raw[2]), 4),
    }


def _calculate_confidence(
    probabilities: Dict[str, float],
    modality_features: Dict[str, Dict[str, Any]],
    response_count: int,
) -> float:
    probs = sorted([probabilities["nc"], probabilities["mci"], probabilities["ad"]], reverse=True)
    margin = probs[0] - probs[1]
    quality_mean = float(np.mean([m["quality"] for m in modality_features.values()]))
    available_ratio = (
        sum(1 for m in modality_features.values() if m["available"]) / len(modality_features)
    )
    coverage_score = _clamp(response_count / 15.0, 0.0, 1.0)

    base = 0.42 + margin * 0.45 + available_ratio * 0.08 + coverage_score * 0.12
    confidence = base * (0.72 + quality_mean * 0.48)
    return round(_clamp(confidence, 0.35, 0.97), 4)


def _normalize_probabilities(probs: Dict[str, float]) -> Dict[str, float]:
    nc = _to_float(probs.get("nc"), 0.0)
    mci = _to_float(probs.get("mci"), 0.0)
    ad = _to_float(probs.get("ad"), 0.0)
    total = nc + mci + ad
    if total <= 0:
        return {"nc": 0.3333, "mci": 0.3333, "ad": 0.3334}
    return {
        "nc": round(nc / total, 4),
        "mci": round(mci / total, 4),
        "ad": round(ad / total, 4),
    }


def _blend_probabilities(
    rule_probs: Dict[str, float],
    deep_probs: Dict[str, float],
    alpha: float,
) -> Dict[str, float]:
    alpha = _clamp(alpha, 0.0, 1.0)
    mixed = {
        key: _to_float(rule_probs.get(key), 0.0) * (1.0 - alpha)
        + _to_float(deep_probs.get(key), 0.0) * alpha
        for key in ("nc", "mci", "ad")
    }
    return _normalize_probabilities(mixed)


def _blend_domain_scores(
    rule_scores: Dict[str, float],
    deep_scores: Dict[str, float],
    alpha: float,
) -> Dict[str, float]:
    alpha = _clamp(alpha, 0.0, 1.0)
    blended: Dict[str, float] = {}
    for domain in DOMAIN_ORDER:
        rule_val = _to_float(rule_scores.get(domain), 5.0)
        deep_val = _to_float(deep_scores.get(domain), rule_val)
        score = rule_val * (1.0 - alpha) + deep_val * alpha
        blended[domain] = round(_clamp(score, 0.0, 10.0), 2)
    return blended


def _assign_risk_level(
    probs: Dict[str, float],
    mmse_score: float,
    confidence: float,
) -> RiskLevel:
    if probs["ad"] >= 0.55 or mmse_score < 18.0:
        risk = RiskLevel.high_risk
    elif probs["ad"] >= 0.35 or probs["mci"] >= 0.45 or mmse_score < 24.0:
        risk = RiskLevel.mild_risk
    else:
        risk = RiskLevel.normal

    # Low confidence safeguards.
    if confidence < 0.45 and risk == RiskLevel.normal and (probs["mci"] + probs["ad"]) > 0.45:
        risk = RiskLevel.mild_risk

    return risk


def _generate_explainability(
    domain_scores: Dict[str, float],
    modality_features: Dict[str, Dict[str, Any]],
    confidence: float,
    model_name: str = "rule_engine",
    strategy: str = "rule",
    deep_payload: Optional[Dict[str, Any]] = None,
    scale_payload: Optional[Dict[str, Any]] = None,
    clinical_report: Optional[Dict[str, Any]] = None,
    recommendation_items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build SHAP-like payload:
    - feature_shap: signed contributions
    - modality_contributions: percentages summing to ~100
    - modality_quality + confidence
    """
    feature_shap: Dict[str, float] = {}
    for domain, score in domain_scores.items():
        # Lower score => more negative impact on cognitive risk.
        feature_shap[f"{domain}_score"] = round(((score - 5.0) / 5.0) * 0.72, 4)

    voice = modality_features["voice"]
    drawing = modality_features["drawing"]
    behavior = modality_features["behavior"]
    questionnaire = modality_features["questionnaire"]

    feature_shap["voice_word_richness"] = round((voice["word_richness"] - 0.5) * 0.55, 4)
    feature_shap["drawing_structure_score"] = round((drawing["structure_score"] - 0.5) * 0.50, 4)
    feature_shap["behavior_stability"] = round((behavior["stability_score"] - 0.5) * 0.48, 4)
    feature_shap["questionnaire_accuracy"] = round((questionnaire["choice_accuracy"] - 0.5) * 0.52, 4)

    # Estimate modality contribution by impairment signal.
    modality_impairment = {
        "questionnaire": _clamp(1.0 - questionnaire["avg_score"], 0.05, 1.0),
        "voice": _clamp(1.0 - voice["quality"] + (1.0 - voice["word_richness"]) * 0.4, 0.05, 1.0),
        "drawing": _clamp(1.0 - drawing["quality"] + (1.0 - drawing["structure_score"]) * 0.4, 0.05, 1.0),
        "behavior": _clamp(1.0 - behavior["quality"] + behavior["slow_ratio"] * 0.5, 0.05, 1.0),
    }
    total_imp = sum(modality_impairment.values())
    modality_contrib = {
        key: round(value / total_imp * 100.0, 2)
        for key, value in modality_impairment.items()
    }
    if deep_payload and deep_payload.get("modality_contributions"):
        modality_contrib = {
            key: round(_to_float(value), 2)
            for key, value in deep_payload["modality_contributions"].items()
        }

    quality_map = {
        key: round(float(value["quality"]), 4)
        for key, value in modality_features.items()
    }
    quality_flag = "limited" if min(quality_map.values()) < 0.6 else "good"

    # Top factors for compact display.
    top_factors = sorted(feature_shap.items(), key=lambda x: abs(x[1]), reverse=True)[:8]

    payload = {
        "feature_shap": feature_shap,
        "top_factors": [{"feature": k, "impact": v} for k, v in top_factors],
        "modality_contributions": modality_contrib,
        "modality_quality": quality_map,
        "model_confidence": confidence,
        "data_quality_flag": quality_flag,
        "model_name": model_name,
        "model_strategy": strategy,
    }
    if scale_payload:
        payload["mmse_subscores"] = scale_payload.get("mmse_subscores")
        payload["moca_subscores"] = scale_payload.get("moca_subscores")
        payload["moca_score"] = scale_payload.get("moca_score")
        payload["moca_score_corrected"] = scale_payload.get("moca_score_corrected")
        payload["education_correction_applied"] = scale_payload.get("education_correction_applied")
        payload["education_correction_points"] = scale_payload.get("education_correction_points")
    if clinical_report is not None:
        payload["clinical_report"] = clinical_report
    if recommendation_items is not None:
        payload["recommendation_items"] = recommendation_items
    if deep_payload:
        if deep_payload.get("attention_matrix") is not None:
            payload["attention_matrix"] = deep_payload["attention_matrix"]
        if deep_payload.get("engine_info") is not None:
            payload["engine_info"] = deep_payload["engine_info"]
    return payload


def _generate_recommendation(
    risk_level: RiskLevel,
    domain_scores: Dict[str, float],
    confidence: float,
    modality_features: Dict[str, Dict[str, Any]],
) -> str:
    weak_domains = sorted(domain_scores.items(), key=lambda x: x[1])[:3]
    weak_labels = "、".join(DOMAIN_LABELS.get(k, k) for k, _ in weak_domains)

    quality_issues = [k for k, v in modality_features.items() if v["quality"] < 0.6]
    quality_note = ""
    if quality_issues:
        quality_note = (
            f" 数据质量提示：{','.join(quality_issues)} 模态质量偏低，"
            "建议下次在安静环境重测并完成语音/绘图任务。"
        )

    if risk_level == RiskLevel.normal:
        return (
            f"当前评估总体处于正常范围，建议维持规律作息、社交与运动。"
            f"可重点训练：{weak_labels}。建议6个月后复查。"
            f"{quality_note}"
        )

    if risk_level == RiskLevel.mild_risk:
        return (
            f"检测到轻度认知风险，主要薄弱域为：{weak_labels}。"
            "建议1-3个月内开展认知训练与运动干预，并安排社区随访复评。"
            f"模型置信度：{round(confidence * 100)}%。{quality_note}"
        )

    return (
        f"检测到较高认知风险，薄弱域集中在：{weak_labels}。"
        "建议尽快前往神经内科/记忆门诊进行专业检查（如神经心理量表、影像学）。"
        "家属应加强用药与安全看护，并同步制定干预计划。"
        f"模型置信度：{round(confidence * 100)}%。{quality_note}"
    )


def analyze_session(session_id: int, db_url: str) -> Dict[str, Any]:
    """
    Analyze one assessment session and persist a multimodal result.
    """
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = LocalSession()

    try:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
        if session is None:
            raise ValueError(f"AssessmentSession {session_id} not found")

        responses = (
            db.query(AssessmentResponse)
            .filter(AssessmentResponse.session_id == session_id)
            .all()
        )
        if not responses:
            raise ValueError(f"Session {session_id} has no responses")

        question_ids = [r.question_id for r in responses]
        questions_list = db.query(Question).filter(Question.id.in_(question_ids)).all()
        questions = {q.id: q for q in questions_list}
        education_years = getattr(getattr(session, "user", None), "education_years", None)

        modality_features = _extract_multimodal_features(responses, questions)
        model_strategy = settings.AI_MODEL_STRATEGY

        # Rule engine baseline (always computed as stable fallback).
        rule_domain_scores = _calculate_domain_scores(responses, questions, modality_features)
        rule_scale_payload = _build_standardized_scale_scores(
            rule_domain_scores,
            modality_features,
            education_years,
        )
        rule_mmse_score = _to_float(rule_scale_payload["mmse_score"], 0.0)
        rule_probs = _generate_probabilities(rule_domain_scores, rule_mmse_score, modality_features)
        rule_confidence = _calculate_confidence(rule_probs, modality_features, len(responses))

        domain_scores = rule_domain_scores
        probs = rule_probs
        confidence = rule_confidence
        selected_model_name = "rule_engine_v2"
        deep_payload: Optional[Dict[str, Any]] = None

        if model_strategy in ("deep", "hybrid"):
            deep_service = get_deep_model_service()
            deep_result = deep_service.predict(modality_features)
            if deep_result is not None:
                deep_payload = deep_result
                deep_domain_scores = deep_result["domain_scores"]
                deep_probs = deep_result["probabilities"]
                deep_confidence = _to_float(deep_result.get("confidence"), rule_confidence)

                if model_strategy == "deep":
                    domain_scores = deep_domain_scores
                    probs = deep_probs
                    confidence = round(_clamp(deep_confidence, 0.35, 0.98), 4)
                    selected_model_name = "deep_cross_modal_fusion"
                else:
                    alpha = settings.DEEP_MODEL_BLEND_ALPHA
                    domain_scores = _blend_domain_scores(rule_domain_scores, deep_domain_scores, alpha)
                    probs = _blend_probabilities(rule_probs, deep_probs, alpha)
                    confidence = round(
                        _clamp(rule_confidence * (1.0 - alpha) + deep_confidence * alpha, 0.35, 0.98),
                        4,
                    )
                    selected_model_name = "hybrid_rule_deep_fusion"
            else:
                deep_payload = {
                    "engine_info": {
                        "engine": "deep_cross_modal",
                        "available": False,
                        "reason": deep_service.reason,
                    }
                }
                if model_strategy == "deep":
                    selected_model_name = "rule_engine_v2_fallback_deep_unavailable"

        scale_payload = _build_standardized_scale_scores(domain_scores, modality_features, education_years)
        mmse_score = _to_float(scale_payload["mmse_score"], 0.0)
        risk_level = _assign_risk_level(probs, mmse_score, confidence)
        clinical_report = _build_clinical_report(
            risk_level=risk_level,
            domain_scores=domain_scores,
            scale_payload=scale_payload,
            confidence=confidence,
        )
        weak_domains = sorted(domain_scores.items(), key=lambda x: x[1])[:3]
        weak_labels = "、".join(DOMAIN_LABELS.get(k, k) for k, _ in weak_domains)
        quality_issues = [k for k, v in modality_features.items() if v["quality"] < 0.6]

        clinical_report["knowledge_ids"] = _collect_rag_knowledge_ids(
            db,
            queries=[
                clinical_report.get("risk_summary", ""),
                clinical_report.get("clinical_note", ""),
                clinical_report.get("scale_interpretation", {}).get("mmse", ""),
                clinical_report.get("scale_interpretation", {}).get("moca", ""),
                clinical_report.get("scale_interpretation", {}).get("education_correction_note", ""),
            ],
            kb_type=KnowledgeType.rule,
            top_k_per_query=2,
        )
        recommendation_items = _build_rag_recommendation_items(
            db,
            risk_level=risk_level,
            weak_labels=weak_labels,
            quality_issues=quality_issues,
        )
        clinical_report["recommended_actions"] = recommendation_items

        explainability = _generate_explainability(
            domain_scores,
            modality_features,
            confidence,
            model_name=selected_model_name,
            strategy=model_strategy,
            deep_payload=deep_payload,
            scale_payload=scale_payload,
            clinical_report=clinical_report,
            recommendation_items=recommendation_items,
        )
        recommendation = _generate_recommendation(
            risk_level=risk_level,
            domain_scores=domain_scores,
            confidence=confidence,
            modality_features=modality_features,
        )

        existing_result = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.session_id == session_id)
            .first()
        )

        if existing_result is not None:
            existing_result.risk_level = risk_level
            existing_result.nc_probability = probs["nc"]
            existing_result.mci_probability = probs["mci"]
            existing_result.ad_probability = probs["ad"]
            existing_result.mmse_score = mmse_score
            existing_result.domain_scores = domain_scores
            existing_result.shap_values = explainability
            existing_result.recommendation = recommendation
            db.commit()
            db.refresh(existing_result)
            result_id = existing_result.id
        else:
            result = AssessmentResult(
                session_id=session_id,
                risk_level=risk_level,
                nc_probability=probs["nc"],
                mci_probability=probs["mci"],
                ad_probability=probs["ad"],
                mmse_score=mmse_score,
                domain_scores=domain_scores,
                shap_values=explainability,
                recommendation=recommendation,
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            result_id = result.id

        create_assessment_notifications(
            db,
            session=session,
            risk_level=risk_level,
            mmse_score=mmse_score,
        )
        db.commit()

        return {
            "result_id": result_id,
            "session_id": session_id,
            "risk_level": risk_level.value,
            "nc_probability": probs["nc"],
            "mci_probability": probs["mci"],
            "ad_probability": probs["ad"],
            "mmse_score": mmse_score,
            "moca_score": scale_payload["moca_score"],
            "moca_score_corrected": scale_payload["moca_score_corrected"],
            "education_correction_applied": scale_payload["education_correction_applied"],
            "education_correction_points": scale_payload["education_correction_points"],
            "mmse_subscores": scale_payload["mmse_subscores"],
            "moca_subscores": scale_payload["moca_subscores"],
            "clinical_report": clinical_report,
            "recommendation_items": recommendation_items,
            "domain_scores": domain_scores,
            "model_confidence": confidence,
            "modality_quality": explainability["modality_quality"],
            "modality_contributions": explainability["modality_contributions"],
            "top_factors": explainability["top_factors"],
            "data_quality_flag": explainability["data_quality_flag"],
            "model_name": explainability.get("model_name"),
            "model_strategy": explainability.get("model_strategy"),
            "engine_info": explainability.get("engine_info"),
            "attention_matrix": explainability.get("attention_matrix"),
            "shap_values": explainability["feature_shap"],
            "recommendation": recommendation,
        }
    finally:
        db.close()
        engine.dispose()
