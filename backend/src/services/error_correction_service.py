"""
예측 오차 보정 서비스
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import numpy as np
import structlog
from ..repositories.prediction_repository import PredictionRepository

logger = structlog.get_logger()

MIN_DATA_POINTS = 5  # 최소 데이터 수 (미만이면 보정 없음)


class ErrorCorrectionService:
    """과거 예측 오차를 분석하여 보정 계수 계산"""

    async def calculate_correction(
        self,
        db: AsyncSession,
        stock_id: int,
        lookback: int = 30
    ) -> dict:
        """
        최근 N건의 과거 예측 오차를 분석하여 보정 계수 반환

        Returns:
            {
                "factor": float,        # 보정 계수 (0이면 보정 없음)
                "data_count": int,      # 분석에 사용된 데이터 수
                "avg_error_pct": float, # 평균 오차율 (%)
                "is_corrected": bool    # 보정 적용 여부
            }
        """
        repo = PredictionRepository(db)
        evaluated = await repo.get_evaluated(stock_id, limit=lookback)

        if len(evaluated) < MIN_DATA_POINTS:
            logger.info(
                "오차 보정 데이터 부족 - 보정 없음",
                stock_id=stock_id,
                data_count=len(evaluated),
                min_required=MIN_DATA_POINTS
            )
            return {
                "factor": 0.0,
                "data_count": len(evaluated),
                "avg_error_pct": 0.0,
                "is_corrected": False
            }

        # 오차율 계산: (actual - predicted) / predicted
        error_ratios = []
        for pred in evaluated:
            if pred.predicted_price and pred.predicted_price != 0:
                ratio = (pred.actual_price - pred.predicted_price) / pred.predicted_price
                error_ratios.append(ratio)

        if not error_ratios:
            return {"factor": 0.0, "data_count": 0, "avg_error_pct": 0.0, "is_corrected": False}

        # 가중 이동평균 (최근 예측에 더 높은 가중치)
        weights = np.linspace(1, 2, len(error_ratios))  # 1 ~ 2 선형 증가
        weighted_factor = float(np.average(error_ratios, weights=weights))
        avg_error_pct = float(np.mean(np.abs(error_ratios)) * 100)

        logger.info(
            "오차 보정 계수 계산",
            stock_id=stock_id,
            data_count=len(error_ratios),
            correction_factor=round(weighted_factor, 4),
            avg_error_pct=round(avg_error_pct, 2)
        )

        return {
            "factor": round(weighted_factor, 4),
            "data_count": len(error_ratios),
            "avg_error_pct": round(avg_error_pct, 2),
            "is_corrected": True
        }

    def apply_correction(self, predicted_price: float, correction_info: dict) -> float:
        """보정 계수를 적용하여 보정된 예측가 반환"""
        if not correction_info.get("is_corrected"):
            return predicted_price
        factor = correction_info.get("factor", 0.0)
        return round(predicted_price * (1 + factor), 4)
