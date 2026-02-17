"""
주가 예측 API 라우터
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import numpy as np
import structlog
from ...schemas.stock import (
    APIResponse,
    PredictionHistoryResponse,
    PredictionHistoryItem,
    PredictionAccuracyResponse,
    AccuracyMetrics
)
from ...services.prediction_service import PredictionService
from ...services.error_correction_service import ErrorCorrectionService
from ...repositories.stock_repository import StockRepository
from ...repositories.prediction_repository import PredictionRepository
from ...infrastructure.database import get_db

logger = structlog.get_logger()

router = APIRouter(prefix="/predictions", tags=["predictions"])

# 예측 서비스 초기화 (모델 로드)
try:
    prediction_service = PredictionService()
except Exception as e:
    logger.error("Failed to initialize prediction service", error=str(e))
    prediction_service = None


@router.get("/health")
async def prediction_health():
    """예측 서비스 상태 확인"""
    is_ready = prediction_service is not None and prediction_service.model is not None

    return APIResponse(
        success=is_ready,
        data={
            "status": "ready" if is_ready else "not_ready",
            "model_loaded": prediction_service.model is not None if prediction_service else False
        },
        message="Prediction service status",
        timestamp=datetime.utcnow()
    )


@router.get("/{ticker}/history")
async def get_prediction_history(
    ticker: str,
    limit: int = Query(default=30, ge=1, le=100, description="조회할 예측 건수"),
    db: AsyncSession = Depends(get_db)
):
    """
    종목의 과거 예측 기록 조회

    - 예측 날짜, 예측 가격, 실제 가격, 오차율 반환
    - actual_price가 없는 항목은 아직 평가 전 (미래 예측)
    """
    ticker = ticker.upper()
    stock_repo = StockRepository(db)
    stock = await stock_repo.get_by_ticker(ticker)

    if stock is None:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {ticker}")

    pred_repo = PredictionRepository(db)
    records = await pred_repo.get_history(stock.id, limit=limit)

    history_items = []
    evaluated_count = 0

    for rec in records:
        error_pct = None
        if rec.actual_price is not None and rec.predicted_price and rec.predicted_price != 0:
            evaluated_count += 1
            error_pct = round(
                (rec.actual_price - rec.predicted_price) / rec.predicted_price * 100, 2
            )

        history_items.append(PredictionHistoryItem(
            id=rec.id,
            target_date=rec.target_date.strftime('%Y-%m-%d'),
            predicted_price=rec.predicted_price,
            actual_price=rec.actual_price,
            error_percent=error_pct
        ))

    return APIResponse(
        success=True,
        data=PredictionHistoryResponse(
            ticker=ticker,
            total_count=len(records),
            evaluated_count=evaluated_count,
            history=history_items
        ),
        message=f"{ticker} 예측 기록 {len(records)}건 조회 완료",
        timestamp=datetime.utcnow()
    )


@router.get("/{ticker}/accuracy")
async def get_prediction_accuracy(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    종목 예측 정확도 분석

    - MAE, MAPE, RMSE, 방향 정확도 반환
    - 실제 가격과 비교 완료된 예측 건만 분석
    """
    ticker = ticker.upper()
    stock_repo = StockRepository(db)
    stock = await stock_repo.get_by_ticker(ticker)

    if stock is None:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {ticker}")

    pred_repo = PredictionRepository(db)
    total_records = await pred_repo.get_history(stock.id, limit=100)
    evaluated_records = await pred_repo.get_evaluated(stock.id, limit=100)

    if len(evaluated_records) < 2:
        correction_service = ErrorCorrectionService()
        correction_info = await correction_service.calculate_correction(db, stock.id)
        return APIResponse(
            success=True,
            data=PredictionAccuracyResponse(
                ticker=ticker,
                total_predictions=len(total_records),
                evaluated_count=len(evaluated_records),
                metrics=AccuracyMetrics(),
                correction_info=correction_info,
                message="예측 기록이 쌓이면 정확도를 분석할 수 있습니다 (최소 2건 필요)"
            ),
            message="데이터 부족",
            timestamp=datetime.utcnow()
        )

    # 정확도 지표 계산
    actuals = np.array([r.actual_price for r in evaluated_records])
    predictions = np.array([r.predicted_price for r in evaluated_records])

    mae = float(np.mean(np.abs(actuals - predictions)))
    mape = float(np.mean(np.abs((actuals - predictions) / actuals)) * 100)
    rmse = float(np.sqrt(np.mean((actuals - predictions) ** 2)))

    # 방향 정확도: 예측 방향(상승/하락)이 실제와 일치하는 비율
    if len(evaluated_records) >= 2:
        sorted_recs = sorted(evaluated_records, key=lambda r: r.target_date)
        correct_dir = 0
        total_dir = len(sorted_recs) - 1

        for i in range(1, len(sorted_recs)):
            pred_dir = sorted_recs[i].predicted_price - sorted_recs[i-1].predicted_price
            actual_dir = sorted_recs[i].actual_price - sorted_recs[i-1].actual_price
            if (pred_dir > 0 and actual_dir > 0) or (pred_dir < 0 and actual_dir < 0):
                correct_dir += 1

        direction_accuracy = round(correct_dir / total_dir * 100, 2) if total_dir > 0 else None
    else:
        direction_accuracy = None

    correction_service = ErrorCorrectionService()
    correction_info = await correction_service.calculate_correction(db, stock.id)

    metrics = AccuracyMetrics(
        mae=round(mae, 4),
        mape=round(mape, 2),
        rmse=round(rmse, 4),
        direction_accuracy=direction_accuracy
    )

    return APIResponse(
        success=True,
        data=PredictionAccuracyResponse(
            ticker=ticker,
            total_predictions=len(total_records),
            evaluated_count=len(evaluated_records),
            metrics=metrics,
            correction_info=correction_info,
            message=f"{len(evaluated_records)}건 평가 완료"
        ),
        message=f"{ticker} 예측 정확도 분석 완료",
        timestamp=datetime.utcnow()
    )


