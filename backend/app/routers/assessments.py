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
    session_create: SessionCreate = SessionCreate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Determine the target user ID for the assessment
    target_user_id = current_user.id
    
    # If family member, they must specify an elder_id to assess
    if current_user.role == UserRole.family:
        if session_create.elder_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Family members must specify an elder_id to start an assessment session",
            )
        # Verify family member has permission to assess this elder
        relation = (
            db.query(UserRelationship)
            .filter(
                UserRelationship.family_id == current_user.id,
                UserRelationship.elder_id == session_create.elder_id,
            )
            .first()
        )
        if not relation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to assess this elder",
            )
        target_user_id = session_create.elder_id
    
    return assessment_service.create_session(db, target_user_id)


@router.get("/sessions", response_model=List[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    elder_id: Optional[int] = Query(None),
):
    if current_user.role in (UserRole.admin, UserRole.doctor):
        query = db.query(AssessmentSession)
        if elder_id is not None:
            query = query.filter(AssessmentSession.user_id == elder_id)
        return query.order_by(AssessmentSession.created_at.desc()).all()
    
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

    elder = db.query(User).filter(User.id == session.user_id).first()
    elder_name = elder.name if elder else "未知"

    risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)
    
    risk_level_descriptions = {
        "normal": "认知正常",
        "mild_risk": "轻度认知风险",
        "moderate_risk": "中度认知风险",
        "high_risk": "高认知风险",
    }
    risk_level_description = risk_level_descriptions.get(risk_level, "未知")

    summary_map = {
        "normal": "本次评估显示整体认知状态较稳定。",
        "mild_risk": "本次评估提示存在轻度认知风险，建议尽快复评。",
        "moderate_risk": "本次评估提示存在中度认知风险，建议密切关注并尽快就医。",
        "high_risk": "本次评估提示较高风险，建议尽快就医进行进一步检查。",
    }

    interpretation_map = {
        "normal": "目前更接近正常范围，继续保持规律作息和训练即可。",
        "mild_risk": "可能有早期下降信号，通过持续干预和随访，很多情况可以改善。",
        "moderate_risk": "认知功能有明显下降，需要加强家庭支持和专业干预。",
        "high_risk": "当前风险较高，请家属尽快陪同就诊，按医嘱完成进一步评估。",
    }

    recommendations = [
        "每天保持30分钟轻中度活动（步行/体操）。",
        "每天进行15-20分钟认知训练（记忆或计算练习）。",
        "规律作息，尽量在同一时间就寝和起床。",
        "家属每周至少一次回访打卡情况并沟通。",
    ]

    next_date = suggest_next_reassessment_date(risk_level, result.created_at.date())
    next_assessment_suggestion = f"建议于 {next_date.strftime('%Y年%m月%d日')} 前进行下一次评估"

    domain_scores = result.domain_scores if result.domain_scores else {
        "memory": 0.0,
        "orientation": 0.0,
        "language": 0.0,
        "attention": 0.0,
        "visuospatial": 0.0,
        "executive": 0.0,
    }

    top_concerns = []
    if result.mmse_score and result.mmse_score < 24:
        top_concerns.append("记忆力下降")
    if result.mmse_score and result.mmse_score < 20:
        top_concerns.append("注意力不集中")

    return FamilyReadableReportOut(
        elder_name=elder_name,
        assessment_date=result.created_at.strftime('%Y年%m月%d日'),
        risk_level=risk_level,
        risk_level_description=risk_level_description,
        mmse_score=result.mmse_score,
        moca_score=None,
        domain_scores=domain_scores,
        top_concerns=top_concerns if top_concerns else ["暂无明显异常"],
        recommendations=recommendations,
        next_assessment_suggestion=next_assessment_suggestion,
        disclaimer="本报告仅供参考，不能替代专业医疗诊断。如有疑问，请咨询专业医生。",
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
