"""
기술적 지표 API 라우터
"""
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from ...schemas.stock import APIResponse
from ...services.stock_data_service import StockDataService
from ...services.feature_engineering import FeatureEngineeringService
from ...core.exceptions import StockNotFoundException, DataFetchException
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/stocks", tags=["indicators"])
stock_service = StockDataService()
feature_service = FeatureEngineeringService()


@router.get("/{ticker}/indicators")
async def get_technical_indicators(
    ticker: str,
    period: str = Query(default="1y", description="조회 기간"),
    summary: bool = Query(default=False, description="최신 값만 요약해서 반환")
):
    """
    종목의 기술적 지표 조회
    
    **계산되는 지표:**
    - **추세**: SMA (20, 50, 200일), EMA (12, 26일), MACD
    - **모멘텀**: RSI (14일), Stochastic (K, D)
    - **변동성**: Bollinger Bands, ATR (14일)
    - **거래량**: OBV, VWAP
    
    **파라미터:**
    - **ticker**: 종목 코드
    - **period**: 조회 기간 (1mo, 3mo, 6mo, 1y, 2y, 5y)
    - **summary**: True면 최신 값만 반환, False면 전체 시계열 반환
    """
    try:
        # 주가 데이터 조회
        df = stock_service.fetch_stock_data(ticker.upper(), period)
        
        # 기술적 지표 계산
        df_with_indicators = feature_service.calculate_all_indicators(df)
        
        if summary:
            # 최신 지표 값만 요약
            result = feature_service.get_indicator_summary(df_with_indicators, ticker.upper())
        else:
            # 전체 시계열 데이터 반환
            data = []
            for date, row in df_with_indicators.iterrows():
                data.append({
                    "date": date.isoformat(),
                    "close": float(row.get('close', 0)),
                    "sma_20": float(row.get('sma_20', 0)) if not pd.isna(row.get('sma_20')) else None,
                    "sma_50": float(row.get('sma_50', 0)) if not pd.isna(row.get('sma_50')) else None,
                    "ema_12": float(row.get('ema_12', 0)) if not pd.isna(row.get('ema_12')) else None,
                    "rsi_14": float(row.get('rsi_14', 0)) if not pd.isna(row.get('rsi_14')) else None,
                    "macd": float(row.get('macd', 0)) if not pd.isna(row.get('macd')) else None,
                    "macd_signal": float(row.get('macd_signal', 0)) if not pd.isna(row.get('macd_signal')) else None,
                    "bb_upper": float(row.get('bb_upper', 0)) if not pd.isna(row.get('bb_upper')) else None,
                    "bb_middle": float(row.get('bb_middle', 0)) if not pd.isna(row.get('bb_middle')) else None,
                    "bb_lower": float(row.get('bb_lower', 0)) if not pd.isna(row.get('bb_lower')) else None,
                    "atr_14": float(row.get('atr_14', 0)) if not pd.isna(row.get('atr_14')) else None,
                })
            
            result = {
                "ticker": ticker.upper(),
                "period": period,
                "count": len(data),
                "indicators": data
            }
        
        return APIResponse(
            success=True,
            data=result,
            message="기술적 지표 조회 성공",
            timestamp=datetime.utcnow()
        )
        
    except StockNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DataFetchException as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("기술적 지표 계산 실패", ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail=f"지표 계산 오류: {str(e)}")


@router.get("/{ticker}/signals")
async def get_trading_signals(ticker: str):
    """
    매매 시그널 분석
    
    기술적 지표를 기반으로 매수/매도/중립 시그널 생성
    """
    try:
        # 주가 데이터 조회 (6개월)
        df = stock_service.fetch_stock_data(ticker.upper(), period="6mo")
        df_with_indicators = feature_service.calculate_all_indicators(df)
        
        # 최신 데이터
        latest = df_with_indicators.iloc[-1]
        
        signals = []
        
        # 1. RSI 시그널
        rsi = latest.get('rsi_14', 50)
        if rsi < 30:
            signals.append({"indicator": "RSI", "signal": "BUY", "reason": f"과매도 구간 (RSI: {rsi:.1f})"})
        elif rsi > 70:
            signals.append({"indicator": "RSI", "signal": "SELL", "reason": f"과매수 구간 (RSI: {rsi:.1f})"})
        else:
            signals.append({"indicator": "RSI", "signal": "NEUTRAL", "reason": f"중립 (RSI: {rsi:.1f})"})
        
        # 2. MACD 시그널
        macd = latest.get('macd', 0)
        macd_signal = latest.get('macd_signal', 0)
        if macd > macd_signal:
            signals.append({"indicator": "MACD", "signal": "BUY", "reason": "MACD가 시그널선 상향 돌파"})
        else:
            signals.append({"indicator": "MACD", "signal": "SELL", "reason": "MACD가 시그널선 하향 돌파"})
        
        # 3. 이동평균선 시그널
        close = latest.get('close', 0)
        sma_20 = latest.get('sma_20', 0)
        sma_50 = latest.get('sma_50', 0)
        
        if close > sma_20 and close > sma_50:
            signals.append({"indicator": "MA", "signal": "BUY", "reason": "가격이 이동평균선 위"})
        elif close < sma_20 and close < sma_50:
            signals.append({"indicator": "MA", "signal": "SELL", "reason": "가격이 이동평균선 아래"})
        else:
            signals.append({"indicator": "MA", "signal": "NEUTRAL", "reason": "혼조"})
        
        # 4. AI 예측 방향 시그널
        try:
            from ...services.prediction_service import PredictionService
            ps = PredictionService()
            pred = ps.predict_future(ticker.upper(), days=7)
            current_price = pred['current_price']
            last_pred = pred['predictions'][-1]['predicted_price']
            pred_change = ((last_pred - current_price) / current_price) * 100
            avg_conf = sum(p.get('confidence', 0.5) for p in pred['predictions']) / len(pred['predictions'])

            if pred_change > 2:
                signals.append({
                    "indicator": "AI예측",
                    "signal": "BUY",
                    "reason": f"7일 후 {pred_change:+.1f}% 상승 예측 (신뢰도 {avg_conf*100:.0f}%)"
                })
            elif pred_change < -2:
                signals.append({
                    "indicator": "AI예측",
                    "signal": "SELL",
                    "reason": f"7일 후 {pred_change:+.1f}% 하락 예측 (신뢰도 {avg_conf*100:.0f}%)"
                })
            else:
                signals.append({
                    "indicator": "AI예측",
                    "signal": "NEUTRAL",
                    "reason": f"7일 후 {pred_change:+.1f}% 보합 예측 (신뢰도 {avg_conf*100:.0f}%)"
                })
        except Exception as pred_err:
            logger.warning("시그널 분석 중 AI 예측 실패", error=str(pred_err))

        # 종합 시그널
        buy_count = sum(1 for s in signals if s["signal"] == "BUY")
        sell_count = sum(1 for s in signals if s["signal"] == "SELL")

        if buy_count > sell_count:
            overall = "BUY"
        elif sell_count > buy_count:
            overall = "SELL"
        else:
            overall = "NEUTRAL"

        return APIResponse(
            success=True,
            data={
                "ticker": ticker.upper(),
                "overall_signal": overall,
                "signals": signals,
                "current_price": float(close),
                "analysis_date": str(latest.name)
            },
            message="매매 시그널 분석 완료",
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("시그널 분석 실패", ticker=ticker, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

import pandas as pd
