"""
주식 데이터 모델 (SQLAlchemy)
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Index, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..infrastructure.database import Base


class Stock(Base):
    """종목 마스터 테이블"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False, comment="종목 코드 (예: AAPL)")
    name = Column(String(200), nullable=False, comment="종목명")
    sector = Column(String(100), comment="섹터")
    industry = Column(String(100), comment="산업")
    market = Column(String(50), default="US", comment="시장 (US, KR 등)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="stock", cascade="all, delete-orphan")


class StockPrice(Base):
    """주가 시계열 데이터 (OHLCV)"""
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True, comment="거래일")
    open = Column(Float, nullable=False, comment="시가")
    high = Column(Float, nullable=False, comment="고가")
    low = Column(Float, nullable=False, comment="저가")
    close = Column(Float, nullable=False, comment="종가")
    volume = Column(Integer, nullable=False, comment="거래량")
    adjusted_close = Column(Float, comment="수정 종가 (배당, 액면분할 조정)")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    stock = relationship("Stock", back_populates="prices")

    # 인덱스: 종목별 날짜 조회 최적화
    __table_args__ = (
        Index("idx_stock_date", "stock_id", "date"),
    )


class TechnicalIndicator(Base):
    """기술적 지표 저장"""
    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    
    # 이동평균선
    sma_20 = Column(Float, comment="20일 단순이동평균")
    sma_50 = Column(Float, comment="50일 단순이동평균")
    sma_200 = Column(Float, comment="200일 단순이동평균")
    ema_12 = Column(Float, comment="12일 지수이동평균")
    ema_26 = Column(Float, comment="26일 지수이동평균")
    
    # 모멘텀 지표
    rsi_14 = Column(Float, comment="14일 RSI")
    macd = Column(Float, comment="MACD")
    macd_signal = Column(Float, comment="MACD 시그널")
    macd_histogram = Column(Float, comment="MACD 히스토그램")
    
    # 변동성 지표
    bb_upper = Column(Float, comment="볼린저 밴드 상단")
    bb_middle = Column(Float, comment="볼린저 밴드 중간")
    bb_lower = Column(Float, comment="볼린저 밴드 하단")
    atr_14 = Column(Float, comment="14일 ATR")
    
    # 거래량 지표
    obv = Column(Float, comment="On-Balance Volume")
    vwap = Column(Float, comment="Volume Weighted Average Price")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    stock = relationship("Stock", back_populates="indicators")

    __table_args__ = (
        Index("idx_indicator_stock_date", "stock_id", "date"),
    )


class Prediction(Base):
    """모델 예측 결과"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    prediction_date = Column(DateTime, nullable=False, comment="예측 생성 시점")
    target_date = Column(DateTime, nullable=False, comment="예측 대상 날짜")
    
    predicted_price = Column(Float, nullable=False, comment="예측 가격")
    actual_price = Column(Float, comment="실제 가격 (결과 확인 후 업데이트)")
    
    model_name = Column(String(50), nullable=False, comment="모델 이름 (lstm, xgboost 등)")
    model_version = Column(String(20), comment="모델 버전")
    confidence_score = Column(Float, comment="신뢰도 점수")
    
    # SHAP values (JSON으로 저장)
    shap_values = Column(Text, comment="SHAP values (JSON)")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    stock = relationship("Stock", back_populates="predictions")

    __table_args__ = (
        Index("idx_prediction_stock_target", "stock_id", "target_date"),
    )
