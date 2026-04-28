from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "MindGuard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    AI_MODEL_STRATEGY: str = "hybrid"  # rule | deep | hybrid
    DEEP_MODEL_CHECKPOINT: str = "models/deep_multimodal_fusion.pt"
    DEEP_MODEL_DEVICE: str = "cpu"  # cpu | cuda
    DEEP_MODEL_ALLOW_RANDOM_INIT: bool = False
    DEEP_MODEL_BLEND_ALPHA: float = 0.65  # used by hybrid strategy, deep weight

    # Security
    SECRET_KEY: str = "cognitive-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database - Use SQLite for local development
    DATABASE_URL: str = "sqlite:///./cognitive.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "cognitive_admin"
    MINIO_SECRET_KEY: str = "cognitive_minio_2026"
    MINIO_BUCKET: str = "cognitive-files"
    MINIO_SECURE: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "https://admin.zhouchao5563.online",
        "https://h5.zhouchao5563.online",
        "https://api.zhouchao5563.online",
        "https://servicewechat.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

    # WeChat subscription message (optional; mock-mode when missing)
    WECHAT_MP_APPID: str = ""
    WECHAT_MP_SECRET: str = ""
    WECHAT_TEMPLATE_ID_ADHERENCE: str = ""
    WECHAT_TEMPLATE_ID_REASSESSMENT: str = ""
    WECHAT_MINIPROGRAM_PAGE: str = "pages/index/index"
    WECHAT_MOCK_MODE: bool = False

    # Reminder scheduling (Celery Beat)
    CELERY_BEAT_ENABLED: bool = True
    CELERY_BEAT_ADHERENCE_INTERVAL_MINUTES: int = 30
    CELERY_BEAT_ADHERENCE_DUE_ONLY: bool = True
    CELERY_BEAT_REASSESSMENT_INTERVAL_MINUTES: int = 120
    CELERY_BEAT_REASSESSMENT_WITHIN_DAYS: int = 7

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("AI_MODEL_STRATEGY", mode="before")
    @classmethod
    def validate_ai_model_strategy(cls, v):
        strategy = str(v).strip().lower()
        if strategy not in {"rule", "deep", "hybrid"}:
            return "hybrid"
        return strategy

    @field_validator("DEEP_MODEL_BLEND_ALPHA", mode="before")
    @classmethod
    def validate_blend_alpha(cls, v):
        try:
            alpha = float(v)
        except (TypeError, ValueError):
            return 0.65
        return max(0.0, min(1.0, alpha))


settings = Settings()
