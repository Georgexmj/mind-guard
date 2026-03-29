"""
AI Analysis Service — Mock Implementation for MVP.

In production this module would:
  1. Load audio responses, run OpenAI Whisper for transcription
  2. Run BERT-based language understanding on transcribed text
  3. Evaluate drawing responses via CNN
  4. Feed multimodal features into a LightGBM ensemble
  5. Generate SHAP explanations
  6. Return structured risk assessment

For MVP we use rule-based heuristics + calibrated random noise to produce
realistic-looking outputs that exercise the full result pipeline.
"""

import random
from datetime import datetime
from typing import Dict, Any

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.assessment import (
    AssessmentSession,
    AssessmentResponse,
    AssessmentResult,
    Question,
    QuestionDomain,
    RiskLevel,
    SessionStatus,
)


# Domain weights for MMSE-like scoring
DOMAIN_WEIGHTS = {
    "memory": 3,
    "orientation": 2,
    "language": 2,
    "attention": 2,
    "visuospatial": 1,
    "executive": 2,
}

DOMAIN_MAX_MMSE_POINTS = {
    "memory": 6,
    "orientation": 10,
    "language": 8,
    "attention": 5,
    "visuospatial": 1,
    "executive": 0,  # not in original MMSE, added by us
}


def _calculate_domain_scores(responses: list, questions: Dict[int, Question]) -> Dict[str, float]:
    """
    Aggregate response scores by domain, returning a 0–10 scale score per domain.
    Adds Gaussian noise to simulate model variance.
    """
    domain_totals: Dict[str, list] = {d.value: [] for d in QuestionDomain}

    for resp in responses:
        q = questions.get(resp.question_id)
        if q is None:
            continue
        domain_key = q.domain.value
        if resp.score is not None:
            domain_totals[domain_key].append(resp.score)
        elif resp.is_correct is not None:
            domain_totals[domain_key].append(1.0 if resp.is_correct else 0.0)

    domain_scores: Dict[str, float] = {}
    for domain in QuestionDomain:
        scores = domain_totals[domain.value]
        if scores:
            raw_mean = float(np.mean(scores))
        else:
            # No questions answered for this domain: assign neutral score with noise
            raw_mean = random.uniform(0.55, 0.80)

        # Scale to 0–10 and add calibrated Gaussian noise
        scaled = raw_mean * 10.0
        noise = float(np.random.normal(0, 0.4))
        domain_scores[domain.value] = round(max(0.0, min(10.0, scaled + noise)), 2)

    return domain_scores


def _calculate_mmse_score(domain_scores: Dict[str, float]) -> float:
    """
    Compute a synthetic MMSE equivalent score (0–30) from domain scores.
    """
    total = 0.0
    for domain, points in DOMAIN_MAX_MMSE_POINTS.items():
        if points > 0:
            total += (domain_scores.get(domain, 5.0) / 10.0) * points
    # Clamp to 0–30
    return round(min(30.0, max(0.0, total)), 1)


def _generate_probabilities(domain_scores: Dict[str, float], mmse_score: float) -> Dict[str, float]:
    """
    Generate calibrated NC/MCI/AD probability distribution.
    Uses a logistic-style mapping from MMSE score + domain weakness signals.
    Probabilities sum to exactly 1.0.
    """
    # Identify cognitive weaknesses
    weak_domains = sum(1 for v in domain_scores.values() if v < 5.0)
    very_weak_domains = sum(1 for v in domain_scores.values() if v < 3.0)

    # Base logistic mapping: MMSE 24-30 → mostly NC, 18-23 → MCI, <18 → AD risk
    if mmse_score >= 26:
        base_nc = random.uniform(0.70, 0.88)
    elif mmse_score >= 22:
        base_nc = random.uniform(0.40, 0.65)
    elif mmse_score >= 18:
        base_nc = random.uniform(0.15, 0.35)
    else:
        base_nc = random.uniform(0.05, 0.20)

    # Adjust based on domain weakness
    nc_adj = base_nc - (weak_domains * 0.04) - (very_weak_domains * 0.06)
    nc_prob = max(0.02, min(0.95, nc_adj))

    remaining = 1.0 - nc_prob
    if mmse_score >= 22:
        mci_share = random.uniform(0.60, 0.80)
    elif mmse_score >= 18:
        mci_share = random.uniform(0.45, 0.65)
    else:
        mci_share = random.uniform(0.25, 0.45)

    mci_prob = remaining * mci_share
    ad_prob = remaining * (1.0 - mci_share)

    # Add small noise and renormalize
    raw = np.array([nc_prob, mci_prob, ad_prob]) + np.abs(np.random.normal(0, 0.015, 3))
    normalized = raw / raw.sum()

    return {
        "nc": round(float(normalized[0]), 4),
        "mci": round(float(normalized[1]), 4),
        "ad": round(float(normalized[2]), 4),
    }


def _assign_risk_level(probs: Dict[str, float], mmse_score: float) -> RiskLevel:
    """Assign clinical risk level based on probabilities and MMSE score."""
    if mmse_score >= 24 and probs["nc"] >= 0.60:
        return RiskLevel.normal
    elif mmse_score >= 18 or probs["mci"] >= 0.40:
        return RiskLevel.mild_risk
    else:
        return RiskLevel.high_risk


