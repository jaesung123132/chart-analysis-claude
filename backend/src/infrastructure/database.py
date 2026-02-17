"""
데이터베이스 연결 및 세션 관리
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 DATABASE_URL 가져오기 (기본값: SQLite 개발 환경)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ispas.db")

# SQLite 여부 판별 (SQLite는 pool_size, max_overflow 미지원)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# 비동기 엔진 생성
if IS_SQLITE:
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base 클래스 (모든 모델이 상속)
Base = declarative_base()


# 의존성 주입용 세션 제공 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입을 위한 DB 세션 제공
    
    사용 예:
    @app.get("/stocks")
    async def get_stocks(db: AsyncSession = Depends(get_db)):
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
