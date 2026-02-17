"""
주식 관련 API 라우터
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from ...schemas.stock import APIResponse, BatchPriceRequest, BatchPriceItem
from ...services.stock_data_service import StockDataService
from ...core.exceptions import StockNotFoundException, DataFetchException
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/stocks", tags=["stocks"])
stock_service = StockDataService()


@router.get("/{ticker}/prices")
async def get_stock_prices(
    ticker: str,
    period: str = Query(default="1y", description="조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y)"),
    interval: str = Query(default="1d", description="데이터 간격 (1d, 1wk, 1mo)")
):
    """
    종목의 주가 데이터 조회
    
    - **ticker**: 종목 코드 (예: AAPL, MSFT, TSLA)
    - **period**: 조회 기간
    - **interval**: 데이터 간격
    """
    try:
        df = stock_service.fetch_stock_data(ticker.upper(), period, interval)
        
        # DataFrame을 JSON으로 변환
        data = []
        for date, row in df.iterrows():
            data.append({
                "date": date.isoformat(),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": int(row.get("volume", 0)),
            })
        
        return APIResponse(
            success=True,
            data={
                "ticker": ticker.upper(),
                "period": period,
                "interval": interval,
                "count": len(data),
                "prices": data
            },
            message="주가 데이터 조회 성공",
            timestamp=datetime.utcnow()
        )
        
    except StockNotFoundException as e:
        logger.warning("종목 없음", ticker=ticker)
        raise HTTPException(status_code=404, detail=str(e))
    except DataFetchException as e:
        logger.error("데이터 조회 실패", ticker=ticker, error=str(e))
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("예상치 못한 오류", ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.get("/{ticker}/info")
async def get_stock_info(ticker: str):
    """
    종목 상세 정보 조회
    
    - **ticker**: 종목 코드
    """
    try:
        info = stock_service.get_stock_info(ticker.upper())
        
        return APIResponse(
            success=True,
            data=info,
            message="종목 정보 조회 성공",
            timestamp=datetime.utcnow()
        )
        
    except DataFetchException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("예상치 못한 오류", ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail="내부 서버 오류")


@router.post("/batch-prices")
async def get_batch_prices(request: BatchPriceRequest):
    """
    여러 종목의 가격 정보 일괄 조회 (즐겨찾기용)

    - **tickers**: 종목 코드 리스트
    - **period**: 조회 기간 (기본값: 5d)
    """
    try:
        # 기존 fetch_multiple_stocks 메서드 활용
        stocks_data = stock_service.fetch_multiple_stocks(
            [ticker.upper() for ticker in request.tickers],
            request.period
        )

        results = []
        for ticker, df in stocks_data.items():
            if df.empty:
                logger.warning("데이터 없음", ticker=ticker)
                continue

            # 최신 가격 (현재가)
            latest = df.iloc[-1]
            current_price = float(latest.get("close", 0))

            # 전일 종가
            previous_close = float(df.iloc[-2].get("close", current_price)) if len(df) > 1 else current_price

            # 변동률 및 변동액
            change_amount = current_price - previous_close
            change_percent = (change_amount / previous_close * 100) if previous_close > 0 else 0

            # 최근 N일 종가 데이터
            prices = []
            for date, row in df.iterrows():
                prices.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "close": float(row.get("close", 0))
                })

            results.append({
                "ticker": ticker,
                "currentPrice": current_price,
                "previousClose": previous_close,
                "changePercent": round(change_percent, 2),
                "changeAmount": round(change_amount, 2),
                "prices": prices
            })

        return APIResponse(
            success=True,
            data={"stocks": results},
            message=f"{len(results)}개 종목 가격 조회 완료",
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error("batch-prices 조회 실패", error=str(e))
        raise HTTPException(status_code=500, detail=f"가격 조회 실패: {str(e)}")


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return APIResponse(
        success=True,
        data={"status": "healthy"},
        message="Stock API is running",
        timestamp=datetime.utcnow()
    )
