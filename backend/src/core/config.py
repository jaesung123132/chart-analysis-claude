"""
애플리케이션 설정 관리
환경변수를 로드하고 검증하는 Pydantic Settings 클래스
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """애플리케이션 전역 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 데이터베이스
    database_url: str = Field(
        default="postgresql+asyncpg://stock_user:stock_password@localhost:5432/stock_analysis",
        description="PostgreSQL 연결 URL",
    )
    database_echo: bool = Field(default=False, description="SQL 쿼리 로깅 활성화")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis 연결 URL")

    # 외부 API
    alpha_vantage_api_key: str = Field(
        default="", description="Alpha Vantage API 키"
    )
    yahoo_finance_enabled: bool = Field(
        default=True, description="Yahoo Finance API 사용 여부"
    )

    # FastAPI
    api_host: str = Field(default="0.0.0.0", description="API 서버 호스트")
    api_port: int = Field(default=8000, description="API 서버 포트")
    api_reload: bool = Field(default=True, description="핫 리로드 활성화")
    debug: bool = Field(default=True, description="디버그 모드")

    # JWT (선택적)
    secret_key: str = Field(
        default="change-this-secret-key-in-production", description="JWT 시크릿 키"
    )
    algorithm: str = Field(default="HS256", description="JWT 알고리즘")
    access_token_expire_minutes: int = Field(
        default=30, description="액세스 토큰 만료 시간(분)"
    )

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", description="Celery 브로커 URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", description="Celery 결과 백엔드 URL"
    )

    # 로깅
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_format: str = Field(default="json", description="로그 포맷 (json/text)")

    # 모델 설정
    model_weights_path: str = Field(
        default="./models/weights", description="모델 가중치 저장 경로"
    )
    model_checkpoint_dir: str = Field(
        default="./models/checkpoints", description="모델 체크포인트 디렉토리"
    )

    # 백테스팅
    backtest_initial_capital: float = Field(
        default=100000.0, description="백테스팅 초기 자본금"
    )
    backtest_commission: float = Field(default=0.001, description="거래 수수료율")

    # 데이터 수집
    data_update_interval_hours: int = Field(
        default=24, description="데이터 업데이트 주기(시간)"
    )
    stock_symbols: str = Field(
        default="AAPL,GOOGL,MSFT,AMZN,TSLA", description="수집할 종목 심볼 (콤마 구분)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """로그 레벨 검증"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    @property
    def stock_symbols_list(self) -> List[str]:
        """종목 심볼 리스트 반환"""
        return [s.strip() for s in self.stock_symbols.split(",") if s.strip()]


# 전역 설정 인스턴스
settings = Settings()
