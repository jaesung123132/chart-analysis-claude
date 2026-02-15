"""
데이터베이스 연결 및 세션 관리
SQLAlchemy 2.x async 엔진 및 세션 설정
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from src.core.config import settings

# Base 클래스 생성 (모든 모델의 기본 클래스)
Base = declarative_base()

# 비동기 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,  # SQL 로깅
    poolclass=NullPool,  # 연결 풀 비활성화 (개발용, 프로덕션에서는 제거)
    future=True,
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입용 DB 세션 생성기

    사용 예:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    데이터베이스 초기화
    테이블 생성 (개발용, 프로덕션에서는 Alembic 사용)
    """
    async with engine.begin() as conn:
        # 모든 테이블 생성
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """데이터베이스 연결 종료"""
    await engine.dispose()
