"""
예측(Prediction) 리포지토리
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from datetime import datetime
from typing import List
from ..models.stock import Prediction
import structlog

logger = structlog.get_logger()


class PredictionRepository:
    """예측 결과 CRUD"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_batch(self, predictions: List[Prediction]) -> List[Prediction]:
        """여러 예측 일괄 저장"""
        for pred in predictions:
            self.db.add(pred)
        await self.db.flush()
        logger.info("예측 저장 완료", count=len(predictions))
        return predictions

    async def get_history(self, stock_id: int, limit: int = 30) -> List[Prediction]:
        """종목별 과거 예측 기록 조회 (최신순)"""
        result = await self.db.execute(
            select(Prediction)
            .where(Prediction.stock_id == stock_id)
            .order_by(Prediction.prediction_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_pending_actuals(self) -> List[Prediction]:
        """actual_price가 없고 target_date가 지난 예측 조회"""
        today = datetime.utcnow()
        result = await self.db.execute(
            select(Prediction)
            .where(
                and_(
                    Prediction.actual_price.is_(None),
                    Prediction.target_date <= today
                )
            )
            .order_by(Prediction.target_date.asc())
            .limit(100)
        )
        return result.scalars().all()

    async def update_actual(self, prediction_id: int, actual_price: float):
        """실제 가격 업데이트"""
        await self.db.execute(
            update(Prediction)
            .where(Prediction.id == prediction_id)
            .values(actual_price=actual_price)
        )
        logger.info("실제 가격 업데이트", prediction_id=prediction_id, actual_price=actual_price)

    async def get_evaluated(self, stock_id: int, limit: int = 30) -> List[Prediction]:
        """actual_price가 있는 예측만 조회 (정확도 분석용, 최신순)"""
        result = await self.db.execute(
            select(Prediction)
            .where(
                and_(
                    Prediction.stock_id == stock_id,
                    Prediction.actual_price.is_not(None)
                )
            )
            .order_by(Prediction.target_date.desc())
            .limit(limit)
        )
        return result.scalars().all()
