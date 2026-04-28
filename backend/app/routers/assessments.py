from datetime import datetime, timedelta
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from typing import List, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.assessment import AssessmentResult, AssessmentSession
from app.models.notification import NotificationType
from app.models.user import User, UserRelationship, UserRole
from app.schemas.assessment import (
    AnswerOut,
    AnswerSubmit,
    AssessmentTrendOut,
    FamilyReadableReportOut,
    PauseResumeOut,
    QuestionOut,
    ResultOut,
    SessionCreate,
    SessionOut,
    TaskStatusOut,
    TrendPointOut,
)
from app.services import assessment_service
from app.services.reminder_service import dispatch_reassessment_reminders as dispatch_reassessment_reminders_service
from app.services.notification_service import upsert_notification
from app.services.intervention_reco import build_top5_from_result, suggest_next_reassessment_date
from app.services.minio_service import build_object_url, upload_bytes
from app.services.report_service import build_doctor_report_pdf
from app.services.wechat_service import send_to_user_by_binding
from app.tasks.celery_app import celery_app
from app.config import settings

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])

RISK_RANK = {"normal": 0, "mild_risk": 1, "high_risk": 2}


def _calc_risk_change(current: Optional[str], previous: Optional[str]) -> str:
    if not current or not previous:
        return "unknown"
    current_rank = RISK_RANK.get(current)
    previous_rank = RISK_RANK.get(previous)
    if current_rank is None or previous_rank is None:
        return "unknown"
    if current_rank > previous_rank:
        return "worsened"
    if current_rank < previous_rank:
        return "improved"
    return "stable"


def _resolve_trend_elder_id(
    db: Session,
    current_user: User,
    elder_id: Optional[int],
) -> int:
    if current_user.role == UserRole.elder:
        return current_user.id

    if current_user.role == UserRole.family:
        if elder_id is None:
            raise HTTPException(status_code=400, detail="Family user must provide elder_id")
        relation = (
            db.query(UserRelationship)
            .filter(
                UserRelationship.family_id == current_user.id,
                UserRelationship.elder_id == elder_id,
            )
            .first()
        )
        if not relation:
            raise HTTPException(status_code=403, detail="Family member has no access to this elder")
        return elder_id

    if elder_id is None:
        raise HTTPException(status_code=400, detail="elder_id is required for doctor/admin")
    return elder_id


def _can_access_session(db: Session, current_user: User, session: AssessmentSession) -> bool:
    if current_user.role in (UserRole.admin, UserRole.doctor):
        return True
    if current_user.role == UserRole.elder:
        return session.user_id == current_user.id
    if current_user.role == UserRole.family:
        relation = (
            db.query(UserRelationship)
            .filter(
                UserRelationship.family_id == current_user.id,
                UserRelationship.elder_id == session.user_id,
            )
            .first()
        )
        return relation is not None
    return False


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    _: SessionCreate = SessionCreate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.family:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Family members cannot start assessment sessions",
        )
    return assessment_service.create_session(db, current_user.id)


