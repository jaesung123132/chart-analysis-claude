"""
FastAPI 메인 애플리케이션
엔드포인트 라우터, 미들웨어, 예외 핸들러 등록
"""
from datetime import datetime
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.exceptions import APIException
from src.infrastructure.database import close_db, init_db

# FastAPI 앱 생성
app = FastAPI(
    title="주가 예측 시스템 API",
    description="고정밀 주가 예측 및 백테스팅 시스템",
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 애플리케이션 시작/종료 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    print(f"🚀 서버 시작: {settings.api_host}:{settings.api_port}")
    print(f"📊 데이터베이스: {settings.database_url.split('@')[-1]}")  # 보안을 위해 호스트만 출력
    # await init_db()  # 개발용 (프로덕션에서는 Alembic 사용)


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    print("👋 서버 종료 중...")
    await close_db()


# 전역 예외 핸들러
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """커스텀 API 예외 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "message": "내부 서버 오류가 발생했습니다.",
            "details": {"error": str(exc)} if settings.debug else {},
            "timestamp": datetime.now().isoformat(),
        },
    )


# 헬스 체크 엔드포인트
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """서버 상태 확인"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "0.1.0",
            "environment": "development" if settings.debug else "production",
        },
        "message": "서버가 정상적으로 작동 중입니다.",
        "timestamp": datetime.now().isoformat(),
    }


# 루트 엔드포인트
@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """API 루트"""
    return {
        "success": True,
        "data": {
            "message": "주가 예측 시스템 API",
            "docs": "/docs",
            "redoc": "/redoc",
        },
        "message": "API에 오신 것을 환영합니다.",
        "timestamp": datetime.now().isoformat(),
    }


# 라우터 등록 (추후 추가)
# from src.api.routers import stocks, predictions, backtest
# app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
# app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
# app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
