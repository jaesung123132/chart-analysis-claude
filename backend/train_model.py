"""
LSTM 모델 학습 스크립트
"""
import sys
import numpy as np
from src.services.stock_data_service import StockDataService
from src.services.feature_engineering import FeatureEngineeringService
from src.services.preprocessing import PreprocessingService
from src.ml_models.lstm_model import LSTMPredictor, ModelTrainer, calculate_metrics

print("="*60)
print("LSTM Stock Price Prediction - Training Script")
print("="*60)

# 1. 데이터 수집
print("\n[1/5] Fetching data...")
stock_service = StockDataService()
feature_service = FeatureEngineeringService()
prep_service = PreprocessingService()

ticker = 'AAPL'
df = stock_service.fetch_stock_data(ticker, period='2y')
print(f"  -> Fetched {len(df)} days of data for {ticker}")

# 2. 기술적 지표 계산
print("\n[2/5] Calculating technical indicators...")
df_indicators = feature_service.calculate_all_indicators(df)
print(f"  -> Generated {len(df_indicators.columns)} features")

# 3. 데이터 전처리
print("\n[3/5] Preprocessing data...")
feature_cols = ['volume', 'rsi_14', 'macd', 'bb_upper', 'bb_lower', 'sma_20', 'ema_12']
target_col = 'close'

X_train, X_val, X_test, y_train, y_val, y_test, scaler = prep_service.prepare_for_ml(
    df_indicators,
    feature_columns=feature_cols,
    target_column=target_col,
    sequence_length=60,
    normalize=True
)

print(f"  -> Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
print(f"  -> Input shape: {X_train.shape}")

# 4. 모델 학습
print("\n[4/5] Training LSTM model...")
model = LSTMPredictor(
    input_size=X_train.shape[2],
    hidden_size=64,
    num_layers=2,
    dropout=0.2
)

trainer = ModelTrainer(model, learning_rate=0.001, device='cpu')

history = trainer.fit(
    X_train, y_train,
    X_val, y_val,
    epochs=30,
    batch_size=32,
    patience=10
)

# 5. 평가
print("\n[5/5] Evaluating model...")
y_pred_val = model.predict(X_val, device='cpu').flatten()
metrics_val = calculate_metrics(y_val, y_pred_val)

y_pred_test = model.predict(X_test, device='cpu').flatten()
metrics_test = calculate_metrics(y_test, y_pred_test)

print("\nValidation Metrics:")
print(f"  RMSE: {metrics_val['rmse']:.6f}")
print(f"  MAE:  {metrics_val['mae']:.6f}")
print(f"  R2:   {metrics_val['r2']:.4f}")

print("\nTest Metrics:")
print(f"  RMSE: {metrics_test['rmse']:.6f}")
print(f"  MAE:  {metrics_test['mae']:.6f}")
print(f"  R2:   {metrics_test['r2']:.4f}")

# 모델 저장
model_path = 'models/weights/lstm_aapl.pt'
trainer.save_model(model_path)
print(f"\nModel saved to: {model_path}")

print("\n" + "="*60)
print("Training completed successfully!")
print("="*60)
