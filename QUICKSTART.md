# 🚀 ISPAS API 빠른 시작 가이드

## 1. 서버 실행 (3단계)

```bash
# 1단계: 백엔드 디렉토리로 이동
cd backend

# 2단계: 필수 패키지 설치
pip install yfinance pandas fastapi uvicorn pydantic pydantic-settings structlog

# 3단계: 서버 실행
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**서버 실행 확인:**
```
✅ Uvicorn running on http://0.0.0.0:8000
```

---

## 2. API 사용법

### 방법 1: 브라우저에서 바로 테스트 (가장 쉬움!)

서버 실행 후 브라우저에서 접속:
```
http://localhost:8000/docs
```

👉 **Swagger UI가 열립니다!**
- 모든 API를 클릭해서 바로 테스트 가능
- "Try it out" → 파라미터 입력 → "Execute"

---

### 방법 2: 브라우저 주소창에 직접 입력

```
# Apple 최근 1개월 주가
http://localhost:8000/api/v1/stocks/AAPL/prices?period=1mo

# Microsoft 정보
http://localhost:8000/api/v1/stocks/MSFT/info

# Tesla 1년 주가
http://localhost:8000/api/v1/stocks/TSLA/prices?period=1y
```

---

### 방법 3: Python 코드로 사용

```python
import requests

# 주가 조회
response = requests.get(
    "http://localhost:8000/api/v1/stocks/AAPL/prices",
    params={"period": "1mo"}
)

data = response.json()
if data["success"]:
    prices = data["data"]["prices"]
    print(f"최근 종가: ${prices[0]['close']:.2f}")
```

---

### 방법 4: curl 명령어

```bash
# 헬스 체크
curl http://localhost:8000/health

# 주가 조회
curl "http://localhost:8000/api/v1/stocks/AAPL/prices?period=1mo"

# 종목 정보
curl "http://localhost:8000/api/v1/stocks/TSLA/info"
```

---

## 3. 주요 엔드포인트

| 엔드포인트 | 설명 | 예시 |
|-----------|------|------|
| `GET /health` | 서버 상태 확인 | `/health` |
| `GET /docs` | API 문서 (Swagger) | `/docs` |
| `GET /api/v1/stocks/{ticker}/prices` | 주가 데이터 | `/api/v1/stocks/AAPL/prices?period=1y` |
| `GET /api/v1/stocks/{ticker}/info` | 종목 정보 | `/api/v1/stocks/TSLA/info` |

---

## 4. 파라미터 옵션

### period (조회 기간)
- `1d` - 1일
- `5d` - 5일
- `1mo` - 1개월
- `3mo` - 3개월
- `6mo` - 6개월
- `1y` - 1년 (기본값)
- `2y` - 2년
- `5y` - 5년
- `10y` - 10년
- `max` - 전체

### interval (데이터 간격)
- `1d` - 일봉 (기본값)
- `1wk` - 주봉
- `1mo` - 월봉

---

## 5. 지원 종목

### 미국 주식 (종목 코드 그대로)
```
AAPL    - Apple
MSFT    - Microsoft
GOOGL   - Google
AMZN    - Amazon
TSLA    - Tesla
NVDA    - Nvidia
META    - Meta (Facebook)
```

### 한국 주식 (종목코드.KS 또는 .KQ)
```
005930.KS  - 삼성전자
000660.KS  - SK하이닉스
035420.KS  - NAVER
```

---

## 6. 응답 형식

모든 API는 동일한 형식으로 응답:

```json
{
  "success": true,
  "data": { ... },
  "message": "성공 메시지",
  "timestamp": "2026-02-15T12:00:00Z"
}
```

---

## 7. 실전 예제

### 여러 종목 비교 분석

```python
import requests
import pandas as pd

tickers = ["AAPL", "MSFT", "GOOGL"]

for ticker in tickers:
    res = requests.get(
        f"http://localhost:8000/api/v1/stocks/{ticker}/prices",
        params={"period": "1y"}
    )
    data = res.json()
    
    if data["success"]:
        prices = data["data"]["prices"]
        latest = prices[0]
        print(f"{ticker}: ${latest['close']:.2f}")
```

---

## 📚 상세 문서

- 서버 실행: `backend/START_SERVER.md`
- API 사용법: `backend/API_USAGE.md`
- 프로젝트 구조: `README.md`

---

## 💡 팁

1. **가장 쉬운 방법**: `/docs`에서 Swagger UI 사용!
2. **빠른 확인**: 브라우저 주소창에 URL 직접 입력
3. **프로그래밍**: Python requests 라이브러리 사용
4. **문제 발생 시**: 서버 로그 확인

**즐거운 주가 분석 되세요! 📈**
