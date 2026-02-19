"""
종합 분석 API 라우터
기본적 분석 + 종합 투자 판단 API
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from ...schemas.stock import APIResponse
from ...services.fundamental_service import FundamentalService
from ...services.investment_score_service import InvestmentScoreService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/analysis", tags=["analysis"])
fundamental_service = FundamentalService()
investment_score_service = InvestmentScoreService()


@router.get("/{ticker}/fundamental")
async def get_fundamental_analysis(ticker: str):
  """
  기본적 분석 조회

  PER/PBR/PEG, 수익성, 재무 건전성, 애널리스트 의견 분석
  """
  try:
    result = fundamental_service.analyze(ticker.upper())

    return APIResponse(
      success=True,
      data=result,
      message="기본적 분석 완료",
      timestamp=datetime.utcnow()
    )
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
    logger.error("기본적 분석 API 실패", ticker=ticker, error=str(e))
    raise HTTPException(status_code=500, detail=f"기본적 분석 오류: {str(e)}")


@router.get("/{ticker}/comprehensive")
async def get_comprehensive_analysis(ticker: str):
  """
  종합 투자 판단 조회

  기본적 분석 + 기술적 분석 통합 스코어, 등급, 추천 의견, AI 요약
  """
  try:
    result = investment_score_service.calculate(ticker.upper())

    return APIResponse(
      success=True,
      data=result,
      message="종합 투자 판단 완료",
      timestamp=datetime.utcnow()
    )
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
    logger.error("종합 분석 API 실패", ticker=ticker, error=str(e))
    raise HTTPException(status_code=500, detail=f"종합 분석 오류: {str(e)}")
