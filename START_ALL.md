# 🚀 ISPAS 전체 시스템 실행 가이드

## 실행 순서

### 1. 백엔드 API 서버 실행

**터미널 1:**
```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

**확인:**
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/health

---

### 2. 프론트엔드 React 서버 실행

**터미널 2:**
```bash
cd frontend
npm run dev
```

**확인:**
- http://localhost:3000

---

## 사용 방법

1. **브라우저에서 접속**: http://localhost:3000

2. **종목 입력**: AAPL, MSFT, TSLA 등

3. **"분석하기" 버튼 클릭**
   - 주가 데이터 조회
   - 기술적 지표 계산
   - 매매 시그널 분석
   - **AI 예측 (7일)** ⭐

4. **결과 확인**:
   - 현재가, RSI, MACD, 매매 시그널
   - 주가 차트 (실제 + AI 예측)
   - 7일 예측 가격
   - 상세 기술적 지표

---

## 지원 종목

### 미국 주식
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- NVDA (Nvidia)
- META (Meta)

### 한국 주식
- 005930.KS (삼성전자)
- 000660.KS (SK하이닉스)
- 035420.KS (NAVER)

---

## 주요 기능

✅ 실시간 주가 조회 (Yahoo Finance)
✅ 기술적 지표 15종 (RSI, MACD, Bollinger Bands 등)
✅ AI 매매 시그널 (BUY/SELL/NEUTRAL)
✅ **LSTM 딥러닝 모델 주가 예측** ⭐
✅ 인터랙티브 차트
✅ 반응형 UI (모바일 지원)

---

## 문제 해결

### 포트 충돌
```bash
# 백엔드를 다른 포트로
uvicorn src.main:app --port 8001

# 프론트엔드 vite.config.js에서 포트 변경
```

### CORS 오류
- 백엔드가 먼저 실행되어야 함
- vite.config.js의 proxy 설정 확인

### 모델 로드 실패
- `backend/models/weights/lstm_aapl.pt` 파일 확인
- 없으면 `python train_model.py` 재실행
