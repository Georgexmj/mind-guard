"""
Simple training report server for testing.
This is a standalone server that handles training data reporting and basic assessment sessions.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./training_reports.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TrainingReportDB(Base):
    __tablename__ = "training_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    elder_id = Column(Integer, nullable=False, index=True)
    course_id = Column(String(100), nullable=False)
    course_name = Column(String(200), nullable=False)
    correct_count = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    answers = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssessmentSessionDB(Base):
    __tablename__ = "assessment_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    elder_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), nullable=False, default="pending")
    risk_level = Column(String(50), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="MindGuard Service", version="1.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrainingAnswerDetail(BaseModel):
    questionId: int
    questionContent: str
    userAnswer: Optional[str]
    isCorrect: bool
    correctAnswer: Optional[str]


class TrainingReportCreate(BaseModel):
    userId: str
    courseId: str
    courseName: str
    correctCount: int
    totalQuestions: int
    accuracy: int
    completedAt: datetime
    answers: List[TrainingAnswerDetail]


class TrainingReportOut(BaseModel):
    id: int
    elder_id: int
    course_id: str
    course_name: str
    correct_count: int
    total_questions: int
    accuracy: float
    completed_at: datetime
    answers: Optional[List[dict]]
    created_at: datetime


class AssessmentSessionOut(BaseModel):
    id: int
    elder_id: int
    session_id: str
    status: str
    risk_level: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# User Models for Authentication
class LoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: int
    name: str
    id_card: str
    phone: Optional[str]

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# Mock users for testing
MOCK_USERS = {
    "123456194808151234": {
        "id": 1,
        "name": "测试老人",
        "id_card": "123456194808151234",
        "password": "123456",
        "phone": "13800138000"
    },
    "123456195001011234": {
        "id": 2,
        "name": "张三",
        "id_card": "123456195001011234",
        "password": "123456",
        "phone": "13900139000"
    }
}


# Authentication Routes
@app.post("/api/v1/auth/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = MOCK_USERS.get(username)
    
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    return {
        "access_token": f"mock_token_{user['id']}",
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "id_card": user["id_card"],
            "phone": user["phone"]
        }
    }


# Training Report Routes
@app.post("/api/v1/training/report", response_model=TrainingReportOut, status_code=201)
def submit_training_report(data: TrainingReportCreate):
    db = SessionLocal()
    
    elder_id = None
    if data.userId.isdigit():
        elder_id = int(data.userId)
    else:
        elder_id = 1
    
    report = TrainingReportDB(
        elder_id=elder_id,
        course_id=data.courseId,
        course_name=data.courseName,
        correct_count=data.correctCount,
        total_questions=data.totalQuestions,
        accuracy=data.accuracy,
        completed_at=data.completedAt,
        answers=[answer.model_dump() for answer in data.answers],
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    db.close()
    
    return report


@app.get("/api/v1/training/reports", response_model=List[TrainingReportOut])
def get_training_reports(
    elder_id: Optional[int] = None,
    course_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    db = SessionLocal()
    q = db.query(TrainingReportDB)
    
    if elder_id is not None:
        q = q.filter(TrainingReportDB.elder_id == elder_id)
    if course_id is not None:
        q = q.filter(TrainingReportDB.course_id == course_id)
    
    reports = q.order_by(TrainingReportDB.completed_at.desc())\
               .offset((page - 1) * page_size)\
               .limit(page_size)\
               .all()
    
    db.close()
    return reports


@app.get("/api/v1/training/reports/{report_id}", response_model=TrainingReportOut)
def get_training_report(report_id: int):
    db = SessionLocal()
    report = db.query(TrainingReportDB).filter(TrainingReportDB.id == report_id).first()
    db.close()
    
    if not report:
        raise HTTPException(status_code=404, detail="Training report not found")
    
    return report


# Assessment Session Routes
@app.get("/api/v1/assessments/sessions", response_model=List[AssessmentSessionOut])
def get_assessment_sessions(
    elder_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    db = SessionLocal()
    q = db.query(AssessmentSessionDB)
    
    if elder_id is not None:
        q = q.filter(AssessmentSessionDB.elder_id == elder_id)
    if status is not None:
        q = q.filter(AssessmentSessionDB.status == status)
    
    sessions = q.order_by(AssessmentSessionDB.created_at.desc())\
                .offset((page - 1) * page_size)\
                .limit(page_size)\
                .all()
    
    db.close()
    return sessions


@app.get("/api/v1/assessments/sessions/{session_id}", response_model=AssessmentSessionOut)
def get_assessment_session(session_id: str):
    db = SessionLocal()
    session = db.query(AssessmentSessionDB).filter(AssessmentSessionDB.session_id == session_id).first()
    db.close()
    
    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    
    return session


# User Routes
@app.get("/api/v1/users/my-elders")
def get_my_elders():
    # Mock data for testing
    return [
        {
            "id": 1,
            "name": "李奶奶",
            "id_card": "123456194808151234",
            "phone": "13800138000",
            "age": 78,
            "gender": "male"
        }
    ]


# Health Check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Root endpoint
@app.get("/")
def root():
    return {
        "app": "MindGuard Service",
        "version": "1.0",
        "description": "Training Report and Assessment Service",
        "docs": "/docs",
        "health": "/health",
        "api_prefix": "/api/v1",
        "endpoints": {
            "training_report": "/api/v1/training/report",
            "training_reports": "/api/v1/training/reports",
            "assessment_sessions": "/api/v1/assessments/sessions",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
