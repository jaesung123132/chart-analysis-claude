"""
StockDataService 테스트
"""
import pytest
from src.services.stock_data_service import StockDataService
from src.core.exceptions import StockNotFoundException, DataFetchException


class TestStockDataService:
    """StockDataService 테스트"""
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.service = StockDataService()
    
    def test_fetch_stock_data_success(self):
        """주가 데이터 조회 성공 테스트"""
        # Given
        ticker = "AAPL"
        
        # When
        df = self.service.fetch_stock_data(ticker, period="1mo")
        
        # Then
        assert not df.empty, "데이터가 있어야 합니다"
        assert len(df) > 0, "최소 1개 이상의 행이 있어야 합니다"
    
    def test_fetch_stock_data_invalid_ticker(self):
        """잘못된 종목 코드 테스트"""
        # Given
        invalid_ticker = "INVALIDTICKER12345"
        
        # When & Then
        with pytest.raises(StockNotFoundException):
            self.service.fetch_stock_data(invalid_ticker, period="1mo")
    
    def test_get_stock_info_success(self):
        """종목 정보 조회 성공 테스트"""
        # Given
        ticker = "AAPL"
        
        # When
        info = self.service.get_stock_info(ticker)
        
        # Then
        assert isinstance(info, dict), "결과는 딕셔너리여야 합니다"
        assert "ticker" in info, "ticker 필드가 있어야 합니다"
        assert info["ticker"] == ticker, "ticker가 일치해야 합니다"
    
    def test_fetch_multiple_stocks(self):
        """여러 종목 조회 테스트"""
        # Given
        tickers = ["AAPL", "MSFT"]
        
        # When
        result = self.service.fetch_multiple_stocks(tickers, period="1mo")
        
        # Then
        assert isinstance(result, dict), "결과는 딕셔너리여야 합니다"
        assert len(result) == 2, "2개 종목의 데이터가 있어야 합니다"
