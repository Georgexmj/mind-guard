from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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
    model_config = ConfigDict(from_attributes=True)

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
