"""
주가 예측 서비스
"""
import torch
import numpy as np
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from ..ml_models.lstm_model import LSTMPredictor
from .stock_data_service import StockDataService
from .feature_engineering import FeatureEngineeringService
from .preprocessing import PreprocessingService
from .error_correction_service import ErrorCorrectionService
from ..repositories.stock_repository import StockRepository
from ..repositories.prediction_repository import PredictionRepository
from ..models.stock import Prediction

logger = structlog.get_logger()

# Feature 이름과 한국어 설명 매핑
FEATURE_DESCRIPTIONS = {
  'volume': '거래량 - 시장 참여도와 유동성 지표',
  'rsi_14': 'RSI(14) - 과매수/과매도 판단 지표',
  'macd': 'MACD - 추세 전환 신호 지표',
  'bb_upper': '볼린저밴드 상단 - 가격 상한 변동성',
  'bb_lower': '볼린저밴드 하단 - 가격 하한 변동성',
  'sma_20': 'SMA(20) - 20일 단기 이동평균',
  'ema_12': 'EMA(12) - 12일 지수이동평균',
  'close': '종가 - 당일 최종 거래 가격',
}

FEATURE_COLS = ['volume', 'rsi_14', 'macd', 'bb_upper', 'bb_lower', 'sma_20', 'ema_12']
TARGET_COL = 'close'


