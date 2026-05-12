from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.assessment import (
    AssessmentSession, AssessmentResponse, AssessmentResult,
    Question, SessionStatus
)
from app.schemas.assessment import AnswerSubmit

PAUSE_RESUME_WINDOW_MINUTES = 30


def get_pause_deadline(session: AssessmentSession) -> Optional[datetime]:
    """
    Reuse completed_at as pause timestamp when status=pending.
    No schema migration required and completed sessions remain distinguishable
    by status=completed.
    """
    if session.status != SessionStatus.pending or session.completed_at is None:
        return None
    return session.completed_at + timedelta(minutes=PAUSE_RESUME_WINDOW_MINUTES)


def is_session_resumable(session: AssessmentSession, now: Optional[datetime] = None) -> bool:
    if session.status != SessionStatus.pending:
        return False
    deadline = get_pause_deadline(session)
    if deadline is None:
        return False
    current = now or datetime.utcnow()
    return current <= deadline


def _attach_pause_metadata(session: AssessmentSession) -> None:
    deadline = get_pause_deadline(session)
    session.pause_deadline = deadline
    session.is_resumable = is_session_resumable(session)


def create_session(db: Session, user_id: int) -> AssessmentSession:
    """
    Create a new assessment session for the given user.
    Sets status to in_progress and records started_at.
    """
    session = AssessmentSession(
        user_id=user_id,
        status=SessionStatus.in_progress,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_next_questions(db: Session, session_id: int, count: int = 5) -> List[Question]:
    """
    Get next unanswered questions for the given session.
    MVP: simple sequential ordering; IRT adaptive selection for production.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status not in (SessionStatus.in_progress, SessionStatus.pending):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )

    if session.status == SessionStatus.pending:
        if not is_session_resumable(session):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Paused session expired. Resume is only available within {PAUSE_RESUME_WINDOW_MINUTES} minutes.",
            )
        # Auto-resume when user requests next questions in valid pause window.
        session.status = SessionStatus.in_progress
        session.completed_at = None
        db.commit()
        db.refresh(session)

    # Get IDs of already-answered questions in this session
    answered_ids = (
        db.query(AssessmentResponse.question_id)
        .filter(AssessmentResponse.session_id == session_id)
        .subquery()
    )

    questions = (
        db.query(Question)
        .filter(Question.is_active == True)
        .filter(Question.id.not_in(answered_ids))
        # Randomize selection for each assessment session so users don't always
        # receive the same first N questions from the bank.
        .order_by(func.random())
        .limit(count)
        .all()
    )

    return questions


def submit_answer(db: Session, session_id: int, answer: AnswerSubmit) -> AssessmentResponse:
    """
    Record a user's answer for a question in a session.
    Evaluates correctness for choice questions automatically.
    Supports both integer and string question IDs from mini-program.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status != SessionStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in progress",
        )

    # Handle both integer and string question IDs
    question_id_str = answer.question_id
    question = None
    final_question_id = None
    original_question_id = question_id_str  # Store original string ID
    
    # Try to parse as integer first
    try:
        int_question_id = int(question_id_str)
        question = db.query(Question).filter(Question.id == int_question_id).first()
        final_question_id = int_question_id
    except (ValueError, TypeError):
        # It's a string ID from mini-program (e.g., 'q1', 'mmse_1', 'moca_1')
        # For mini-program questions, use a hash-based integer ID
        # Use hash of string to generate a consistent integer
        hash_val = hash(question_id_str)
        final_question_id = abs(hash_val) % 1000000
        # Check if this question_id already exists in responses
        existing = (
            db.query(AssessmentResponse)
            .filter(
                AssessmentResponse.session_id == session_id,
                AssessmentResponse.question_id == final_question_id,
            )
            .first()
        )
        if existing:
            # Collision - use a different approach
            final_question_id = abs(hash(question_id_str + str(session_id))) % 1000000

    # Check for duplicate answer
    existing = (
        db.query(AssessmentResponse)
        .filter(
            AssessmentResponse.session_id == session_id,
            AssessmentResponse.question_id == final_question_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question already answered in this session",
        )

    # Evaluate correctness for choice questions
    is_correct: Optional[bool] = None
    score: Optional[float] = None

    if question:
        if question.q_type.value == "choice" and question.correct_answer is not None:
            answer_text_norm = (answer.answer_text or "").strip().lower()
            correct_norm = question.correct_answer.strip().lower()
            is_correct = answer_text_norm == correct_norm
            score = 1.0 if is_correct else 0.0
        elif question.q_type.value in ("voice", "drawing", "scale"):
            if question.q_type.value == "scale" and answer.answer_text is not None:
                try:
                    raw_val = float(answer.answer_text)
                    score = min(max(raw_val / 10.0, 0.0), 1.0)
                    is_correct = score >= 0.5
                except ValueError:
                    score = 0.0
                    is_correct = False

    # Store original question_id in answer_data
    answer_data_with_id = answer.answer_data or {}
    answer_data_with_id["original_question_id"] = original_question_id

    response = AssessmentResponse(
        session_id=session_id,
        question_id=final_question_id,
        answer_text=answer.answer_text,
        answer_data=answer_data_with_id,
        reaction_time_ms=answer.reaction_time_ms,
        is_correct=is_correct,
        score=score,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


def complete_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Mark session as completed, run AI analysis synchronously.
    Returns dict with analysis result.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status != SessionStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is not in progress (current status: {session.status.value})",
        )

    # Ensure at least one answer was submitted
    response_count = (
        db.query(AssessmentResponse)
        .filter(AssessmentResponse.session_id == session_id)
        .count()
    )
    if response_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete session with no answers submitted",
        )

    # Update session status
    session.status = SessionStatus.completed
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    # Try to run AI analysis asynchronously using Celery
    # Fall back to immediate simple analysis if Celery/Redis is not available
    try:
        from app.tasks.analysis import analyze_session_task
        import redis
        
        # Test Redis connection before sending task
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
            r.ping()
            # Redis is available, send to Celery
            task = analyze_session_task.delay(session_id)
            session.task_id = task.task_id
            db.commit()
            return {
                "task_id": session.task_id,
                "session_id": session_id,
                "status": "pending",
                "message": "Assessment completed, analysis in progress"
            }
        except (redis.ConnectionError, redis.TimeoutError):
            # Redis not available, fall back to simple analysis
            print("Redis not available, using fallback analysis")
            raise Exception("Redis not available")
    except Exception as e:
        # If analysis fails, create a fallback result based on simple scoring
        print(f"AI analysis failed, creating fallback result: {str(e)}")
        session.task_id = "sync_task_" + str(session_id) + "_fallback"
        
        # Create fallback result using simple MMSE-like scoring
        responses = db.query(AssessmentResponse).filter(AssessmentResponse.session_id == session_id).all()
        questions = db.query(Question).all()
        question_dict = {q.id: q for q in questions}
        
        # Calculate simple score (correct answers count)
        correct_count = 0
        total_possible = 0
        
        for resp in responses:
            q = question_dict.get(resp.question_id)
            if q and hasattr(q, 'correct_answer') and q.correct_answer:
                total_possible += 1
                answer_text = resp.answer_text or str(resp.answer_data.get('answer_value', '') if isinstance(resp.answer_data, dict) else '')
                if str(answer_text).strip() == str(q.correct_answer).strip():
                    correct_count += 1
        
        # Calculate MMSE-like score (0-30 scale)
        mmse_score = round((correct_count / max(total_possible, 1)) * 30)
        
        # Determine risk level based on MMSE score (following medical standards)
        # MMSE: 27-30 = normal, 21-26 = mild cognitive impairment, 10-20 = moderate, <10 = severe
        if mmse_score >= 27:
            risk_level = 'normal'
        elif mmse_score >= 21:
            risk_level = 'mild_risk'
        elif mmse_score >= 10:
            risk_level = 'moderate_risk'
        else:
            risk_level = 'high_risk'
        
        # Calculate probabilities based on MMSE score
        # Normal cognition probability (higher = better)
        nc_prob = min(1.0, max(0.0, mmse_score / 30))
        
        # MCI (Mild Cognitive Impairment) probability
        if mmse_score >= 27:
            mci_prob = 0.05  # Low probability when normal
        elif mmse_score >= 21:
            mci_prob = min(1.0, max(0.0, (27 - mmse_score) / 6 * 0.6 + 0.1))  # 10%-70% for MCI range
        elif mmse_score >= 10:
            mci_prob = min(1.0, max(0.0, (20 - mmse_score) / 10 * 0.3 + 0.5))  # 50%-80% for moderate
        else:
            mci_prob = 0.7  # High probability for severe
        
        # AD (Alzheimer's Disease) probability
        if mmse_score >= 27:
            ad_prob = 0.02  # Very low probability when normal
        elif mmse_score >= 21:
            ad_prob = min(1.0, max(0.0, (27 - mmse_score) / 6 * 0.15 + 0.02))  # 2%-17% for MCI range
        elif mmse_score >= 10:
            ad_prob = min(1.0, max(0.0, (20 - mmse_score) / 10 * 0.3 + 0.15))  # 15%-45% for moderate
        else:
            ad_prob = min(1.0, max(0.0, (10 - mmse_score) / 10 * 0.4 + 0.45))  # 45%-85% for severe
        
        # Create fallback assessment result
        fallback_result = AssessmentResult(
            session_id=session_id,
            risk_level=risk_level,
            nc_probability=nc_prob,
            mci_probability=mci_prob,
            ad_probability=ad_prob,
            mmse_score=mmse_score,
            domain_scores={
                'memory': round(mmse_score * 0.2),
                'orientation': round(mmse_score * 0.33),
                'language': round(mmse_score * 0.27),
                'attention': round(mmse_score * 0.17),
                'visuospatial': 1 if mmse_score >= 20 else 0,
                'executive': 0,
            },
            shap_values={
                'model_confidence': 0.6,
                'modality_quality': {'questionnaire': {'available': True, 'quality': 0.7}},
                'modality_contributions': {'questionnaire': 1.0},
                'top_factors': ['问卷答题表现'],
                'data_quality_flag': 'warning',
                'model_name': 'fallback_rule_engine',
                'model_strategy': 'rule_based',
            },
            recommendation=f"评估完成，MMSE得分：{mmse_score}/30。风险等级：{risk_level}。建议定期复查。"
        )
        
        db.add(fallback_result)
        db.commit()
        db.refresh(fallback_result)
        
        result_dict = {
            "result_id": fallback_result.id,
            "session_id": session_id,
            "risk_level": risk_level,
            "nc_probability": nc_prob,
            "mci_probability": mci_prob,
            "ad_probability": ad_prob,
            "mmse_score": mmse_score,
            "domain_scores": fallback_result.domain_scores,
        }
        
        return {
            "task_id": session.task_id,
            "session_id": session_id,
            "status": "completed",
            "analysis_result": result_dict,
            "fallback": True
        }


