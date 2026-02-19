"""
종합 투자 판단 스코어 서비스
기본적 분석 + 기술적 분석 + AI 예측 방향을 통합하여 종합 투자 점수 산출
"""
import structlog
from typing import Dict
from .fundamental_service import FundamentalService
from .stock_data_service import StockDataService
from .feature_engineering import FeatureEngineeringService
from .prediction_service import PredictionService

logger = structlog.get_logger()


class InvestmentScoreService:
  """종합 투자 판단 스코어 서비스"""

  def __init__(self):
    self.fundamental_service = FundamentalService()
    self.stock_service = StockDataService()
    self.feature_service = FeatureEngineeringService()
    self.prediction_service = PredictionService()
    logger.info("InvestmentScoreService 초기화")

  def calculate(self, ticker: str) -> dict:
    """
    종합 투자 판단 스코어 계산
    기본적(40%) + 기술적(30%) + AI 예측(30%) = 100점

    Args:
      ticker: 종목 코드

    Returns:
      종합 판단 결과 딕셔너리
    """
    try:
      # 기본적 분석
      fundamental = self.fundamental_service.analyze(ticker)

      # 기술적 분석
      technical = self._analyze_technical(ticker)

      # AI 예측 분석
      prediction = self._analyze_prediction(ticker)

      # 3축 통합 점수
      fundamental_score = fundamental.get('fundamental_score', 50)
      technical_score = technical.get('technical_score', 50)
      prediction_score = prediction.get('prediction_score', 50)

      # 기본적 40% + 기술적 30% + 예측 30%
      total = (fundamental_score * 0.4) + (technical_score * 0.3) + (prediction_score * 0.3)

      # 모순 감지
      contradictions = self._detect_contradictions(technical, prediction)

      grade = self._get_grade(total)
      recommendation = self._get_recommendation(total, contradictions)
      summary = self._generate_summary(fundamental, technical, prediction, total, contradictions)

      return {
        'ticker': ticker,
        'company_name': fundamental.get('company_name', ticker),
        'total_score': round(total, 1),
        'grade': grade['grade'],
        'grade_label': grade['label'],
        'recommendation': recommendation,
        'fundamental_score': round(fundamental_score, 1),
        'technical_score': round(technical_score, 1),
        'prediction_score': round(prediction_score, 1),
        'prediction_trend': prediction.get('trend', {}),
        'contradictions': contradictions,
        'fundamental_detail': fundamental,
        'technical_detail': technical,
        'prediction_detail': prediction,
        'summary': summary,
      }
    except Exception as e:
      logger.error("종합 투자 판단 실패", ticker=ticker, error=str(e))
      raise

  def _analyze_technical(self, ticker: str) -> dict:
    """기술적 분석 수행"""
    try:
      df = self.stock_service.fetch_stock_data(ticker, period='6mo')
      df_with_indicators = self.feature_service.calculate_all_indicators(df)
      score_info = self.feature_service.calculate_technical_score(df_with_indicators)
      summary = self.feature_service.get_indicator_summary(df_with_indicators, ticker)

      # 기술적 시그널 방향 판단
      latest = df_with_indicators.iloc[-1]
      rsi = latest.get('rsi_14', 50)
      macd = latest.get('macd', 0)
      macd_signal = latest.get('macd_signal', 0)
      close = latest.get('close', 0)
      sma_20 = latest.get('sma_20', 0)
      sma_50 = latest.get('sma_50', 0)

      signals = []
      if rsi < 30:
        signals.append('BUY')
      elif rsi > 70:
        signals.append('SELL')
      else:
        signals.append('NEUTRAL')
      if macd > macd_signal:
        signals.append('BUY')
      else:
        signals.append('SELL')
      if close > sma_20 and close > sma_50:
        signals.append('BUY')
      elif close < sma_20 and close < sma_50:
        signals.append('SELL')
      else:
        signals.append('NEUTRAL')

      buy_count = signals.count('BUY')
      sell_count = signals.count('SELL')
      overall = 'BUY' if buy_count > sell_count else ('SELL' if sell_count > buy_count else 'NEUTRAL')

      return {
        'technical_score': score_info['technical_score'],
        'score_details': score_info['details'],
        'indicators': summary,
        'signal_direction': overall,
        'candle_patterns': summary.get('candle_patterns', []),
        'crosses': summary.get('crosses', []),
        'support_resistance': summary.get('support_resistance', {}),
      }
    except Exception as e:
      logger.error("기술적 분석 실패", ticker=ticker, error=str(e))
      return {'technical_score': 50, 'score_details': {}, 'indicators': {}, 'signal_direction': 'NEUTRAL'}

  def _analyze_prediction(self, ticker: str) -> dict:
    """AI 예측 분석 및 점수화"""
    try:
      pred = self.prediction_service.predict_future(ticker, days=7)
      current_price = pred['current_price']
      predictions = pred['predictions']

      if not predictions:
        return {'prediction_score': 50, 'trend': {}}

      last_price = predictions[-1]['predicted_price']
      first_price = predictions[0]['predicted_price']
      change_pct = ((last_price - current_price) / current_price) * 100
      avg_confidence = sum(p.get('confidence', 0.5) for p in predictions) / len(predictions)

      # 예측 방향
      if change_pct > 2:
        direction = 'UP'
      elif change_pct < -2:
        direction = 'DOWN'
      else:
        direction = 'FLAT'

      # 예측 점수 (0-100)
      # 상승 예측일수록 높은 점수, 하락 예측일수록 낮은 점수
      # change_pct -10% → 20점, 0% → 50점, +10% → 80점
      raw_score = 50 + (change_pct * 3)  # -10% → 20, +10% → 80
      # 신뢰도로 중립(50) 방향으로 조정: 신뢰도 낮으면 50에 가깝게
      prediction_score = 50 + (raw_score - 50) * avg_confidence
      prediction_score = max(0, min(100, prediction_score))

      return {
        'prediction_score': round(prediction_score, 1),
        'trend': {
          'direction': direction,
          'change_pct': round(change_pct, 2),
          'current_price': round(current_price, 2),
          'predicted_7d_price': round(last_price, 2),
          'avg_confidence': round(avg_confidence, 4),
        },
        'predictions': predictions,
      }
    except Exception as e:
      logger.error("예측 분석 실패", ticker=ticker, error=str(e))
      return {'prediction_score': 50, 'trend': {'direction': 'UNKNOWN', 'change_pct': 0, 'avg_confidence': 0}}

  def _detect_contradictions(self, technical: dict, prediction: dict) -> list:
    """시그널 간 모순 감지"""
    contradictions = []
    signal_dir = technical.get('signal_direction', 'NEUTRAL')
    pred_trend = prediction.get('trend', {})
    pred_dir = pred_trend.get('direction', 'UNKNOWN')
    change_pct = pred_trend.get('change_pct', 0)
    avg_conf = pred_trend.get('avg_confidence', 0)

    # 모순 1: 시그널 BUY인데 예측 하락
    if signal_dir == 'BUY' and pred_dir == 'DOWN':
      contradictions.append({
        'type': 'signal_vs_prediction',
        'severity': 'high' if abs(change_pct) > 5 else 'medium',
        'message': f'기술적 시그널은 매수(BUY)이지만, AI 예측은 7일간 {change_pct:+.1f}% 하락을 예측합니다.',
        'advice': '단기 기술적 지표는 긍정적이나 AI 모델은 하락 추세를 감지했습니다. 신중한 접근이 필요합니다.',
      })

    # 모순 2: 시그널 SELL인데 예측 상승
    if signal_dir == 'SELL' and pred_dir == 'UP':
      contradictions.append({
        'type': 'signal_vs_prediction',
        'severity': 'high' if abs(change_pct) > 5 else 'medium',
        'message': f'기술적 시그널은 매도(SELL)이지만, AI 예측은 7일간 {change_pct:+.1f}% 상승을 예측합니다.',
        'advice': '기술적 지표는 과열 신호이나 AI 모델은 추가 상승을 예측합니다. 보유 지속을 고려해볼 수 있습니다.',
      })

    # 경고: 신뢰도 매우 낮음
    if avg_conf < 0.3 and pred_dir != 'FLAT':
      contradictions.append({
        'type': 'low_confidence',
        'severity': 'medium',
        'message': f'AI 예측 신뢰도가 낮습니다 (평균 {avg_conf * 100:.0f}%). 예측 결과를 참고 수준으로만 활용하세요.',
        'advice': '모델이 현재 시장 패턴에 대해 확신이 낮습니다. 기본적 분석과 기술적 지표를 우선 참고하세요.',
      })

    return contradictions

  def _get_grade(self, score: float) -> dict:
    """점수 기반 등급 판정"""
    if score >= 80:
      return {'grade': 'A+', 'label': '매수 적극 추천'}
    elif score >= 70:
      return {'grade': 'A', 'label': '매수 추천'}
    elif score >= 60:
      return {'grade': 'B+', 'label': '관심 종목'}
    elif score >= 50:
      return {'grade': 'B', 'label': '중립 (관망)'}
    elif score >= 40:
      return {'grade': 'C', 'label': '주의'}
    else:
      return {'grade': 'D', 'label': '매도 고려'}

  def _get_recommendation(self, score: float, contradictions: list) -> dict:
    """점수 + 모순을 반영한 추천 의견"""
    has_high_contradiction = any(c['severity'] == 'high' for c in contradictions)

    # 높은 모순이 있으면 추천 등급을 한 단계 낮춤
    if has_high_contradiction and score >= 60:
      return {
        'action': '신중 접근',
        'color': 'orange',
        'description': '분석 지표 간 상충되는 신호가 감지되었습니다. 기본적 가치는 긍정적이나, 단기 예측과 기술적 신호 사이에 괴리가 있어 신중한 접근이 필요합니다.'
      }

    if score >= 80:
      return {
        'action': '적극 매수',
        'color': 'green',
        'description': '기본적 가치, 기술적 지표, AI 예측이 모두 우수합니다. 적극적인 매수를 고려해볼 수 있습니다.'
      }
    elif score >= 70:
      return {
        'action': '매수',
        'color': 'green',
        'description': '긍정적인 투자 요인이 많습니다. 매수를 고려해볼 수 있습니다.'
      }
    elif score >= 60:
      return {
        'action': '관심',
        'color': 'blue',
        'description': '일부 긍정적 신호가 있으나, 추가 확인이 필요합니다. 관심 목록에 추가하세요.'
      }
    elif score >= 50:
      return {
        'action': '관망',
        'color': 'gray',
        'description': '뚜렷한 방향성이 없습니다. 시장 상황을 지켜보며 관망하는 것이 좋습니다.'
      }
    elif score >= 40:
      return {
        'action': '주의',
        'color': 'orange',
        'description': '부정적 신호가 다수 감지됩니다. 신규 매수는 신중해야 합니다.'
      }
    else:
      return {
        'action': '매도 고려',
        'color': 'red',
        'description': '기본적 가치, 기술적 지표, AI 예측 모두 부정적입니다. 보유 중이라면 매도를 고려하세요.'
      }

  def _generate_summary(self, fundamental: dict, technical: dict, prediction: dict, total_score: float, contradictions: list) -> str:
    """종합 판단 요약 텍스트 자동 생성"""
    parts = []

    # 가치 평가 요약
    valuation = fundamental.get('valuation', {})
    pe = valuation.get('trailing_pe')
    if pe is not None:
      parts.append(f"PER {pe:.1f}배로 {valuation.get('pe_assessment', '분석 불가')}")

    # 수익성 요약
    profitability = fundamental.get('profitability', {})
    pm = profitability.get('profit_margins')
    if pm is not None:
      parts.append(f"순이익률 {pm * 100:.1f}%({profitability.get('margin_assessment', '')})")

    # 기술적 시그널 요약
    signal_dir = technical.get('signal_direction', 'NEUTRAL')
    signal_kr = {'BUY': '매수', 'SELL': '매도', 'NEUTRAL': '중립'}.get(signal_dir, '중립')
    parts.append(f"기술적 시그널 {signal_kr}")

    # AI 예측 방향 요약
    trend = prediction.get('trend', {})
    pred_dir = trend.get('direction', 'UNKNOWN')
    change_pct = trend.get('change_pct', 0)
    avg_conf = trend.get('avg_confidence', 0)

    if pred_dir == 'UP':
      parts.append(f"AI 예측 7일 {change_pct:+.1f}% 상승 (신뢰도 {avg_conf * 100:.0f}%)")
    elif pred_dir == 'DOWN':
      parts.append(f"AI 예측 7일 {change_pct:+.1f}% 하락 (신뢰도 {avg_conf * 100:.0f}%)")
    else:
      parts.append(f"AI 예측 7일 보합 (신뢰도 {avg_conf * 100:.0f}%)")

    summary = '. '.join(parts[:4])

    # 모순 경고 추가
    if contradictions:
      high_contradictions = [c for c in contradictions if c['severity'] == 'high']
      if high_contradictions:
        summary += f". [주의] {high_contradictions[0]['message']}"
      else:
        low_contradictions = [c for c in contradictions if c['type'] == 'low_confidence']
        if low_contradictions:
          summary += f". [참고] {low_contradictions[0]['message']}"

    # 종합 판단
    grade_info = self._get_grade(total_score)
    summary += f" 종합 판단: {grade_info['label']}."

    return summary