def _generate_shap_values(domain_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Generate mock SHAP feature importance values.
    In production these come from the LightGBM/SHAP library.
    """
    features = list(domain_scores.keys()) + [
        "reaction_time_avg", "answer_revision_count",
        "voice_pause_ratio", "drawing_accuracy_score",
    ]
    raw_shap = {f: float(np.random.normal(0, 0.15)) for f in features}

    # Domain scores with lower values should have larger negative SHAP impact
    for domain, score in domain_scores.items():
        deviation = (score - 5.0) / 10.0
        raw_shap[domain] = round(deviation * random.uniform(0.4, 0.8), 4)

    return {k: round(v, 4) for k, v in raw_shap.items()}


def _generate_recommendation(risk_level: RiskLevel, domain_scores: Dict[str, float]) -> str:
    """Generate a human-readable clinical recommendation."""
    weak = [d for d, s in domain_scores.items() if s < 5.0]
    weak_str = "、".join(weak) if weak else "无明显"

    if risk_level == RiskLevel.normal:
        return (
            "认知功能评估结果正常，建议保持健康生活方式，定期复查（建议每6个月进行一次评估）。"
            f"薄弱认知域：{weak_str}，可进行针对性训练。"
        )
    elif risk_level == RiskLevel.mild_risk:
        return (
            "评估发现轻度认知风险，建议尽快就医进行神经心理学全面评估，"
            f"重点关注{weak_str}领域。建议加强有氧运动、社交活动及认知训练，"
            "控制血压、血糖、血脂等血管风险因素。每3个月复查一次。"
        )
    else:
        return (
            "评估发现高度认知障碍风险，强烈建议立即至神经内科或记忆门诊就诊进行全面检查，"
            f"包括头颅MRI、神经心理学测试及血液生化检查。{weak_str}领域存在显著缺损。"
            "家属应加强日常看护，避免老人独自外出，防止走失及意外伤害。"
        )


def analyze_session(session_id: int, db_url: str) -> Dict[str, Any]:
    """
    Core AI analysis function executed by Celery worker.

    Steps:
    1. Connect to DB using provided db_url
    2. Load session and all responses
    3. Calculate per-domain scores
    4. Generate probability distribution (NC/MCI/AD)
    5. Assign risk level
    6. Generate SHAP values and recommendation
    7. Persist AssessmentResult
    8. Return result dict

    Args:
        session_id: ID of the AssessmentSession to analyze
        db_url: SQLAlchemy database URL (passed from Celery task to avoid
                carrying live DB connections across process boundaries)

    Returns:
        Dict containing all result fields
    """
    # Create a fresh DB connection in the worker process
    engine = create_engine(db_url, pool_pre_ping=True, echo=False)
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = LocalSession()

    try:
        # Load session
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
        if session is None:
            raise ValueError(f"AssessmentSession {session_id} not found")

        # Load all responses for this session
        responses = (
            db.query(AssessmentResponse)
            .filter(AssessmentResponse.session_id == session_id)
            .all()
        )

        # Build question lookup
        question_ids = [r.question_id for r in responses]
        questions_list = db.query(Question).filter(Question.id.in_(question_ids)).all()
        questions: Dict[int, Question] = {q.id: q for q in questions_list}

        # Step 3: Calculate domain scores
        domain_scores = _calculate_domain_scores(responses, questions)

        # Step 4: Calculate MMSE-equivalent score
        mmse_score = _calculate_mmse_score(domain_scores)

        # Step 5: Generate probability distribution
        probs = _generate_probabilities(domain_scores, mmse_score)
        nc_probability = probs["nc"]
        mci_probability = probs["mci"]
        ad_probability = probs["ad"]

        # Step 6: Assign risk level
        risk_level = _assign_risk_level(probs, mmse_score)

        # Step 7: Generate SHAP values and recommendation
        shap_values = _generate_shap_values(domain_scores)
        recommendation = _generate_recommendation(risk_level, domain_scores)

        # Step 8: Check for existing result (idempotent)
        existing_result = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.session_id == session_id)
            .first()
        )

        if existing_result is not None:
            # Update existing result
            existing_result.risk_level = risk_level
            existing_result.nc_probability = nc_probability
            existing_result.mci_probability = mci_probability
            existing_result.ad_probability = ad_probability
            existing_result.mmse_score = mmse_score
            existing_result.domain_scores = domain_scores
            existing_result.shap_values = shap_values
            existing_result.recommendation = recommendation
            db.commit()
            db.refresh(existing_result)
            result_id = existing_result.id
        else:
            result = AssessmentResult(
                session_id=session_id,
                risk_level=risk_level,
                nc_probability=nc_probability,
                mci_probability=mci_probability,
                ad_probability=ad_probability,
                mmse_score=mmse_score,
                domain_scores=domain_scores,
                shap_values=shap_values,
                recommendation=recommendation,
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            result_id = result.id

        return {
            "result_id": result_id,
            "session_id": session_id,
            "risk_level": risk_level.value,
            "nc_probability": nc_probability,
            "mci_probability": mci_probability,
            "ad_probability": ad_probability,
            "mmse_score": mmse_score,
            "domain_scores": domain_scores,
            "shap_values": shap_values,
            "recommendation": recommendation,
        }

    finally:
        db.close()
        engine.dispose()
