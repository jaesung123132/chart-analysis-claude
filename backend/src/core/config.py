"""
애플리케이션 설정
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any


class Settings(BaseSettings):
    """환경변수 기반 설정"""

    # 프로젝트 정보
    PROJECT_NAME: str = "ISPAS"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # 데이터베이스 (기본값: SQLite 개발 환경)
    DATABASE_URL: str = "sqlite+aiosqlite:///./ispas.db"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # API 키 (선택적)
    ALPHA_VANTAGE_API_KEY: str = ""
    YAHOO_FINANCE_ENABLED: bool = True

    # CORS - 쉼표 구분 문자열 또는 JSON 배열 모두 허용
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 로깅
    LOG_LEVEL: str = "INFO"

    # 보안
    SECRET_KEY: str = "your-secret-key-change-this-in-production"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parseCorsOrigins(cls, v: Any) -> List[str]:
        """CORS_ORIGINS를 쉼표 구분 문자열 또는 리스트로 파싱"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
