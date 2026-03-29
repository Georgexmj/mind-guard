from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, users, assessments, questions, communities, dashboard, interventions

# Import all models to ensure they are registered with SQLAlchemy metadata
import app.models.user  # noqa: F401
import app.models.assessment  # noqa: F401
import app.models.intervention  # noqa: F401

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "基于多模态交互的社区老年认知障碍早期筛查与干预系统 API\n\n"
        "A multimodal AI-powered system for early screening and intervention "
        "of cognitive impairment in community-dwelling elderly populations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(assessments.router)
app.include_router(questions.router)
app.include_router(communities.router)
app.include_router(dashboard.router)
app.include_router(interventions.router)


@app.on_event("startup")
def on_startup():
    """Create all database tables on application startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["System"])
def root():
    """Root endpoint returning API metadata."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Community Cognitive Impairment Screening System API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": "/api/v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "assessments": "/api/v1/assessments",
            "questions": "/api/v1/questions",
            "communities": "/api/v1/communities",
        },
    }
