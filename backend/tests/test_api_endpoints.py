"""
API 엔드포인트 통합 테스트
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestStockEndpoints:
    """Stock API 엔드포인트 테스트"""
    
    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        # When
        response = client.get("/")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_endpoint(self):
        """헬스 체크 엔드포인트 테스트"""
        # When
        response = client.get("/health")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_stock_health_endpoint(self):
        """Stock API 헬스 체크 테스트"""
        # When
        response = client.get("/api/v1/stocks/health")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_stock_prices_success(self):
        """주가 조회 성공 테스트"""
        # Given
        ticker = "AAPL"
        
        # When
        response = client.get(f"/api/v1/stocks/{ticker}/prices?period=1mo")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["ticker"] == ticker
        assert "prices" in data["data"]
        assert len(data["data"]["prices"]) > 0
    
    def test_get_stock_prices_with_params(self):
        """파라미터를 포함한 주가 조회 테스트"""
        # Given
        ticker = "MSFT"
        period = "3mo"
        interval = "1d"
        
        # When
        response = client.get(
            f"/api/v1/stocks/{ticker}/prices",
            params={"period": period, "interval": interval}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["period"] == period
        assert data["data"]["interval"] == interval
    
    def test_get_stock_info_success(self):
        """종목 정보 조회 성공 테스트"""
        # Given
        ticker = "AAPL"
        
        # When
        response = client.get(f"/api/v1/stocks/{ticker}/info")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["ticker"] == ticker
    
    def test_get_stock_prices_invalid_ticker(self):
        """존재하지 않는 종목 조회 테스트"""
        # Given
        invalid_ticker = "INVALIDTICKER12345"
        
        # When
        response = client.get(f"/api/v1/stocks/{invalid_ticker}/prices")
        
        # Then
        assert response.status_code == 404
    
    def test_api_response_format(self):
        """API 응답 형식 검증"""
        # When
        response = client.get("/api/v1/stocks/AAPL/prices?period=1mo")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        
        # 표준 응답 형식 검증
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "timestamp" in data
