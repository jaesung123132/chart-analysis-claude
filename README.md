# ISPAS - Intelligent Stock Price Analysis System

주가 예측을 위한 하이브리드 머신러닝 시스템

## 프로젝트 개요

- **목표 예측 정확도**: RMSE 1.5% 이하
- **데이터 처리 지연시간**: < 200ms
- **백테스팅 기간**: 10년 (2014-2024)
- **설명 가능한 AI (XAI)**: SHAP values 기반 예측 근거 제시

## 기술 스택

### 백엔드
- Python 3.14
- FastAPI 0.129.0
- PostgreSQL 17 + TimescaleDB 2.23
- SQLAlchemy 2.x (async)
- Redis 7.x

### 머신러닝
- PyTorch 2.10.0 (연구/개발)
- TensorFlow 2.20.0 (프로덕션 배포)
- XGBoost, Scikit-learn
- Optuna (하이퍼파라미터 튜닝)
- SHAP (모델 설명)

### 프론트엔드
- React 18.x LTS
- TypeScript 5.x
- Tailwind CSS
- Vite 6.x
- Recharts

### 인프라
- Docker Engine 29.x
- Docker Compose v5
- Nginx
- Celery (비동기 작업 큐)

## 시작하기

### 사전 요구사항

- Docker 29.x 이상
- Docker Compose v5 이상
- Python 3.14 (로컬 개발용)
- Node.js 24.x LTS (프론트엔드 개발용)

### 설치 및 실행

1. **환경변수 설정**
\`\`\`bash
cp backend/.env.example backend/.env
# .env 파일을 편집하여 API 키 등을 설정
\`\`\`

2. **Docker Compose로 인프라 시작**
\`\`\`bash
docker compose up -d
\`\`\`

3. **데이터베이스 마이그레이션**
\`\`\`bash
cd backend
alembic upgrade head
\`\`\`

4. **백엔드 API 실행**
\`\`\`bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

5. **프론트엔드 개발 서버**
\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

### API 문서

백엔드 실행 후 다음 URL에서 API 문서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

\`\`\`
chat-project/
├── backend/
│   ├── src/
│   │   ├── api/routers/      # FastAPI 라우터
│   │   ├── schemas/          # Pydantic DTO
│   │   ├── services/         # 비즈니스 로직
│   │   ├── repositories/     # 데이터 액세스
│   │   ├── models/           # SQLAlchemy 모델
│   │   ├── ml_models/        # PyTorch/TF 모델
│   │   ├── infrastructure/   # DB, API 클라이언트
│   │   ├── core/             # 설정, 예외
│   │   └── main.py           # FastAPI 앱
│   ├── tests/
│   ├── notebooks/            # Jupyter 노트북
│   └── models/weights/       # 학습된 모델
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── stores/           # Zustand 상태 관리
│       └── services/         # API 클라이언트
├── docker-compose.yml
└── ROADMAP.html
\`\`\`

## 개발 로드맵

- [x] Phase 1: 기반 구축 및 데이터 수집 (Week 1-2)
- [ ] Phase 2: 탐색적 데이터 분석 (Week 3-4)
- [ ] Phase 3: 예측 모델 개발 (Week 5-8)
- [ ] Phase 4: 백테스팅 및 검증 (Week 9-10)
- [ ] Phase 5: API 개발 및 UI 구축 (Week 11-12)

## 라이선스

MIT License

## 기여

이슈 및 PR 환영합니다!
