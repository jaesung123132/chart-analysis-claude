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

    # 밴드 폭
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

  # ========== 캔들 패턴 인식 ==========

  def _detect_candle_patterns(self, df: pd.DataFrame) -> list:
    """
    최근 캔들 패턴 인식

    Returns:
      감지된 패턴 리스트
    """
    patterns = []
    if len(df) < 3:
      return patterns

    recent = df.tail(10)

    for i in range(len(recent)):
      row = recent.iloc[i]
      date = str(row.name.date()) if hasattr(row.name, 'date') else str(row.name)
      o, h, l, c = row['open'], row['high'], row['low'], row['close']
      body = abs(c - o)
      total_range = h - l

      if total_range == 0:
        continue

      body_ratio = body / total_range

      # 도지 (Doji): body가 전체 range의 10% 미만
      if body_ratio < 0.1:
        patterns.append({
          'date': date,
          'pattern': 'doji',
          'pattern_kr': '도지 (Doji)',
          'signal': 'reversal',
          'description': '시가와 종가가 거의 같아 추세 전환 가능성을 나타냅니다.'
        })

      # 망치형 (Hammer): 하단 꼬리가 body의 2배 이상, 하락 추세 바닥에서 반전 신호
      lower_shadow = min(o, c) - l
      upper_shadow = h - max(o, c)
      if body > 0 and lower_shadow >= body * 2 and upper_shadow <= body * 0.5:
        patterns.append({
          'date': date,
          'pattern': 'hammer',
          'pattern_kr': '망치형 (Hammer)',
          'signal': 'bullish',
          'description': '하락 추세에서 반등 가능성을 나타내는 상승 반전 신호입니다.'
        })

      # 역망치형 (Inverted Hammer): 상단 꼬리가 body의 2배 이상
      if body > 0 and upper_shadow >= body * 2 and lower_shadow <= body * 0.5:
        patterns.append({
          'date': date,
          'pattern': 'inverted_hammer',
          'pattern_kr': '역망치형 (Inverted Hammer)',
          'signal': 'bullish',
          'description': '하락 추세에서 매수세 유입 가능성을 나타냅니다.'
        })

      # 장악형 (Engulfing): 전일 body를 완전히 감싸는 패턴
      if i > 0:
        prev = recent.iloc[i - 1]
        prev_o, prev_c = prev['open'], prev['close']
        prev_body = abs(prev_c - prev_o)

        # 상승 장악형 (Bullish Engulfing)
        if prev_c < prev_o and c > o and body > prev_body * 1.1:
          if o <= prev_c and c >= prev_o:
            patterns.append({
              'date': date,
              'pattern': 'bullish_engulfing',
              'pattern_kr': '상승 장악형 (Bullish Engulfing)',
              'signal': 'bullish',
              'description': '전일 하락 캔들을 완전히 감싸는 상승 캔들로, 강한 상승 반전 신호입니다.'
            })

        # 하락 장악형 (Bearish Engulfing)
        if prev_c > prev_o and c < o and body > prev_body * 1.1:
          if o >= prev_c and c <= prev_o:
            patterns.append({
              'date': date,
              'pattern': 'bearish_engulfing',
              'pattern_kr': '하락 장악형 (Bearish Engulfing)',
              'signal': 'bearish',
              'description': '전일 상승 캔들을 완전히 감싸는 하락 캔들로, 강한 하락 반전 신호입니다.'
            })

    # 최근 5개만 반환
    return patterns[-5:]

  # ========== 골든/데드크로스 감지 ==========

  def _detect_crosses(self, df: pd.DataFrame) -> list:
    """
    골든크로스/데드크로스 감지

    Returns:
      크로스 이벤트 리스트
    """
    crosses = []
    if 'sma_20' not in df.columns or 'sma_50' not in df.columns:
      return crosses

    df_valid = df.dropna(subset=['sma_20', 'sma_50'])
    if len(df_valid) < 2:
      return crosses

    # 최근 60일 내 크로스 탐색
    lookback = min(60, len(df_valid))
    recent = df_valid.tail(lookback)

    for i in range(1, len(recent)):
      curr = recent.iloc[i]
      prev = recent.iloc[i - 1]
      date = str(curr.name.date()) if hasattr(curr.name, 'date') else str(curr.name)

      prev_diff = prev['sma_20'] - prev['sma_50']
      curr_diff = curr['sma_20'] - curr['sma_50']

      # 골든크로스: SMA20이 SMA50을 상향 돌파
      if prev_diff <= 0 and curr_diff > 0:
        crosses.append({
          'date': date,
          'type': 'golden_cross',
          'type_kr': '골든크로스',
          'signal': 'bullish',
          'description': 'SMA(20)이 SMA(50)을 상향 돌파했습니다. 중기 상승 추세 전환 신호입니다.',
          'sma_20': round(float(curr['sma_20']), 2),
          'sma_50': round(float(curr['sma_50']), 2),
        })

      # 데드크로스: SMA20이 SMA50을 하향 돌파
      if prev_diff >= 0 and curr_diff < 0:
        crosses.append({
          'date': date,
          'type': 'dead_cross',
          'type_kr': '데드크로스',
          'signal': 'bearish',
          'description': 'SMA(20)이 SMA(50)을 하향 돌파했습니다. 중기 하락 추세 전환 신호입니다.',
          'sma_20': round(float(curr['sma_20']), 2),
          'sma_50': round(float(curr['sma_50']), 2),
        })

    return crosses

  # ========== 지지선/저항선 ==========

  def _calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> dict:
    """
    지지선/저항선 계산

    Returns:
      지지선/저항선 정보
    """
    if len(df) < window:
      return {'support': [], 'resistance': [], 'pivot': None}

    recent = df.tail(window)
    close = float(recent['close'].iloc[-1])
    high = float(recent['high'].max())
    low = float(recent['low'].min())

    # 피봇 포인트
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)

    # 로컬 최솟값 = 지지선 후보
    supports = []
    resistances = []

    closes = recent['close'].values
    lows = recent['low'].values
    highs = recent['high'].values

    # 로컬 최소/최대 탐색 (5일 윈도우)
    for i in range(2, len(recent) - 2):
      # 로컬 최솟값
      if lows[i] <= lows[i - 1] and lows[i] <= lows[i - 2] and lows[i] <= lows[i + 1] and lows[i] <= lows[i + 2]:
        supports.append(round(float(lows[i]), 2))

      # 로컬 최댓값
      if highs[i] >= highs[i - 1] and highs[i] >= highs[i - 2] and highs[i] >= highs[i + 1] and highs[i] >= highs[i + 2]:
        resistances.append(round(float(highs[i]), 2))

    # 피봇 기반 지지/저항선 추가
    supports.extend([round(s1, 2), round(s2, 2)])
    resistances.extend([round(r1, 2), round(r2, 2)])

    # 중복 제거 및 정렬
    supports = sorted(list(set(supports)))
    resistances = sorted(list(set(resistances)))

    # 현재가 대비 위치
    nearest_support = max([s for s in supports if s < close], default=None)
    nearest_resistance = min([r for r in resistances if r > close], default=None)

    return {
      'pivot': round(pivot, 2),
      'support': supports,
      'resistance': resistances,
      'nearest_support': nearest_support,
      'nearest_resistance': nearest_resistance,
      'current_price': round(close, 2),
      'support_distance_pct': round(((close - nearest_support) / close) * 100, 2) if nearest_support else None,
      'resistance_distance_pct': round(((nearest_resistance - close) / close) * 100, 2) if nearest_resistance else None,
    }

  # ========== 기술적 분석 점수 ==========

  def calculate_technical_score(self, df: pd.DataFrame) -> dict:
    """
    기술적 분석 종합 점수 (0-100)

    Returns:
      점수 및 세부 항목
    """
    latest = df.iloc[-1]
    scores = {}

    # 1. RSI 적정 범위 (20점)
    rsi = latest.get('rsi_14', 50)
    if 40 <= rsi <= 60:
      scores['rsi'] = 20
    elif 30 <= rsi <= 70:
      scores['rsi'] = 15
    elif rsi < 30:
      scores['rsi'] = 12  # 과매도 = 매수 기회
    elif rsi > 70:
      scores['rsi'] = 5  # 과매수 = 위험
    else:
      scores['rsi'] = 10

    # 2. MACD 방향 (20점)
    macd = latest.get('macd', 0)
    macd_signal = latest.get('macd_signal', 0)
    macd_hist = latest.get('macd_histogram', 0)
    if macd > macd_signal and macd_hist > 0:
      scores['macd'] = 20
    elif macd > macd_signal:
      scores['macd'] = 15
    elif macd < macd_signal and macd_hist < 0:
      scores['macd'] = 5
    else:
      scores['macd'] = 10

    # 3. 이동평균선 위치 (20점)
    close = latest.get('close', 0)
    sma_20 = latest.get('sma_20', close)
    sma_50 = latest.get('sma_50', close)
    ma_score = 10
    if close > sma_20:
      ma_score += 5
    if close > sma_50:
      ma_score += 5
    if not np.isnan(sma_20) and not np.isnan(sma_50) and sma_20 > sma_50:
      ma_score += 5
    scores['ma'] = min(20, ma_score)

    # 4. 볼린저밴드 위치 (20점)
    bb_upper = latest.get('bb_upper', close)
    bb_lower = latest.get('bb_lower', close)
    bb_middle = latest.get('bb_middle', close)
    if not np.isnan(bb_upper) and not np.isnan(bb_lower):
      bb_range = bb_upper - bb_lower
      if bb_range > 0:
        bb_position = (close - bb_lower) / bb_range
        if 0.3 <= bb_position <= 0.7:
          scores['bb'] = 20  # 중앙 근처 = 안정
        elif bb_position < 0.2:
          scores['bb'] = 14  # 하단 근처 = 반등 가능
        elif bb_position > 0.8:
          scores['bb'] = 8  # 상단 근처 = 과열
        else:
          scores['bb'] = 15
      else:
        scores['bb'] = 10
    else:
      scores['bb'] = 10

    # 5. 캔들 패턴 + 크로스 시그널 (20점)
    pattern_score = 10  # 기본
    patterns = self._detect_candle_patterns(df)
    crosses = self._detect_crosses(df)

    bullish_patterns = sum(1 for p in patterns if p['signal'] == 'bullish')
    bearish_patterns = sum(1 for p in patterns if p['signal'] == 'bearish')
    pattern_score += (bullish_patterns - bearish_patterns) * 3

    for cross in crosses[-3:]:  # 최근 3개
      if cross['signal'] == 'bullish':
        pattern_score += 5
      else:
        pattern_score -= 5

    scores['pattern'] = max(0, min(20, pattern_score))

    total = sum(scores.values())

    return {
      'technical_score': total,
      'details': scores,
      'max_score': 100,
    }

  # ========== 유틸리티 ==========

  def get_indicator_summary(self, df: pd.DataFrame, ticker: str) -> Dict:
    """
    최신 지표 값 요약 (패턴/크로스/지지저항 포함)

    Returns:
      최신 지표 값 딕셔너리
    """
    latest = df.iloc[-1]

    # 캔들 패턴, 크로스, 지지/저항선
    candle_patterns = self._detect_candle_patterns(df)
    crosses = self._detect_crosses(df)
    support_resistance = self._calculate_support_resistance(df)
    technical_score = self.calculate_technical_score(df)

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
      },
      "candle_patterns": candle_patterns,
      "crosses": crosses,
      "support_resistance": support_resistance,
      "technical_score": technical_score,
    }
