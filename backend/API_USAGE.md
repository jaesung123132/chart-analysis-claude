# ISPAS API 사용 가이드

## 🔗 주요 엔드포인트

### 1. 헬스 체크
**요청:**
```bash
GET http://localhost:8000/health
```

**응답:**
```json
{
  "status": "healthy",
  "service": "ispas-api"
}
```

---

### 2. API 정보 조회
**요청:**
```bash
GET http://localhost:8000/
```

**응답:**
```json
{
  "message": "ISPAS API Server",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/api/v1/stocks/health"
}
```

---

### 3. 주가 데이터 조회 ⭐
**엔드포인트:**
```
GET /api/v1/stocks/{ticker}/prices
```

**파라미터:**
- `ticker` (필수): 종목 코드 (예: AAPL, MSFT, TSLA)
- `period` (선택): 조회 기간 (기본값: 1y)
  - 가능한 값: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max
- `interval` (선택): 데이터 간격 (기본값: 1d)
  - 가능한 값: 1d, 1wk, 1mo

**예시 1: Apple 1년 주가**
```bash
curl "http://localhost:8000/api/v1/stocks/AAPL/prices?period=1y"
```

**예시 2: Microsoft 3개월 주가**
```bash
curl "http://localhost:8000/api/v1/stocks/MSFT/prices?period=3mo&interval=1d"
```

**응답:**
```json
{
  "success": true,
  "data": {
    "ticker": "AAPL",
    "period": "1y",
    "interval": "1d",
    "count": 252,
    "prices": [
      {
        "date": "2025-02-14T00:00:00",
        "open": 226.08,
        "high": 228.0,
        "low": 225.27,
        "close": 227.79,
        "volume": 42834900
      },
      {
        "date": "2025-02-13T00:00:00",
        "open": 228.5,
        "high": 229.39,
        "low": 226.21,
        "close": 226.63,
        "volume": 44523100
      }
    ]
  },
  "message": "주가 데이터 조회 성공",
  "timestamp": "2026-02-15T12:00:00.000Z"
}
```

---

### 4. 종목 정보 조회 ⭐
**엔드포인트:**
```
GET /api/v1/stocks/{ticker}/info
```

**예시: Tesla 정보**
```bash
curl "http://localhost:8000/api/v1/stocks/TSLA/info"
```

**응답:**
```json
{
  "success": true,
  "data": {
    "ticker": "TSLA",
    "name": "Tesla, Inc.",
    "sector": "Consumer Cyclical",
    "industry": "Auto Manufacturers",
    "market_cap": 724963000000,
    "currency": "USD"
  },
  "message": "종목 정보 조회 성공",
  "timestamp": "2026-02-15T12:00:00.000Z"
}
```

---

## 🌐 브라우저에서 사용

API 서버 실행 후 브라우저에서 직접 접속 가능:

### Swagger UI (추천)
```
http://localhost:8000/docs
```
- 모든 API를 UI에서 바로 테스트 가능
- "Try it out" 버튼 클릭 → 파라미터 입력 → "Execute"

### ReDoc
```
http://localhost:8000/redoc
```
- 읽기 쉬운 문서 형식

### 직접 URL 접속
```
http://localhost:8000/api/v1/stocks/AAPL/prices?period=1mo
```

---

## 🐍 Python에서 사용

### 방법 1: requests 사용
```python
import requests

# 주가 데이터 조회
response = requests.get(
    "http://localhost:8000/api/v1/stocks/AAPL/prices",
    params={"period": "1y", "interval": "1d"}
)

data = response.json()
if data["success"]:
    prices = data["data"]["prices"]
    print(f"총 {len(prices)}일 데이터 조회")
    print(f"최근 종가: ${prices[0]['close']}")
```

### 방법 2: pandas로 DataFrame 변환
```python
import requests
import pandas as pd

# API 호출
response = requests.get("http://localhost:8000/api/v1/stocks/AAPL/prices?period=1y")
data = response.json()

# DataFrame으로 변환
if data["success"]:
    df = pd.DataFrame(data["data"]["prices"])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    print(df.head())
    print(f"\n평균 종가: ${df['close'].mean():.2f}")
    print(f"최고가: ${df['high'].max():.2f}")
    print(f"최저가: ${df['low'].min():.2f}")
```

---

## 📊 실전 예제

### 여러 종목 비교
```python
import requests
import pandas as pd
import matplotlib.pyplot as plt

tickers = ["AAPL", "MSFT", "GOOGL"]
all_data = {}

for ticker in tickers:
    response = requests.get(
        f"http://localhost:8000/api/v1/stocks/{ticker}/prices",
        params={"period": "6mo"}
    )
    data = response.json()
    
    if data["success"]:
        df = pd.DataFrame(data["data"]["prices"])
        df['date'] = pd.to_datetime(df['date'])
        all_data[ticker] = df.set_index('date')['close']

# 그래프 그리기
combined = pd.DataFrame(all_data)
combined.plot(figsize=(12, 6), title="6개월 주가 비교")
plt.ylabel("Price ($)")
plt.show()
```

---

## ❌ 에러 처리

### 404 Not Found (종목 없음)
```json
{
  "detail": "종목을 찾을 수 없습니다: INVALIDTICKER"
}
```

### 503 Service Unavailable (API 오류)
```json
{
  "detail": "데이터 조회 실패: ..."
}
```

### 500 Internal Server Error
```json
{
  "detail": "내부 서버 오류"
}
```

---

## 🔍 지원 종목

### 미국 주식
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- NVDA (Nvidia)
- META (Meta/Facebook)
- ... 기타 모든 미국 상장 주식

### 한국 주식
종목 코드에 `.KS` (KOSPI) 또는 `.KQ` (KOSDAQ) 추가:
- 005930.KS (삼성전자)
- 000660.KS (SK하이닉스)
- 035420.KS (NAVER)

**예시:**
```bash
curl "http://localhost:8000/api/v1/stocks/005930.KS/prices?period=1y"
```

---

## 💡 팁

1. **Swagger UI 활용**: `/docs`에서 모든 API를 쉽게 테스트
2. **기간 선택**: 장기 분석은 5y, 단기는 1mo 사용
3. **캐싱**: 같은 요청은 빠르게 응답 (Redis 캐싱)
4. **에러 확인**: `success: false`일 때 `message` 확인

