"""
기술적 지표 계산 서비스 (Feature Engineering)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()


class FeatureEngineeringService:
    """기술적 지표 계산 서비스"""
    
    def __init__(self):
        logger.info("FeatureEngineeringService 초기화")
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        모든 기술적 지표를 한 번에 계산
        
        Args:
            df: OHLCV 데이터 (columns: open, high, low, close, volume)
        
        Returns:
            기술적 지표가 추가된 DataFrame
        """
        result = df.copy()
        
        # 추세 지표
        result = self._add_moving_averages(result)
        result = self._add_macd(result)
        
        # 모멘텀 지표
        result = self._add_rsi(result)
        result = self._add_stochastic(result)
        
        # 변동성 지표
        result = self._add_bollinger_bands(result)
        result = self._add_atr(result)
        
        # 거래량 지표
        result = self._add_obv(result)
        result = self._add_vwap(result)
        
        logger.info("모든 기술적 지표 계산 완료", indicators=len(result.columns) - len(df.columns))
        return result
    
    # ========== 추세 지표 (Trend Indicators) ==========
    
    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """이동평균선 추가 (SMA, EMA)"""
        df = df.copy()
        
        # SMA (Simple Moving Average)
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # EMA (Exponential Moving Average)
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        return df
    
    def _add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """MACD (Moving Average Convergence Divergence)"""
        df = df.copy()
        
        # MACD Line = 12-day EMA - 26-day EMA
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        
        # Signal Line = 9-day EMA of MACD
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Histogram = MACD - Signal
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        return df
    
    # ========== 모멘텀 지표 (Momentum Indicators) ==========
    
    def _add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """RSI (Relative Strength Index)"""
        df = df.copy()
        
        # 가격 변화
        delta = df['close'].diff()
        
        # 상승/하락 분리
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 평균 상승/하락
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # RS = Average Gain / Average Loss
        rs = avg_gain / avg_loss
        
        # RSI = 100 - (100 / (1 + RS))
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        return df
    
    def _add_stochastic(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Stochastic Oscillator"""
        df = df.copy()
        
        # %K = (현재가 - 최저가) / (최고가 - 최저가) * 100
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        
        df['stoch_k'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
        
        # %D = %K의 3일 이동평균
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        return df
    
    # ========== 변동성 지표 (Volatility Indicators) ==========
    
    def _add_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """Bollinger Bands"""
        df = df.copy()
        
        # 중간선 (SMA)
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        
        # 표준편차
        std = df['close'].rolling(window=period).std()
        
        # 상단/하단 밴드
        df['bb_upper'] = df['bb_middle'] + (std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (std * std_dev)
        
        # 밴드 폭 (선택적)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        return df
    
    def _add_atr(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """ATR (Average True Range)"""
        df = df.copy()
        
        # True Range 계산
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR = True Range의 이동평균
        df['atr_14'] = true_range.rolling(window=period).mean()
        
        return df
    
    # ========== 거래량 지표 (Volume Indicators) ==========
    
    def _add_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """OBV (On-Balance Volume)"""
        df = df.copy()
        
        # 가격 방향
        direction = np.where(df['close'] > df['close'].shift(), 1, -1)
        direction[0] = 0  # 첫 번째 값
        
        # OBV = 누적 (거래량 * 방향)
        df['obv'] = (df['volume'] * direction).cumsum()
        
        return df
    
    def _add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """VWAP (Volume Weighted Average Price)"""
        df = df.copy()
        
        # Typical Price = (High + Low + Close) / 3
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # VWAP = Σ(Typical Price * Volume) / Σ(Volume)
        df['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        return df
    
    # ========== 유틸리티 ==========
    
    def get_indicator_summary(self, df: pd.DataFrame, ticker: str) -> Dict:
        """
        최신 지표 값 요약
        
        Returns:
            최신 지표 값 딕셔너리
        """
        latest = df.iloc[-1]
        
        return {
            "ticker": ticker,
            "date": str(latest.name),
            "price": {
                "close": float(latest['close']),
                "sma_20": float(latest.get('sma_20', np.nan)),
                "sma_50": float(latest.get('sma_50', np.nan)),
                "sma_200": float(latest.get('sma_200', np.nan)),
            },
            "momentum": {
                "rsi_14": float(latest.get('rsi_14', np.nan)),
                "stoch_k": float(latest.get('stoch_k', np.nan)),
                "stoch_d": float(latest.get('stoch_d', np.nan)),
            },
            "trend": {
                "macd": float(latest.get('macd', np.nan)),
                "macd_signal": float(latest.get('macd_signal', np.nan)),
                "macd_histogram": float(latest.get('macd_histogram', np.nan)),
            },
            "volatility": {
                "bb_upper": float(latest.get('bb_upper', np.nan)),
                "bb_middle": float(latest.get('bb_middle', np.nan)),
                "bb_lower": float(latest.get('bb_lower', np.nan)),
                "atr_14": float(latest.get('atr_14', np.nan)),
            },
            "volume": {
                "obv": float(latest.get('obv', np.nan)),
                "vwap": float(latest.get('vwap', np.nan)),
            }
        }