@router.get("/sessions", response_model=List[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    elder_id: Optional[int] = Query(None),
):
    if current_user.role in (UserRole.admin, UserRole.doctor):
        return db.query(AssessmentSession).order_by(AssessmentSession.created_at.desc()).all()
    
    if current_user.role == UserRole.elder:
        return assessment_service.get_sessions_by_user(db, current_user.id)
    
    if current_user.role == UserRole.family:
        if elder_id is not None:
            relation = (
                db.query(UserRelationship)
                .filter(
                    UserRelationship.family_id == current_user.id,
                    UserRelationship.elder_id == elder_id,
                )
                .first()
            )
            if not relation:
                raise HTTPException(status_code=403, detail="Family member has no access to this elder")
            return assessment_service.get_sessions_by_user(db, elder_id)
        
        elders = (
            db.query(User)
            .join(UserRelationship, UserRelationship.elder_id == User.id)
            .filter(UserRelationship.family_id == current_user.id)
            .all()
        )
        elder_ids = [e.id for e in elders]
        if not elder_ids:
            return []
        return (
            db.query(AssessmentSession)
            .filter(AssessmentSession.user_id.in_(elder_ids))
            .order_by(AssessmentSession.created_at.desc())
            .all()
        )
    
    return []


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return session


@router.get("/sessions/{session_id}/questions", response_model=List[QuestionOut])
def get_questions(
    session_id: int,
    count: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.get_next_questions(db, session_id, count=count)


@router.post("/sessions/{session_id}/answers", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
def submit_answer(
    session_id: int,
    answer: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.submit_answer(db, session_id, answer)


@router.post("/sessions/{session_id}/uploads/audio")
async def upload_audio_file(
    session_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")

    content_type = (file.content_type or "").lower()
    if not (content_type.startswith("audio/") or content_type in {"application/octet-stream"}):
        raise HTTPException(status_code=400, detail="Only audio files are supported")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    object_name = upload_bytes(
        file_bytes=file_bytes,
        filename=file.filename or "voice.mp3",
        prefix=f"sessions/{session_id}/audio",
        content_type=file.content_type or "audio/mpeg",
    )
    return {
        "session_id": session_id,
        "object_name": object_name,
        "audio_url": build_object_url(object_name),
        "size_bytes": len(file_bytes),
        "content_type": file.content_type or "audio/mpeg",
    }


@router.post("/sessions/{session_id}/complete", status_code=status.HTTP_202_ACCEPTED)
def complete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.complete_session(db, session_id)


@router.post("/sessions/{session_id}/pause", response_model=PauseResumeOut)
def pause_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.pause_session(db, session_id)


@router.post("/sessions/{session_id}/resume", response_model=PauseResumeOut)
def resume_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.resume_session(db, session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def discard_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.discard_session(db, session_id)


@router.get("/sessions/{session_id}/result", response_model=Optional[ResultOut])
def get_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this session")
    return assessment_service.get_result(db, session_id)


@router.get("/trend", response_model=AssessmentTrendOut)
def get_assessment_trend(
    elder_id: Optional[int] = Query(None),
    months: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_elder_id = _resolve_trend_elder_id(db, current_user, elder_id)
    start_time = datetime.utcnow() - timedelta(days=months * 31)

    rows = (
        db.query(AssessmentResult, AssessmentSession)
        .join(AssessmentSession, AssessmentResult.session_id == AssessmentSession.id)
        .filter(
            AssessmentSession.user_id == target_elder_id,
            AssessmentResult.created_at >= start_time,
        )
        .order_by(AssessmentResult.created_at.asc())
        .all()
    )

    points: List[TrendPointOut] = []
    risk_levels: List[str] = []
    for result, session in rows:
        shap = result.shap_values if isinstance(result.shap_values, dict) else {}
        risk = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)
        risk_levels.append(risk)
        points.append(
            TrendPointOut(
                session_id=session.id,
                assessed_at=result.created_at,
                mmse_score=result.mmse_score,
                moca_score_corrected=shap.get("moca_score_corrected"),
                risk_level=risk,
            )
        )

    latest_risk = risk_levels[-1] if risk_levels else None
    previous_risk = risk_levels[-2] if len(risk_levels) > 1 else None
    risk_change = _calc_risk_change(latest_risk, previous_risk)

    next_date: Optional[str] = None
    if points and latest_risk:
        next_date = suggest_next_reassessment_date(
            latest_risk,
            points[-1].assessed_at.date(),
        ).isoformat()

    return AssessmentTrendOut(
        elder_id=target_elder_id,
        points=points,
        latest_risk_level=latest_risk,
        previous_risk_level=previous_risk,
        risk_change=risk_change,
        next_reassessment_date=next_date,
    )


@router.get("/sessions/{session_id}/doctor-report.pdf")
def export_doctor_report_pdf(
    session_id: int,
    hospital_name: str = Query("MindGuard 社区认知门诊"),
    doctor_name: str = Query("-"),
    signature_text: str = Query("电子签名有效"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.admin, UserRole.doctor):
        raise HTTPException(status_code=403, detail="Only doctor/admin can export doctor report")

    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    result = db.query(AssessmentResult).filter(AssessmentResult.session_id == session_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Assessment result not found")

    risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)
    next_date = suggest_next_reassessment_date(risk_level, result.created_at.date())
    recommendations = build_top5_from_result(result)
    verify_token = f"mindguard:session:{session.id}:ts:{int(datetime.utcnow().timestamp())}"
    pdf_bytes = build_doctor_report_pdf(
        session=session,
        result=result,
        recommendations=recommendations,
        next_reassessment_date=next_date,
        hospital_name=hospital_name,
        doctor_name=doctor_name,
        signature_text=signature_text,
        verify_token=verify_token,
    )

    filename = f"mindguard_doctor_report_session_{session_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/doctor/batch")
def export_doctor_reports_batch(
    session_ids: List[int] = Query(...),
    hospital_name: str = Query("MindGuard 社区认知门诊"),
    doctor_name: str = Query("-"),
    signature_text: str = Query("电子签名有效"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.admin, UserRole.doctor):
        raise HTTPException(status_code=403, detail="Only doctor/admin can export doctor report")
    if not session_ids:
        raise HTTPException(status_code=400, detail="session_ids is required")

    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as zf:
        for session_id in session_ids:
            session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
            if not session:
                continue
            result = db.query(AssessmentResult).filter(AssessmentResult.session_id == session_id).first()
            if not result:
                continue
            risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)
            next_date = suggest_next_reassessment_date(risk_level, result.created_at.date())
            recommendations = build_top5_from_result(result)
            verify_token = f"mindguard:session:{session.id}:ts:{int(datetime.utcnow().timestamp())}"
            pdf_bytes = build_doctor_report_pdf(
                session=session,
                result=result,
                recommendations=recommendations,
                next_reassessment_date=next_date,
                hospital_name=hospital_name,
                doctor_name=doctor_name,
                signature_text=signature_text,
                verify_token=verify_token,
            )
            zf.writestr(f"mindguard_doctor_report_session_{session_id}.pdf", pdf_bytes)

    buffer.seek(0)
    zip_name = f"mindguard_doctor_reports_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@router.get("/sessions/{session_id}/family-report", response_model=FamilyReadableReportOut)
def get_family_readable_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not _can_access_session(db, current_user, session):
        raise HTTPException(status_code=403, detail="Access denied")

    result = db.query(AssessmentResult).filter(AssessmentResult.session_id == session_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Assessment result not found")

    risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)
    rows = (
        db.query(AssessmentResult)
        .join(AssessmentSession, AssessmentResult.session_id == AssessmentSession.id)
        .filter(AssessmentSession.user_id == session.user_id)
        .order_by(AssessmentResult.created_at.desc())
        .limit(2)
        .all()
    )
    latest = rows[0] if rows else None
    previous = rows[1] if len(rows) > 1 else None
    previous_risk = (
        previous.risk_level.value if previous and hasattr(previous.risk_level, "value") else (str(previous.risk_level) if previous else None)
    )
    latest_risk = (
        latest.risk_level.value if latest and hasattr(latest.risk_level, "value") else (str(latest.risk_level) if latest else risk_level)
    )
    risk_change = _calc_risk_change(latest_risk, previous_risk)

    next_date = suggest_next_reassessment_date(risk_level, result.created_at.date()).isoformat()

    summary_map = {
        "normal": "\u8fd9\u6b21\u8bc4\u4f30\u63d0\u793a\u6574\u4f53\u8ba4\u77e5\u72b6\u6001\u8f83\u5e73\u7a33\u3002",
        "mild_risk": "\u8fd9\u6b21\u8bc4\u4f30\u63d0\u793a\u5b58\u5728\u8f7b\u5ea6\u8ba4\u77e5\u98ce\u9669\uff0c\u5efa\u8bae\u5c3d\u5feb\u590d\u8bc4\u3002",
        "high_risk": "\u8fd9\u6b21\u8bc4\u4f30\u63d0\u793a\u8f83\u9ad8\u98ce\u9669\uff0c\u5efa\u8bae\u5c3d\u5feb\u5c31\u533b\u8fdb\u4e00\u6b65\u68c0\u67e5\u3002",
    }
    interpretation_map = {
        "normal": "\u76ee\u524d\u66f4\u63a5\u8fd1\u6b63\u5e38\u8303\u56f4\uff0c\u7ee7\u7eed\u4fdd\u6301\u89c4\u5f8b\u4f5c\u606f\u548c\u8bad\u7ec3\u5373\u53ef\u3002",
        "mild_risk": "\u53ef\u80fd\u6709\u65e9\u671f\u4e0b\u964d\u4fe1\u53f7\uff0c\u901a\u8fc7\u6301\u7eed\u5e72\u9884\u548c\u968f\u8bbf\uff0c\u5f88\u591a\u60c5\u51b5\u53ef\u4ee5\u6539\u5584\u3002",
        "high_risk": "\u5f53\u524d\u98ce\u9669\u8f83\u9ad8\uff0c\u8bf7\u5bb6\u5c5e\u5c3d\u5feb\u966a\u540c\u5c31\u8bca\uff0c\u6309\u533b\u5631\u5b8c\u6210\u8fdb\u4e00\u6b65\u8bc4\u4f30\u3002",
    }

    tips = [
        "\u6bcf\u5929\u4fdd\u630130\u5206\u949f\u8f7b\u4e2d\u5ea6\u6d3b\u52a8\uff08\u6b65\u884c/\u4f53\u64cd\uff09\u3002",
        "\u6bcf\u5929\u8fdb\u884c15-20\u5206\u949f\u8ba4\u77e5\u8bad\u7ec3\uff08\u8bb0\u5fc6\u6216\u8ba1\u7b97\u7ec3\u4e60\uff09\u3002",
        "\u89c4\u5f8b\u4f5c\u606f\uff0c\u5c3d\u91cf\u5728\u540c\u4e00\u65f6\u95f4\u5c31\u5bdd\u548c\u8d77\u5e8a\u3002",
        "\u5bb6\u5c5e\u6bcf\u5468\u81f3\u5c11\u4e00\u6b21\u56de\u987e\u6253\u5361\u60c5\u51b5\u5e76\u6c9f\u901a\u3002",
    ]
    warning_signs = [
        "\u8fd1\u671f\u8ff7\u8def\u3001\u9057\u5fd8\u660e\u663e\u52a0\u91cd\u3002",
        "\u65e5\u5e38\u751f\u6d3b\u80fd\u529b\u4e0b\u964d\uff08\u5982\u505a\u996d\u3001\u7528\u836f\uff09\u3002",
        "\u60c5\u7eea\u6216\u884c\u4e3a\u53d8\u5316\u660e\u663e\uff08\u70e6\u8e81/\u6de1\u6f20\uff09\u3002",
    ]

    return FamilyReadableReportOut(
        elder_id=session.user_id,
        session_id=session.id,
        assessed_at=result.created_at,
        risk_level=risk_level,
        risk_change=risk_change,
        next_reassessment_date=next_date,
        summary=summary_map.get(risk_level, summary_map["mild_risk"]),
        plain_interpretation=interpretation_map.get(risk_level, interpretation_map["mild_risk"]),
        daily_tips=tips,
        warning_signs=warning_signs,
    )


@router.post("/reminders/reassessment/dispatch")
def dispatch_reassessment_reminders(
    within_days: int = Query(7, ge=0, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.admin, UserRole.doctor):
        raise HTTPException(status_code=403, detail="Only doctor/admin can dispatch reminders")
    return dispatch_reassessment_reminders_service(
        db,
        dispatcher=current_user,
        within_days=within_days,
    )


@router.get("/tasks/{task_id}", response_model=TaskStatusOut)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task_result = AsyncResult(task_id, app=celery_app)
    result_data = None
    if task_result.ready():
        try:
            result_data = task_result.result
            if not isinstance(result_data, dict):
                result_data = {"raw": str(result_data)}
        except Exception:
            result_data = {"error": "Could not retrieve task result"}

    return TaskStatusOut(task_id=task_id, status=task_result.status, result=result_data)
