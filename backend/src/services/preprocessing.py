"""
데이터 전처리 파이프라인
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from typing import Tuple, List
import structlog

logger = structlog.get_logger()


class PreprocessingService:
    """ML 모델을 위한 데이터 전처리 서비스"""
    
    def __init__(self):
        self.scaler = None
        logger.info("PreprocessingService 초기화")
    
    def normalize_data(
        self, 
        df: pd.DataFrame, 
        method: str = 'minmax',
        fit: bool = True
    ) -> pd.DataFrame:
        """
        데이터 정규화
        
        Args:
            df: 입력 데이터
            method: 'minmax' 또는 'standard'
            fit: True면 scaler를 fitting, False면 기존 scaler 사용
        
        Returns:
            정규화된 DataFrame
        """
        df = df.copy()
        
        # Scaler 선택
        if method == 'minmax':
            if self.scaler is None or fit:
                self.scaler = MinMaxScaler()
        elif method == 'standard':
            if self.scaler is None or fit:
                self.scaler = StandardScaler()
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # 숫자형 컬럼만 정규화
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if fit:
            df[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
        else:
            df[numeric_cols] = self.scaler.transform(df[numeric_cols])
        
        logger.info("데이터 정규화 완료", method=method, columns=len(numeric_cols))
        return df
    
    def create_sequences(
        self,
        data: np.ndarray,
        sequence_length: int = 60,
        target_column: int = 0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        시계열 시퀀스 생성 (슬라이딩 윈도우)
        
        Args:
            data: 입력 데이터 (2D array)
            sequence_length: 시퀀스 길이 (예: 60일)
            target_column: 예측할 컬럼 인덱스
        
        Returns:
            (X, y) - 특성과 타겟
        """
        X, y = [], []
        
        for i in range(len(data) - sequence_length):
            # 입력: i ~ i+sequence_length
            X.append(data[i:i + sequence_length])
            
            # 타겟: i+sequence_length의 target_column 값
            y.append(data[i + sequence_length, target_column])
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(
            "시퀀스 생성 완료",
            sequence_length=sequence_length,
            samples=len(X),
            shape=X.shape
        )
        
        return X, y
    
    def train_val_test_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple:
        """
        학습/검증/테스트 데이터 분리
        
        시계열 데이터이므로 랜덤 셔플 없이 순차적으로 분리
        
        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "비율의 합은 1이어야 합니다"
        
        n = len(X)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        X_train = X[:train_end]
        X_val = X[train_end:val_end]
        X_test = X[val_end:]
        
        y_train = y[:train_end]
        y_val = y[train_end:val_end]
        y_test = y[val_end:]
        
        logger.info(
            "데이터 분리 완료",
            train=len(X_train),
            val=len(X_val),
            test=len(X_test)
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def prepare_for_ml(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        target_column: str = 'close',
        sequence_length: int = 60,
        normalize: bool = True
    ) -> Tuple:
        """
        ML 모델 학습을 위한 전체 파이프라인
        
        Args:
            df: 입력 데이터 (기술적 지표 포함)
            feature_columns: 사용할 특성 컬럼
            target_column: 예측 대상 컬럼
            sequence_length: 시퀀스 길이
            normalize: 정규화 여부
        
        Returns:
            (X_train, X_val, X_test, y_train, y_val, y_test, scaler)
        """
        # 1. 결측치 제거
        df = df[feature_columns + [target_column]].dropna()
        
        # 2. 정규화
        if normalize:
            df_normalized = self.normalize_data(df, method='minmax', fit=True)
        else:
            df_normalized = df
        
        # 3. NumPy 배열로 변환
        data = df_normalized.values
        target_idx = df_normalized.columns.get_loc(target_column)
        
        # 4. 시퀀스 생성
        X, y = self.create_sequences(data, sequence_length, target_idx)
        
        # 5. Train/Val/Test 분리
        X_train, X_val, X_test, y_train, y_val, y_test = self.train_val_test_split(X, y)
        
        logger.info(
            "ML 데이터 준비 완료",
            features=len(feature_columns),
            sequence_length=sequence_length,
            train_samples=len(X_train)
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test, self.scaler
    
    def inverse_transform_predictions(self, predictions: np.ndarray) -> np.ndarray:
        """
        정규화된 예측값을 원래 스케일로 복원
        
        Args:
            predictions: 정규화된 예측값
        
        Returns:
            원래 스케일의 예측값
        """
        if self.scaler is None:
            raise ValueError("Scaler가 초기화되지 않았습니다")
        
        # MinMaxScaler의 경우
        if isinstance(self.scaler, MinMaxScaler):
            # 첫 번째 특성(종가)의 스케일 파라미터 사용
            data_min = self.scaler.data_min_[0]
            data_max = self.scaler.data_max_[0]
            
            return predictions * (data_max - data_min) + data_min
        else:
            # StandardScaler의 경우
            mean = self.scaler.mean_[0]
            scale = self.scaler.scale_[0]
            
            return predictions * scale + mean
