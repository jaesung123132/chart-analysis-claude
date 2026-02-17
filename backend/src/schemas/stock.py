"""
Stock DTO (Pydantic 스키마)
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any


class StockBase(BaseModel):
    """종목 기본 스키마"""
    ticker: str = Field(..., description="종목 코드", example="AAPL")
    name: str = Field(..., description="종목명", example="Apple Inc.")
    sector: Optional[str] = Field(None, description="섹터")
    industry: Optional[str] = Field(None, description="산업")
    market: str = Field(default="US", description="시장")


class StockCreate(StockBase):
    """종목 생성 요청"""
    pass


class StockResponse(StockBase):
    """종목 응답"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockPriceResponse(BaseModel):
    """주가 데이터 응답"""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    
    class Config:
        from_attributes = True


class BatchPriceRequest(BaseModel):
    """즐겨찾기 다중 종목 가격 조회 요청"""
    tickers: List[str] = Field(..., description="종목 코드 리스트", example=["AAPL", "TSLA"])
    period: str = Field(default="5d", description="조회 기간", example="5d")


class BatchPriceItem(BaseModel):
    """개별 종목 가격 정보"""
    ticker: str
    currentPrice: float
    previousClose: float
    changePercent: float
    changeAmount: float
    prices: List[dict]  # 최근 N일 종가 데이터


class PredictionHistoryItem(BaseModel):
    """과거 예측 기록 항목"""
    id: int
    target_date: str
    predicted_price: float
    actual_price: Optional[float] = None
    error_percent: Optional[float] = None  # (actual - predicted) / predicted * 100

    class Config:
        from_attributes = True


class PredictionHistoryResponse(BaseModel):
    """예측 기록 응답"""
    ticker: str
    total_count: int
    evaluated_count: int  # actual_price가 있는 건수
    history: List[PredictionHistoryItem]


class AccuracyMetrics(BaseModel):
    """예측 정확도 지표"""
    mae: Optional[float] = None         # 평균 절대 오차
    mape: Optional[float] = None        # 평균 절대 백분율 오차 (%)
    rmse: Optional[float] = None        # 평균 제곱근 오차
    direction_accuracy: Optional[float] = None  # 방향 정확도 (%)


class PredictionAccuracyResponse(BaseModel):
    """예측 정확도 응답"""
    ticker: str
    total_predictions: int
    evaluated_count: int
    metrics: AccuracyMetrics
    correction_info: Optional[dict] = None
    message: str


class APIResponse(BaseModel):
    """표준 API 응답 형식"""
    success: bool
    data: Optional[Any] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
