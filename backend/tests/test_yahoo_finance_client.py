"""
Yahoo Finance 클라이언트 테스트
"""
import pytest
from src.infrastructure.api_clients.yahoo_finance import YahooFinanceClient


class TestYahooFinanceClient:
    """YahooFinanceClient 테스트"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.client = YahooFinanceClient()
    
    def test_get_historical_data_success(self):
        """정상적인 주가 데이터 조회 테스트"""
        # Given
        symbol = "AAPL"
        period = "1mo"
        
        # When
        df = self.client.get_historical_data(symbol, period)
        
        # Then
        assert not df.empty, "데이터가 비어있으면 안 됩니다"
        assert len(df) > 0, "최소 1개 이상의 데이터가 있어야 합니다"
        assert "Close" in df.columns or "close" in df.columns, "Close 컬럼이 있어야 합니다"
        assert "Volume" in df.columns or "volume" in df.columns, "Volume 컬럼이 있어야 합니다"
    
    def test_get_historical_data_invalid_symbol(self):
        """존재하지 않는 종목 조회 테스트"""
        # Given
        invalid_symbol = "INVALIDticker123456"
        
        # When
        df = self.client.get_historical_data(invalid_symbol, "1mo")
        
        # Then
        assert df.empty, "잘못된 종목은 빈 DataFrame을 반환해야 합니다"
    
    def test_get_stock_info_success(self):
        """종목 정보 조회 테스트"""
        # Given
        symbol = "AAPL"
        
        # When
        info = self.client.get_stock_info(symbol)
        
        # Then
        assert isinstance(info, dict), "정보는 딕셔너리여야 합니다"
        assert "symbol" in info or "ticker" in info, "종목 코드 정보가 있어야 합니다"
    
    def test_get_multiple_stocks(self):
        """여러 종목 동시 조회 테스트"""
        # Given
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        # When
        result = self.client.get_multiple_stocks(symbols, period="1mo")
        
        # Then
        assert isinstance(result, dict), "결과는 딕셔너리여야 합니다"
        assert len(result) == 3, "3개 종목의 데이터가 있어야 합니다"
        for symbol in symbols:
            assert symbol in result, f"{symbol} 데이터가 있어야 합니다"
