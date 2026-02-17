"""
Yahoo Finance API 클라이언트 (yfinance 사용)
"""
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import structlog

logger = structlog.get_logger()


class YahooFinanceClient:
    """Yahoo Finance 비동기 클라이언트 (yfinance 기반)"""
    
    def __init__(self):
        logger.info("YahooFinanceClient 초기화 완료")
    
    def get_historical_data(
        self,
        symbol: str,
        period: str = "5y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        과거 주가 데이터 조회
        
        Args:
            symbol: 종목 코드 (예: AAPL)
            period: 조회 기간 ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: 데이터 간격 ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning("데이터 없음", symbol=symbol, period=period)
                return pd.DataFrame()
            
            logger.info(
                "Yahoo Finance 데이터 조회 성공",
                symbol=symbol,
                rows=len(df),
                period=period
            )
            return df
            
        except Exception as e:
            logger.error("Yahoo Finance 데이터 조회 실패", symbol=symbol, error=str(e))
            raise
    
    def get_stock_info(self, symbol: str) -> Dict:
        """
        종목 상세 정보 조회
        
        Returns:
            종목 정보 딕셔너리 (sector, industry, marketCap 등)
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            logger.info("종목 정보 조회 성공", symbol=symbol)
            return info
            
        except Exception as e:
            logger.error("종목 정보 조회 실패", symbol=symbol, error=str(e))
            raise
    
    def get_multiple_stocks(
        self,
        symbols: List[str],
        period: str = "5y",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 데이터를 한 번에 조회
        
        Args:
            symbols: 종목 코드 리스트
            period: 조회 기간
            interval: 데이터 간격
        
        Returns:
            {symbol: DataFrame} 딕셔너리
        """
        result = {}
        for symbol in symbols:
            try:
                df = self.get_historical_data(symbol, period, interval)
                result[symbol] = df
            except Exception as e:
                logger.error("종목 조회 실패", symbol=symbol, error=str(e))
                result[symbol] = pd.DataFrame()
        
        return result
