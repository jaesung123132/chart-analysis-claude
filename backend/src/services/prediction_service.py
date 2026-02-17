"""
주가 예측 서비스
"""
import torch
import numpy as np
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
    
    def predict_future(
        self, 
        ticker: str, 
        days: int = 7
    ) -> Dict:
        """
        미래 주가 예측
        
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
        feature_cols = ['volume', 'rsi_14', 'macd', 'bb_upper', 'bb_lower', 'sma_20', 'ema_12']
        target_col = 'close'
        
        # 데이터 준비
        df_clean = df_indicators[feature_cols + [target_col]].dropna()
        
        # 정규화
        df_normalized = self.prep_service.normalize_data(df_clean, method='minmax', fit=True)
        
        # 최근 60일 데이터
        recent_data = df_normalized.values[-60:]
        
        # 3. 예측
        predictions = []
        current_price = df['close'].iloc[-1]
        
        # 반복적으로 예측 (Autoregressive)
        input_sequence = recent_data.copy()
        
        for _ in range(days):
            # 시퀀스를 모델 입력 형태로 변환
            X = input_sequence.reshape(1, 60, -1)
            
            # 예측
            with torch.no_grad():
                pred_normalized = self.model.predict(X, device='cpu')[0][0]
            
            # 역정규화 (첫 번째 특성이 close)
            scaler = self.prep_service.scaler
            pred_price = pred_normalized * (scaler.data_max_[7] - scaler.data_min_[7]) + scaler.data_min_[7]
            
            predictions.append(float(pred_price))
            
            # 다음 입력을 위해 시퀀스 업데이트 (간단히 마지막 값을 복사)
            # 실제로는 예측된 값으로 특성을 재계산해야 하지만, 여기서는 간소화
            input_sequence = np.roll(input_sequence, -1, axis=0)
            input_sequence[-1] = input_sequence[-2]  # 단순화
        
        # 4. 결과 구성
        last_date = df.index[-1]
        prediction_dates = [
            (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
            for i in range(days)
        ]
        
        return {
            'ticker': ticker,
            'current_price': float(current_price),
            'predictions': [
                {'date': date, 'predicted_price': pred}
                for date, pred in zip(prediction_dates, predictions)
            ],
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
            원시 예측 + 보정 예측 + 보정 정보 포함 딕셔너리
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
            corrected_price = self.error_correction_service.apply_correction(raw_price, correction_info)

            # DB에는 원시 예측값 저장 (실제 가격과 비교하여 오차 보정 모델 개선용)
            pred = Prediction(
                stock_id=stock.id,
                prediction_date=now,
                target_date=datetime.strptime(item['date'], '%Y-%m-%d'),
                predicted_price=raw_price,
                model_name='lstm',
                model_version='1.0',
            )
            prediction_objects.append(pred)
            corrected_predictions.append({
                'date': item['date'],
                'predicted_price': raw_price,
                'corrected_price': round(corrected_price, 4)
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
            'correction_info': correction_info,
            'prediction_date': now.isoformat(),
            'model': 'LSTM'
        }
