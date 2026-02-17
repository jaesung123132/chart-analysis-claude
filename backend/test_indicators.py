from src.services.feature_engineering import FeatureEngineeringService
from src.services.stock_data_service import StockDataService

# Test
stock_service = StockDataService()
feature_service = FeatureEngineeringService()

# Fetch Apple data
print('[1/3] Fetching AAPL data...')
df = stock_service.fetch_stock_data('AAPL', period='3mo')
print(f'      Success: {len(df)} days of data')

# Calculate technical indicators
print('[2/3] Calculating technical indicators...')
df_indicators = feature_service.calculate_all_indicators(df)
print(f'      Success: {len(df_indicators.columns)} columns total')

# Display latest values
latest = df_indicators.iloc[-1]
print(f'[3/3] Latest indicators ({latest.name.date()}):')
print(f'      Close Price: ${latest["close"]:.2f}')
print(f'      RSI(14): {latest.get("rsi_14", 0):.2f}')
print(f'      MACD: {latest.get("macd", 0):.4f}')
print(f'      BB Upper: ${latest.get("bb_upper", 0):.2f}')
print(f'      BB Lower: ${latest.get("bb_lower", 0):.2f}')
print(f'      SMA(20): ${latest.get("sma_20", 0):.2f}')
print(f'      ATR(14): ${latest.get("atr_14", 0):.2f}')

print('\n==> All technical indicators calculated successfully!')
