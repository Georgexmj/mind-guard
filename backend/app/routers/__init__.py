from .auth import router as auth_router
from .users import router as users_router
from .assessments import router as assessments_router
from .questions import router as questions_router
from .communities import router as communities_router
from .dashboard import router as dashboard_router
from .interventions import router as interventions_router
from .notifications import router as notifications_router
from .rag import router as rag_router
from .training import router as training_router

__all__ = [
    "auth_router",
    "users_router",
    "assessments_router",
    "questions_router",
    "communities_router",
    "dashboard_router",
    "interventions_router",
    "notifications_router",
    "rag_router",
    "training_router",
]
