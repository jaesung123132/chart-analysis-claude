"""
주식 데이터 수집 서비스
"""
from typing import List, Dict
import pandas as pd
from datetime import datetime
import structlog
from ..infrastructure.api_clients.yahoo_finance import YahooFinanceClient
from ..core.exceptions import DataFetchException, StockNotFoundException

logger = structlog.get_logger()


class StockDataService:
    """주식 데이터 수집 및 처리 서비스"""
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
    
    def fetch_stock_data(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        주식 데이터 조회
        
        Args:
            ticker: 종목 코드
            period: 조회 기간
            interval: 데이터 간격
        
        Returns:
            OHLCV DataFrame
        """
        try:
            df = self.yahoo_client.get_historical_data(ticker, period, interval)
            
            if df.empty:
                raise StockNotFoundException(ticker)
            
            # 컬럼명 표준화
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            logger.info(
                "주가 데이터 조회 완료",
                ticker=ticker,
                rows=len(df),
                start_date=df.index[0] if not df.empty else None,
                end_date=df.index[-1] if not df.empty else None
            )
            
            return df
            
        except StockNotFoundException:
            raise
        except Exception as e:
            logger.error("데이터 조회 실패", ticker=ticker, error=str(e))
            raise DataFetchException(str(e), {"ticker": ticker})
    
    def get_stock_info(self, ticker: str) -> Dict:
        """종목 정보 조회"""
        try:
            info = self.yahoo_client.get_stock_info(ticker)
            
            # 필요한 필드만 추출
            return {
                "ticker": ticker,
                "name": info.get("longName", info.get("shortName", ticker)),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
            }
            
        except Exception as e:
            logger.error("종목 정보 조회 실패", ticker=ticker, error=str(e))
            raise DataFetchException(str(e), {"ticker": ticker})
    
    def fetch_multiple_stocks(
        self,
        tickers: List[str],
        period: str = "5y"
    ) -> Dict[str, pd.DataFrame]:
        """여러 종목 데이터 조회"""
        return self.yahoo_client.get_multiple_stocks(tickers, period)