def pause_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Pause an in-progress session and allow resume within 30 minutes.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status == SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed session cannot be paused",
        )

    if session.status == SessionStatus.pending:
        if not is_session_resumable(session):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Paused session expired. Resume is only available within {PAUSE_RESUME_WINDOW_MINUTES} minutes.",
            )
        _attach_pause_metadata(session)
        return {
            "session_id": session.id,
            "status": session.status,
            "message": "Session already paused",
            "pause_deadline": session.pause_deadline,
            "is_resumable": session.is_resumable,
        }

    session.status = SessionStatus.pending
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    _attach_pause_metadata(session)
    return {
        "session_id": session.id,
        "status": session.status,
        "message": "Session paused successfully",
        "pause_deadline": session.pause_deadline,
        "is_resumable": session.is_resumable,
    }


def resume_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Resume a paused session if within the 30-minute window.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status == SessionStatus.in_progress:
        return {
            "session_id": session.id,
            "status": session.status,
            "message": "Session already in progress",
            "pause_deadline": None,
            "is_resumable": True,
        }

    if session.status != SessionStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only paused sessions can be resumed (current status: {session.status.value})",
        )

    if not is_session_resumable(session):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Paused session expired. Resume is only available within {PAUSE_RESUME_WINDOW_MINUTES} minutes.",
        )

    session.status = SessionStatus.in_progress
    session.completed_at = None
    db.commit()
    db.refresh(session)
    return {
        "session_id": session.id,
        "status": session.status,
        "message": "Session resumed successfully",
        "pause_deadline": None,
        "is_resumable": True,
    }


