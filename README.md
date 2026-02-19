# ISPAS - Intelligent Stock Price Analysis System

AI 기반 종합 주식 투자 분석 시스템 (v1.0.1)

## 프로젝트 개요

단순한 주가 확인 도구가 아닌, **기본적 분석 + 기술적 분석 + AI 예측**을 통합한 종합 투자 판단 보조 시스템입니다.

### 핵심 기능

- **종합 투자 판단**: 기본적(40%) + 기술적(30%) + AI 예측(30%) 3축 통합 스코어 (0-100점, A+~D 등급)
- **기본적 분석**: PER/PBR/PEG 가치평가, 수익성, 재무건전성, 애널리스트 목표가 분석
- **기술적 분석**: 20+ 기술적 지표, 캔들 패턴 인식, 골든/데드크로스, 지지선/저항선
- **AI 주가 예측**: LSTM 모델 7일 예측 + Gradient Feature Importance + Monte Carlo 신뢰도
- **모순 감지**: 기술적 시그널과 AI 예측 방향이 충돌하면 자동 경고 및 등급 조정
- **오차 보정**: 과거 예측 오차를 가중 이동평균으로 분석하여 예측 보정

## 기술 스택

### 백엔드
- Python 3.11+ / FastAPI
- SQLAlchemy 2.x (async) + SQLite (개발) / PostgreSQL (프로덕션)
- PyTorch (LSTM 예측 모델)
- yfinance (Yahoo Finance 데이터)
- structlog (구조화 로깅)

### 프론트엔드
- React 18 / Vite 6
- Tailwind CSS
- Recharts (데이터 시각화)
- Axios (HTTP 클라이언트)

## 시작하기

### 사전 요구사항
- Python 3.11 이상
- Node.js 18+ (프론트엔드)

### 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

### API 문서

백엔드 실행 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/v1/stocks/{ticker}/prices` | 주가 데이터 조회 |
| GET | `/api/v1/stocks/{ticker}/info` | 종목 정보 |
| POST | `/api/v1/stocks/batch-prices` | 다중 종목 일괄 조회 |
| GET | `/api/v1/stocks/{ticker}/indicators` | 기술적 지표 (summary 옵션) |
| GET | `/api/v1/stocks/{ticker}/signals` | 매매 시그널 (RSI/MACD/MA/AI예측) |
| GET | `/api/v1/predictions/{ticker}` | 7일 주가 예측 + 오차 보정 |
| GET | `/api/v1/predictions/{ticker}/history` | 과거 예측 기록 |
| GET | `/api/v1/predictions/{ticker}/accuracy` | 예측 정확도 분석 |
| POST | `/api/v1/predictions/{ticker}/update-actuals` | 실제 가격 업데이트 |
| GET | `/api/v1/analysis/{ticker}/fundamental` | 기본적 분석 |
| GET | `/api/v1/analysis/{ticker}/comprehensive` | 종합 투자 판단 |
| GET | `/api/v1/search` | 한글/영문 종목 검색 |

## 프로젝트 구조

```
chat-project/
├── backend/
│   ├── src/
│   │   ├── api/routers/        # FastAPI 라우터 (stocks, indicators, predictions, search, analysis)
│   │   ├── schemas/            # Pydantic DTO
│   │   ├── services/           # 비즈니스 로직
│   │   │   ├── prediction_service.py        # LSTM 예측 + Feature Importance + 신뢰도
│   │   │   ├── fundamental_service.py       # 기본적 분석 (PER/PBR/수익성/재무)
│   │   │   ├── investment_score_service.py  # 종합 투자 판단 (3축 통합)
│   │   │   ├── feature_engineering.py       # 기술적 지표 + 패턴/크로스/지지저항
│   │   │   ├── error_correction_service.py  # 오차 보정
│   │   │   ├── stock_data_service.py        # 주가 데이터 조회
│   │   │   └── preprocessing.py             # 데이터 전처리
│   │   ├── repositories/       # 데이터 액세스 계층
│   │   ├── models/             # SQLAlchemy ORM 모델
│   │   ├── ml_models/          # LSTM 모델 정의
│   │   ├── infrastructure/     # DB, Yahoo Finance 클라이언트
│   │   ├── core/               # 설정, 예외
│   │   └── main.py             # FastAPI 앱 엔트리포인트
│   └── models/weights/         # 학습된 모델 가중치
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── StockDashboard.jsx       # 메인 대시보드 (5탭 구조)
│       │   ├── InvestmentScore.jsx      # 종합 투자 판단 UI
│       │   ├── FundamentalAnalysis.jsx  # 기본적 분석 UI
│       │   ├── TechnicalAnalysis.jsx    # 기술적 분석 UI
│       │   ├── PredictionAccuracy.jsx   # 예측 정확도 UI
│       │   ├── StockSearch.jsx          # 종목 검색 (자동완성)
│       │   └── Favorite*.jsx            # 즐겨찾기 관련
│       └── hooks/               # useFavorites, useDebounce
└── README.md
```

## 아키텍처

- **레이어드 아키텍처**: Router → Service → Repository
- **DTO 패턴**: Pydantic 스키마로 요청/응답 검증
- **비동기 처리**: FastAPI + async SQLAlchemy
- **종합 판단 로직**: 기본적 분석(Yahoo Finance info) + 기술적 분석(20+ 지표) + LSTM 예측을 3축으로 통합, 모순 감지 시 자동 등급 조정

## 라이선스

MIT License