@router.post("/{ticker}/update-actuals")
async def update_actual_prices(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    실제 가격 수동 업데이트

    - target_date가 지났고 actual_price가 없는 예측 조회
    - Yahoo Finance에서 실제 종가 조회 후 업데이트
    """
    ticker = ticker.upper()
    from ...services.stock_data_service import StockDataService

    pred_repo = PredictionRepository(db)
    stock_repo = StockRepository(db)

    stock = await stock_repo.get_by_ticker(ticker)
    if stock is None:
        raise HTTPException(status_code=404, detail=f"종목을 찾을 수 없습니다: {ticker}")

    # target_date가 지났고 actual_price 없는 예측 조회
    pending = await pred_repo.get_pending_actuals()
    pending_for_ticker = [p for p in pending if p.stock_id == stock.id]

    if not pending_for_ticker:
        return APIResponse(
            success=True,
            data={"updated_count": 0},
            message="업데이트할 예측 없음",
            timestamp=datetime.utcnow()
        )

    # 실제 가격 조회 (1년치 데이터로 충분)
    stock_service = StockDataService()
    try:
        df = stock_service.fetch_stock_data(ticker, period='1y')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주가 데이터 조회 실패: {str(e)}")

    updated_count = 0
    for pred in pending_for_ticker:
        target_str = pred.target_date.strftime('%Y-%m-%d')
        # 정확히 해당 날짜가 없으면 가장 가까운 날짜 사용
        try:
            if target_str in df.index.strftime('%Y-%m-%d').tolist():
                actual = float(df.loc[df.index.strftime('%Y-%m-%d') == target_str, 'close'].iloc[0])
            else:
                # 가장 가까운 날짜의 종가 (주말/공휴일 대응)
                target_dt = pred.target_date
                df_sorted = df.copy()
                closest_idx = (df_sorted.index - target_dt).abs().argmin()
                actual = float(df_sorted.iloc[closest_idx]['close'])

            await pred_repo.update_actual(pred.id, actual)
            updated_count += 1
        except Exception as e:
            logger.warning("실제 가격 업데이트 실패", pred_id=pred.id, error=str(e))

    logger.info("실제 가격 수동 업데이트 완료", ticker=ticker, updated_count=updated_count)

    return APIResponse(
        success=True,
        data={"updated_count": updated_count, "pending_count": len(pending_for_ticker)},
        message=f"{updated_count}건 실제 가격 업데이트 완료",
        timestamp=datetime.utcnow()
    )


@router.get("/{ticker}")
async def predict_stock_price(
    ticker: str,
    days: int = Query(default=7, ge=1, le=30, description="예측할 일수 (1-30)"),
    db: AsyncSession = Depends(get_db)
):
    """
    LSTM 모델을 사용한 주가 예측 (DB 저장 + 오차 보정 적용)

    **파라미터:**
    - **ticker**: 종목 코드 (예: AAPL)
    - **days**: 예측할 일수 (기본 7일, 최대 30일)

    **응답:**
    - 현재 가격
    - 원시 예측가 + 보정 예측가
    - 보정 정보 (factor, 데이터 수, 평균 오차율)
    """
    if prediction_service is None:
        raise HTTPException(
            status_code=503,
            detail="Prediction service not available. Model not loaded."
        )

    try:
        result = await prediction_service.predict_and_save(db, ticker.upper(), days=days)

        return APIResponse(
            success=True,
            data=result,
            message=f"{days}일 주가 예측 완료 (DB 저장)",
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error("Prediction failed", ticker=ticker, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"예측 실패: {str(e)}"
        )