def discard_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Discard an unfinished assessment session.

    Intended for "user exited midway" scenario. Completed sessions are retained
    for audit/history and cannot be discarded through this API.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status == SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed session cannot be discarded",
        )

    db.query(AssessmentResult).filter(AssessmentResult.session_id == session_id).delete(synchronize_session=False)
    db.query(AssessmentResponse).filter(AssessmentResponse.session_id == session_id).delete(synchronize_session=False)
    db.delete(session)
    db.commit()

    return {"session_id": session_id, "status": "discarded"}


def get_result(db: Session, session_id: int) -> Optional[AssessmentResult]:
    """Retrieve the AI result for a session, or None if not yet available."""
    result = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.session_id == session_id)
        .first()
    )
    if result is not None:
        # Handle both dict and string (JSON) formats for shap_values
        shap_values = result.shap_values
        if isinstance(shap_values, str):
            import json
            try:
                shap_values = json.loads(shap_values)
            except (json.JSONDecodeError, TypeError):
                shap_values = {}
        
        explainability = shap_values if isinstance(shap_values, dict) else {}
        
        # Expose frequently used explainability fields as top-level response attributes.
        result.model_confidence = explainability.get("model_confidence")
        result.modality_quality = explainability.get("modality_quality")
        result.modality_contributions = explainability.get("modality_contributions")
        result.top_factors = explainability.get("top_factors")
        result.data_quality_flag = explainability.get("data_quality_flag")
        result.model_name = explainability.get("model_name")
        result.model_strategy = explainability.get("model_strategy")
        result.engine_info = explainability.get("engine_info")
        result.attention_matrix = explainability.get("attention_matrix")
        result.mmse_subscores = explainability.get("mmse_subscores")
        result.moca_subscores = explainability.get("moca_subscores")
        result.moca_score = explainability.get("moca_score")
        result.moca_score_corrected = explainability.get("moca_score_corrected")
        result.education_correction_applied = explainability.get("education_correction_applied")
        result.education_correction_points = explainability.get("education_correction_points")
        result.clinical_report = explainability.get("clinical_report")
        result.recommendation_items = explainability.get("recommendation_items")
    return result


def get_sessions_by_user(db: Session, user_id: int) -> List[AssessmentSession]:
    """Return all assessment sessions for a user, most recent first."""
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.created_at.desc())
        .all()
    )
    for session in sessions:
        _attach_pause_metadata(session)
    return sessions


def get_session_by_id(db: Session, session_id: int) -> Optional[AssessmentSession]:
    """Retrieve a single session by its ID."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is not None:
        _attach_pause_metadata(session)
    return session
