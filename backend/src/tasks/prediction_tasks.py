"""
예측 관련 Celery 태스크

주요 태스크:
- update_actual_prices_all: 전체 종목 실제 가격 자동 업데이트
"""
import asyncio
import structlog
from . import celery_app

logger = structlog.get_logger()


def _run_async(coro):
    """동기 Celery 태스크에서 비동기 코루틴 실행"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _do_update_actual_prices():
    """
    실제 가격 업데이트 비동기 로직

    1. 전체 pending 예측 조회 (target_date <= 오늘, actual_price IS NULL)
    2. 종목별로 그룹화
    3. Yahoo Finance에서 실제 종가 조회
    4. DB 업데이트
    """
    from ..infrastructure.database import AsyncSessionLocal
    from ..repositories.prediction_repository import PredictionRepository
    from ..repositories.stock_repository import StockRepository
    from ..services.stock_data_service import StockDataService

    async with AsyncSessionLocal() as db:
        try:
            pred_repo = PredictionRepository(db)
            stock_repo = StockRepository(db)
            stock_service = StockDataService()

            # 전체 pending 예측 조회
            pending = await pred_repo.get_pending_actuals()

            if not pending:
                logger.info("업데이트할 실제 가격 없음")
                return {"updated_count": 0, "skipped_count": 0}

            # 종목 ID별로 그룹화
            stock_ids = list(set(p.stock_id for p in pending))
            logger.info("실제 가격 업데이트 시작", total_pending=len(pending), stocks=len(stock_ids))

            updated_count = 0
            skipped_count = 0

            for stock_id in stock_ids:
                # 해당 종목의 Stock 정보 조회
                from sqlalchemy import select
                from ..models.stock import Stock
                result = await db.execute(select(Stock).where(Stock.id == stock_id))
                stock = result.scalar_one_or_none()

                if stock is None:
                    skipped_count += len([p for p in pending if p.stock_id == stock_id])
                    continue

                # 해당 종목의 pending 예측
                ticker_pending = [p for p in pending if p.stock_id == stock_id]

                try:
                    df = stock_service.fetch_stock_data(stock.ticker, period='1y')
                    df_dates = df.index.strftime('%Y-%m-%d').tolist()

                    for pred in ticker_pending:
                        target_str = pred.target_date.strftime('%Y-%m-%d')
                        try:
                            if target_str in df_dates:
                                actual = float(df.loc[
                                    df.index.strftime('%Y-%m-%d') == target_str, 'close'
                                ].iloc[0])
                            else:
                                # 가장 가까운 날짜 (주말/공휴일 대응)
                                target_dt = pred.target_date
                                closest_idx = (df.index - target_dt).abs().argmin()
                                actual = float(df.iloc[closest_idx]['close'])

                            await pred_repo.update_actual(pred.id, actual)
                            updated_count += 1
                        except Exception as e:
                            logger.warning(
                                "개별 예측 업데이트 실패",
                                pred_id=pred.id,
                                ticker=stock.ticker,
                                error=str(e)
                            )
                            skipped_count += 1

                except Exception as e:
                    logger.error(
                        "종목 실제 가격 조회 실패",
                        ticker=stock.ticker,
                        error=str(e)
                    )
                    skipped_count += len(ticker_pending)

            await db.commit()
            logger.info(
                "실제 가격 업데이트 완료",
                updated_count=updated_count,
                skipped_count=skipped_count
            )
            return {"updated_count": updated_count, "skipped_count": skipped_count}

        except Exception as e:
            await db.rollback()
            logger.error("실제 가격 업데이트 중 오류", error=str(e))
            raise


@celery_app.task(name="backend.src.tasks.prediction_tasks.update_actual_prices_all")
def update_actual_prices_all():
    """
    [Celery Beat 스케줄 태스크]
    전체 종목의 실제 가격을 자동 업데이트

    - 매일 주기적으로 실행 (beat_schedule 설정 기준)
    - target_date가 지났고 actual_price가 없는 예측 모두 처리
    """
    logger.info("Celery: 실제 가격 자동 업데이트 태스크 시작")
    result = _run_async(_do_update_actual_prices())
    logger.info("Celery: 실제 가격 자동 업데이트 완료", result=result)
    return result