class PredictionService:
  """LSTM 모델을 사용한 주가 예측 서비스"""

  def __init__(self, model_path: str = 'models/weights/lstm_aapl.pt'):
    self.model_path = model_path
    self.model = None
    self.stock_service = StockDataService()
    self.feature_service = FeatureEngineeringService()
    self.prep_service = PreprocessingService()
    self.error_correction_service = ErrorCorrectionService()

    # 모델 로드
    self._load_model()

    logger.info("PredictionService initialized", model_path=model_path)

  def _load_model(self):
    """저장된 모델 로드"""
    try:
      checkpoint = torch.load(self.model_path, map_location='cpu')

      # 모델 생성
      self.model = LSTMPredictor(
        input_size=8,  # feature 개수
        hidden_size=64,
        num_layers=2,
        dropout=0.2
      )

      # 가중치 로드
      self.model.load_state_dict(checkpoint['model_state_dict'])
      self.model.eval()

      logger.info("Model loaded successfully")
    except Exception as e:
      logger.error("Failed to load model", error=str(e))
      self.model = None

  # ========== 기술적 지표 재계산 헬퍼 (numpy array 대상) ==========

  def _calculate_rsi(self, closes: np.ndarray, period: int = 14) -> float:
    """RSI 계산 (numpy 배열 대상)"""
    if len(closes) < period + 1:
      return 50.0
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
      return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))

  def _calculate_ema(self, data: np.ndarray, span: int) -> float:
    """EMA 계산"""
    if len(data) < span:
      return float(data[-1]) if len(data) > 0 else 0.0
    multiplier = 2.0 / (span + 1)
    ema = data[0]
    for val in data[1:]:
      ema = (val - ema) * multiplier + ema
    return float(ema)

  def _calculate_sma(self, data: np.ndarray, period: int) -> float:
    """SMA 계산"""
    if len(data) < period:
      return float(np.mean(data)) if len(data) > 0 else 0.0
    return float(np.mean(data[-period:]))

  def _calculate_macd(self, closes: np.ndarray) -> float:
    """MACD 계산 (EMA12 - EMA26)"""
    ema12 = self._calculate_ema(closes, 12)
    ema26 = self._calculate_ema(closes, 26)
    return ema12 - ema26

  def _calculate_bollinger(self, closes: np.ndarray, period: int = 20) -> tuple:
    """볼린저밴드 상단/하단 계산"""
    if len(closes) < period:
      mean = float(np.mean(closes))
      std = float(np.std(closes))
    else:
      mean = float(np.mean(closes[-period:]))
      std = float(np.std(closes[-period:]))
    upper = mean + 2 * std
    lower = mean - 2 * std
    return upper, lower

  # ========== Gradient 기반 Feature Importance ==========

  def _calculate_feature_importance(self, X: np.ndarray) -> list:
    """
    Gradient 기반 feature importance 계산

    Args:
      X: 입력 시퀀스 (1, seq_len, n_features)

    Returns:
      feature별 importance 리스트
    """
    try:
      feature_names = FEATURE_COLS + [TARGET_COL]
      x_tensor = torch.FloatTensor(X).requires_grad_(True)

      # forward + backward
      output = self.model(x_tensor)
      output.backward()

      # gradient 절대값 평균 = feature별 importance
      gradients = x_tensor.grad.abs().mean(dim=1).squeeze()  # (n_features,)
      importance_raw = gradients.detach().numpy()

      # 비율로 정규화
      total = importance_raw.sum()
      if total > 0:
        importance_normalized = importance_raw / total
      else:
        importance_normalized = np.ones(len(feature_names)) / len(feature_names)

      result = []
      for i, name in enumerate(feature_names):
        result.append({
          'feature': name,
          'importance': round(float(importance_normalized[i]), 4),
          'description': FEATURE_DESCRIPTIONS.get(name, name)
        })

      # importance 내림차순 정렬
      result.sort(key=lambda x: x['importance'], reverse=True)
      return result
    except Exception as e:
      logger.warning("Feature importance 계산 실패", error=str(e))
      # fallback: 균등 분배
      feature_names = FEATURE_COLS + [TARGET_COL]
      return [
        {'feature': name, 'importance': round(1.0 / len(feature_names), 4),
         'description': FEATURE_DESCRIPTIONS.get(name, name)}
        for name in feature_names
      ]

  # ========== Monte Carlo Dropout 신뢰도 ==========

  def _calculate_confidence(self, X: np.ndarray, n_perturbations: int = 10) -> float:
    """
    Monte Carlo Dropout 기반 예측 신뢰도 계산

    Args:
      X: 입력 시퀀스 (1, seq_len, n_features)
      n_perturbations: 반복 횟수

    Returns:
      신뢰도 (0~1)
    """
    try:
      # Dropout 활성화 (train 모드)
      self.model.train()
      predictions = []

      for _ in range(n_perturbations):
        with torch.no_grad():
          x_tensor = torch.FloatTensor(X)
          pred = self.model(x_tensor).item()
          predictions.append(pred)

      # eval 모드 복원
      self.model.eval()

      preds = np.array(predictions)
      mean = np.mean(preds)
      std = np.std(preds)

      if mean == 0:
        cv = 0
      else:
        cv = abs(std / mean)

      # CV가 작을수록 신뢰도 높음 (cv*3으로 완화, 기존 cv*10은 너무 공격적)
      confidence = max(0.1, min(0.95, 1.0 - cv * 3))
      return round(confidence, 4)
    except Exception as e:
      logger.warning("신뢰도 계산 실패", error=str(e))
      self.model.eval()
      return 0.5

  def predict_future(
    self,
    ticker: str,
    days: int = 7
  ) -> Dict:
    """
    미래 주가 예측 (개선된 자동회귀 루프 + feature importance + 신뢰도)

    Args:
      ticker: 종목 코드
      days: 예측할 일수

    Returns:
      예측 결과 딕셔너리
    """
    if self.model is None:
      raise ValueError("Model not loaded")

    # 1. 데이터 수집 (최근 1년)
    df = self.stock_service.fetch_stock_data(ticker, period='1y')
    df_indicators = self.feature_service.calculate_all_indicators(df)

    # 2. 전처리
    all_cols = FEATURE_COLS + [TARGET_COL]
    df_clean = df_indicators[all_cols].dropna()

    # 정규화 (fit=True로 scaler 학습)
    df_normalized = self.prep_service.normalize_data(df_clean, method='minmax', fit=True)

    # 최근 60일 정규화된 데이터
    recent_normalized = df_normalized.values[-60:]

    # 원본 데이터 120일치 보관 (자동회귀 스텝에서 지표 재계산용)
    raw_recent = df_clean.values[-120:].copy()
    # raw_recent의 마지막 열(index 7)이 close
    raw_closes = list(raw_recent[:, 7])  # close 이력
    raw_volumes = list(raw_recent[:, 0])  # volume 이력

    # 3. Feature importance 계산 (초기 시퀀스로)
    X_for_importance = recent_normalized.reshape(1, 60, -1)
    feature_importance = self._calculate_feature_importance(X_for_importance)

    # 4. 예측 (개선된 자동회귀)
    predictions = []
    current_price = df['close'].iloc[-1]
    scaler = self.prep_service.scaler

    input_sequence = recent_normalized.copy()

    for step in range(days):
      # 시퀀스를 모델 입력 형태로 변환
      X = input_sequence.reshape(1, 60, -1)

      # 예측
      with torch.no_grad():
        pred_normalized = self.model.predict(X, device='cpu')[0][0]

      # 역정규화 (close는 인덱스 7)
      pred_price = pred_normalized * (scaler.data_max_[7] - scaler.data_min_[7]) + scaler.data_min_[7]

      # 신뢰도 계산
      confidence = self._calculate_confidence(X)

      predictions.append({
        'predicted_price': float(pred_price),
        'confidence': confidence
      })

      # 자동회귀: 예측된 close로 지표 재계산 후 시퀀스 갱신
      raw_closes.append(float(pred_price))
      # volume은 최근 평균 사용
      avg_volume = np.mean(raw_volumes[-20:])
      raw_volumes.append(avg_volume)

      closes_arr = np.array(raw_closes)
      # 기술적 지표 재계산
      new_rsi = self._calculate_rsi(closes_arr)
      new_macd = self._calculate_macd(closes_arr)
      bb_upper, bb_lower = self._calculate_bollinger(closes_arr)
      new_sma20 = self._calculate_sma(closes_arr, 20)
      new_ema12 = self._calculate_ema(closes_arr, 12)

      # 새 raw row: [volume, rsi_14, macd, bb_upper, bb_lower, sma_20, ema_12, close]
      new_raw_row = np.array([
        avg_volume, new_rsi, new_macd, bb_upper, bb_lower,
        new_sma20, new_ema12, float(pred_price)
      ])

      # scaler로 정규화
      new_normalized = (new_raw_row - scaler.data_min_) / (scaler.data_max_ - scaler.data_min_ + 1e-10)

      # 시퀀스 갱신 (shift left, 새 행 추가)
      input_sequence = np.roll(input_sequence, -1, axis=0)
      input_sequence[-1] = new_normalized

    # 5. 결과 구성
    last_date = df.index[-1]
    prediction_dates = [
      (last_date + timedelta(days=i + 1)).strftime('%Y-%m-%d')
      for i in range(days)
    ]

    # 예측 결과에 날짜 추가
    for i, date in enumerate(prediction_dates):
      predictions[i]['date'] = date

    return {
      'ticker': ticker,
      'current_price': float(current_price),
      'predictions': predictions,
      'feature_importance': feature_importance,
      'prediction_date': datetime.utcnow().isoformat(),
      'model': 'LSTM'
    }

  async def predict_and_save(
    self,
    db: AsyncSession,
    ticker: str,
    days: int = 7
  ) -> Dict:
    """
    미래 주가 예측 후 DB 저장 (오차 보정 적용)

    Args:
      db: 데이터베이스 세션
      ticker: 종목 코드
      days: 예측할 일수

    Returns:
      원시 예측 + 보정 예측 + 보정 정보 + feature importance 포함 딕셔너리
    """
    # 1. 원시 예측 (동기 메서드)
    raw_result = self.predict_future(ticker, days)

    # 2. 종목 get_or_create
    stock_repo = StockRepository(db)
    stock = await stock_repo.get_or_create(ticker=ticker)

    # 3. 오차 보정 계수 계산
    correction_info = await self.error_correction_service.calculate_correction(
      db=db,
      stock_id=stock.id
    )

    # 4. 보정된 예측값 계산 및 Prediction ORM 객체 생성
    now = datetime.utcnow()
    prediction_objects = []
    corrected_predictions = []

    for item in raw_result['predictions']:
      raw_price = item['predicted_price']
      confidence = item.get('confidence', 0.5)
      corrected_price = self.error_correction_service.apply_correction(raw_price, correction_info)

      # feature importance를 JSON으로 직렬화
      fi_json = json.dumps(raw_result.get('feature_importance', []), ensure_ascii=False)

      # DB에는 원시 예측값 저장
      pred = Prediction(
        stock_id=stock.id,
        prediction_date=now,
        target_date=datetime.strptime(item['date'], '%Y-%m-%d'),
        predicted_price=raw_price,
        model_name='lstm',
        model_version='1.0',
        confidence_score=confidence,
        shap_values=fi_json,
      )
      prediction_objects.append(pred)
      corrected_predictions.append({
        'date': item['date'],
        'predicted_price': raw_price,
        'corrected_price': round(corrected_price, 4),
        'confidence': confidence
      })

    # 5. DB 저장
    pred_repo = PredictionRepository(db)
    await pred_repo.save_batch(prediction_objects)

    logger.info(
      "예측 완료 및 DB 저장",
      ticker=ticker,
      days=days,
      is_corrected=correction_info['is_corrected'],
      correction_factor=correction_info['factor']
    )

    return {
      'ticker': ticker,
      'current_price': raw_result['current_price'],
      'predictions': corrected_predictions,
      'feature_importance': raw_result.get('feature_importance', []),
      'correction_info': correction_info,
      'prediction_date': now.isoformat(),
      'model': 'LSTM'
    }
