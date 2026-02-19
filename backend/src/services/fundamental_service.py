"""
기본적 분석 서비스 (Fundamental Analysis)
PER/PBR/실적/애널리스트 분석 + 기본적 분석 점수 계산
"""
import numpy as np
from typing import Dict, Optional
import structlog
from ..infrastructure.api_clients.yahoo_finance import YahooFinanceClient

logger = structlog.get_logger()


class FundamentalService:
  """기본적 분석 서비스"""

  def __init__(self):
    self.yahoo_client = YahooFinanceClient()
    logger.info("FundamentalService 초기화")

  def analyze(self, ticker: str) -> dict:
    """
    종합 기본적 분석 수행

    Args:
      ticker: 종목 코드

    Returns:
      기본적 분석 결과 딕셔너리
    """
    try:
      info = self.yahoo_client.get_stock_info(ticker)
      if not info:
        raise ValueError(f"종목 정보를 찾을 수 없습니다: {ticker}")

      valuation = self._analyze_valuation(info)
      profitability = self._analyze_profitability(info)
      financial_health = self._analyze_health(info)
      analyst = self._analyze_analyst(info)
      fundamental_score = self._calculate_score(valuation, profitability, financial_health, analyst)

      return {
        'ticker': ticker,
        'company_name': info.get('longName', info.get('shortName', ticker)),
        'sector': info.get('sector', '정보 없음'),
        'industry': info.get('industry', '정보 없음'),
        'valuation': valuation,
        'profitability': profitability,
        'financial_health': financial_health,
        'analyst': analyst,
        'fundamental_score': fundamental_score,
      }
    except Exception as e:
      logger.error("기본적 분석 실패", ticker=ticker, error=str(e))
      raise

  def _safe_get(self, info: dict, key: str, default=None):
    """안전하게 값 추출 (None, NaN 처리)"""
    val = info.get(key, default)
    if val is None:
      return default
    try:
      if np.isnan(float(val)):
        return default
    except (TypeError, ValueError):
      pass
    return val

  def _analyze_valuation(self, info: dict) -> dict:
    """가치 평가 분석"""
    trailing_pe = self._safe_get(info, 'trailingPE')
    forward_pe = self._safe_get(info, 'forwardPE')
    price_to_book = self._safe_get(info, 'priceToBook')
    peg_ratio = self._safe_get(info, 'pegRatio')
    market_cap = self._safe_get(info, 'marketCap')

    # 시가총액 분류
    cap_category = '정보 없음'
    if market_cap:
      if market_cap >= 200e9:
        cap_category = '메가캡 (2000억$ 이상)'
      elif market_cap >= 10e9:
        cap_category = '대형주 (100억$ 이상)'
      elif market_cap >= 2e9:
        cap_category = '중형주 (20억$ 이상)'
      else:
        cap_category = '소형주 (20억$ 미만)'

    # PER 판정
    pe_assessment = '정보 없음'
    if trailing_pe is not None:
      if trailing_pe < 0:
        pe_assessment = '적자 (음수 PER)'
      elif trailing_pe < 10:
        pe_assessment = '저평가 가능성'
      elif trailing_pe < 20:
        pe_assessment = '적정 수준'
      elif trailing_pe < 30:
        pe_assessment = '다소 고평가'
      else:
        pe_assessment = '고평가 (높은 성장 기대)'

    # PBR 판정
    pbr_assessment = '정보 없음'
    if price_to_book is not None:
      if price_to_book < 1:
        pbr_assessment = '자산가치 대비 저평가'
      elif price_to_book < 3:
        pbr_assessment = '적정 수준'
      else:
        pbr_assessment = '자산가치 대비 고평가'

    # PEG 판정
    peg_assessment = '정보 없음'
    if peg_ratio is not None:
      if peg_ratio < 0:
        peg_assessment = '음수 (이익 감소 또는 적자)'
      elif peg_ratio < 1:
        peg_assessment = '성장성 대비 저평가'
      elif peg_ratio < 2:
        peg_assessment = '적정 수준'
      else:
        peg_assessment = '성장성 대비 고평가'

    return {
      'trailing_pe': trailing_pe,
      'forward_pe': forward_pe,
      'price_to_book': price_to_book,
      'peg_ratio': peg_ratio,
      'market_cap': market_cap,
      'cap_category': cap_category,
      'pe_assessment': pe_assessment,
      'pbr_assessment': pbr_assessment,
      'peg_assessment': peg_assessment,
      'score': self._valuation_score(trailing_pe, price_to_book, peg_ratio),
    }

  def _valuation_score(self, pe, pbr, peg) -> float:
    """가치 평가 점수 (0-100)"""
    score = 50  # 기본값

    if pe is not None:
      if pe < 0:
        score -= 15
      elif pe < 10:
        score += 20
      elif pe < 15:
        score += 15
      elif pe < 20:
        score += 5
      elif pe < 30:
        score -= 5
      else:
        score -= 15

    if pbr is not None:
      if pbr < 1:
        score += 15
      elif pbr < 3:
        score += 5
      elif pbr > 5:
        score -= 10

    if peg is not None:
      if 0 < peg < 1:
        score += 15
      elif 1 <= peg < 2:
        score += 5
      elif peg >= 2:
        score -= 10

    return max(0, min(100, score))

  def _analyze_profitability(self, info: dict) -> dict:
    """수익성 분석"""
    revenue_growth = self._safe_get(info, 'revenueGrowth')
    operating_margins = self._safe_get(info, 'operatingMargins')
    profit_margins = self._safe_get(info, 'profitMargins')
    trailing_eps = self._safe_get(info, 'trailingEps')
    earnings_growth = self._safe_get(info, 'earningsGrowth')
    revenue = self._safe_get(info, 'totalRevenue')

    # 마진 판정
    margin_assessment = '정보 없음'
    if profit_margins is not None:
      pm = profit_margins * 100
      if pm > 20:
        margin_assessment = '우수한 수익성'
      elif pm > 10:
        margin_assessment = '양호한 수익성'
      elif pm > 0:
        margin_assessment = '낮은 수익성'
      else:
        margin_assessment = '적자'

    # 성장 판정
    growth_assessment = '정보 없음'
    if revenue_growth is not None:
      rg = revenue_growth * 100
      if rg > 20:
        growth_assessment = '고성장'
      elif rg > 10:
        growth_assessment = '양호한 성장'
      elif rg > 0:
        growth_assessment = '저성장'
      else:
        growth_assessment = '역성장'

    return {
      'revenue_growth': revenue_growth,
      'operating_margins': operating_margins,
      'profit_margins': profit_margins,
      'trailing_eps': trailing_eps,
      'earnings_growth': earnings_growth,
      'revenue': revenue,
      'margin_assessment': margin_assessment,
      'growth_assessment': growth_assessment,
      'score': self._profitability_score(revenue_growth, operating_margins, profit_margins, earnings_growth),
    }

  def _profitability_score(self, rev_growth, op_margin, profit_margin, earnings_growth) -> float:
    """수익성 점수 (0-100)"""
    score = 50

    if profit_margin is not None:
      pm = profit_margin * 100
      if pm > 20:
        score += 15
      elif pm > 10:
        score += 10
      elif pm > 0:
        score += 0
      else:
        score -= 15

    if op_margin is not None:
      om = op_margin * 100
      if om > 25:
        score += 10
      elif om > 15:
        score += 5
      elif om < 0:
        score -= 10

    if rev_growth is not None:
      rg = rev_growth * 100
      if rg > 20:
        score += 15
      elif rg > 10:
        score += 10
      elif rg > 0:
        score += 5
      else:
        score -= 10

    if earnings_growth is not None:
      eg = earnings_growth * 100
      if eg > 20:
        score += 10
      elif eg > 0:
        score += 5
      else:
        score -= 5

    return max(0, min(100, score))

  def _analyze_health(self, info: dict) -> dict:
    """재무 건전성 분석"""
    debt_to_equity = self._safe_get(info, 'debtToEquity')
    current_ratio = self._safe_get(info, 'currentRatio')
    roe = self._safe_get(info, 'returnOnEquity')
    roa = self._safe_get(info, 'returnOnAssets')
    free_cashflow = self._safe_get(info, 'freeCashflow')

    # 부채비율 판정
    debt_assessment = '정보 없음'
    if debt_to_equity is not None:
      if debt_to_equity < 50:
        debt_assessment = '매우 건전'
      elif debt_to_equity < 100:
        debt_assessment = '양호'
      elif debt_to_equity < 200:
        debt_assessment = '주의'
      else:
        debt_assessment = '위험 (고부채)'

    # 유동비율 판정
    liquidity_assessment = '정보 없음'
    if current_ratio is not None:
      if current_ratio >= 2:
        liquidity_assessment = '매우 양호'
      elif current_ratio >= 1.5:
        liquidity_assessment = '양호'
      elif current_ratio >= 1:
        liquidity_assessment = '보통'
      else:
        liquidity_assessment = '유동성 위험'

    # ROE 판정
    roe_assessment = '정보 없음'
    if roe is not None:
      roe_pct = roe * 100
      if roe_pct > 20:
        roe_assessment = '우수'
      elif roe_pct > 15:
        roe_assessment = '양호'
      elif roe_pct > 10:
        roe_assessment = '보통'
      elif roe_pct > 0:
        roe_assessment = '낮음'
      else:
        roe_assessment = '적자'

    return {
      'debt_to_equity': debt_to_equity,
      'current_ratio': current_ratio,
      'return_on_equity': roe,
      'return_on_assets': roa,
      'free_cashflow': free_cashflow,
      'debt_assessment': debt_assessment,
      'liquidity_assessment': liquidity_assessment,
      'roe_assessment': roe_assessment,
      'score': self._health_score(debt_to_equity, current_ratio, roe),
    }

  def _health_score(self, dte, cr, roe) -> float:
    """재무 건전성 점수 (0-100)"""
    score = 50

    if dte is not None:
      if dte < 50:
        score += 15
      elif dte < 100:
        score += 10
      elif dte < 200:
        score -= 5
      else:
        score -= 15

    if cr is not None:
      if cr >= 2:
        score += 15
      elif cr >= 1.5:
        score += 10
      elif cr >= 1:
        score += 5
      else:
        score -= 10

    if roe is not None:
      roe_pct = roe * 100
      if roe_pct > 20:
        score += 20
      elif roe_pct > 15:
        score += 15
      elif roe_pct > 10:
        score += 5
      elif roe_pct < 0:
        score -= 15

    return max(0, min(100, score))

  def _analyze_analyst(self, info: dict) -> dict:
    """애널리스트 의견 분석"""
    target_mean = self._safe_get(info, 'targetMeanPrice')
    target_high = self._safe_get(info, 'targetHighPrice')
    target_low = self._safe_get(info, 'targetLowPrice')
    recommendation = self._safe_get(info, 'recommendationKey', '정보 없음')
    num_analysts = self._safe_get(info, 'numberOfAnalystOpinions', 0)
    current_price = self._safe_get(info, 'currentPrice') or self._safe_get(info, 'regularMarketPrice')

    # 목표가 괴리율 계산
    target_gap_pct = None
    target_assessment = '정보 없음'
    if target_mean and current_price and current_price > 0:
      target_gap_pct = round(((target_mean - current_price) / current_price) * 100, 2)
      if target_gap_pct > 20:
        target_assessment = '강한 상승 여력'
      elif target_gap_pct > 10:
        target_assessment = '상승 여력 있음'
      elif target_gap_pct > 0:
        target_assessment = '소폭 상승 여력'
      elif target_gap_pct > -10:
        target_assessment = '소폭 하락 가능'
      else:
        target_assessment = '하락 위험'

    # 추천 의견 한국어 변환
    rec_kr = {
      'buy': '매수',
      'strong_buy': '적극 매수',
      'hold': '보유',
      'sell': '매도',
      'strong_sell': '적극 매도',
      'underperform': '시장 하회',
      'outperform': '시장 상회',
    }
    recommendation_kr = rec_kr.get(recommendation, recommendation)

    return {
      'target_mean_price': target_mean,
      'target_high_price': target_high,
      'target_low_price': target_low,
      'current_price': current_price,
      'target_gap_pct': target_gap_pct,
      'recommendation': recommendation,
      'recommendation_kr': recommendation_kr,
      'num_analysts': num_analysts,
      'target_assessment': target_assessment,
      'score': self._analyst_score(target_gap_pct, recommendation, num_analysts),
    }

  def _analyst_score(self, gap_pct, recommendation, num_analysts) -> float:
    """애널리스트 점수 (0-100)"""
    score = 50

    if gap_pct is not None:
      if gap_pct > 20:
        score += 20
      elif gap_pct > 10:
        score += 15
      elif gap_pct > 0:
        score += 5
      elif gap_pct > -10:
        score -= 5
      else:
        score -= 15

    rec_scores = {
      'strong_buy': 20,
      'buy': 15,
      'outperform': 10,
      'hold': 0,
      'underperform': -10,
      'sell': -15,
      'strong_sell': -20,
    }
    score += rec_scores.get(recommendation, 0)

    # 분석가 수가 적으면 신뢰도 하락
    if num_analysts and num_analysts < 5:
      score -= 5

    return max(0, min(100, score))

  def _calculate_score(self, valuation, profitability, health, analyst) -> float:
    """
    기본적 분석 종합 점수 (0-100)

    가치 평가 30% + 수익성 30% + 재무 건전성 20% + 애널리스트 20%
    """
    v_score = valuation.get('score', 50)
    p_score = profitability.get('score', 50)
    h_score = health.get('score', 50)
    a_score = analyst.get('score', 50)

    total = (v_score * 0.3) + (p_score * 0.3) + (h_score * 0.2) + (a_score * 0.2)
    return round(total, 1)
