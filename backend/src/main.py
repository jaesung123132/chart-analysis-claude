"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .api.routers import stocks, indicators, predictions, search
from .infrastructure.database import engine, Base
from .models import stock as stock_models  # 모델 임포트 (테이블 등록)
import structlog

# 구조화된 로깅 설정
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# FastAPI 앱 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Stock Price Analysis System - 주가 예측 AI 시스템",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stocks.router, prefix=settings.API_V1_PREFIX)
app.include_router(indicators.router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 이벤트 - DB 테이블 자동 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("ISPAS API 서버 시작", version=settings.VERSION)
    logger.info("DB 테이블 자동 생성 완료")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 이벤트"""
    logger.info("ISPAS API 서버 종료")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "ISPAS API Server",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/stocks/health"
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy", "service": "ispas-api"}
