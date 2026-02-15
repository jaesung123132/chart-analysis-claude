# 주가 예측 시스템 (Stock Analysis & Prediction System)

고정밀 주가 예측 및 백테스팅 시스템 - ISPAS (Intelligent Stock Price Analysis System)

## 📋 프로젝트 개요

- **목표**: RMSE 1.5% 이하의 고정밀 주가 예측
- **실시간 처리**: 200ms 이하 응답 시간
- **백테스팅**: 10년 데이터 기반 검증
- **XAI**: 설명 가능한 AI (SHAP values)

## 🛠️ 기술 스택

### 백엔드
- **Python**: 3.10+
- **FastAPI**: 0.115+ (비동기 API 프레임워크)
- **PostgreSQL**: 17 + TimescaleDB 2.23
- **Redis**: 7.x (캐싱, 메시지 큐)
- **SQLAlchemy**: 2.x (ORM, async 지원)

### 머신러닝
- **PyTorch**: 2.5+ (LSTM, GRU, Transformer)
- **TensorFlow**: 2.18+ (프로덕션 배포)
- **XGBoost**: 앙상블 모델
- **Optuna**: 하이퍼파라미터 튜닝
- **SHAP**: 모델 설명 가능성

### 프론트엔드
- **React**: 18.x (TypeScript)
- **Vite**: 6.x
- **Tailwind CSS**
- **Recharts**: 차트 시각화

### 인프라
- **Docker**: 컨테이너 기반 배포
- **Celery**: 비동기 작업 큐
- **Nginx**: 리버스 프록시

## 📁 프로젝트 구조

```
chat-project/
├── backend/
│   ├── src/
│   │   ├── api/routers/        # API 엔드포인트
│   │   ├── schemas/            # Pydantic DTO
│   │   ├── services/           # 비즈니스 로직
│   │   ├── repositories/       # 데이터 접근 계층
│   │   ├── models/             # SQLAlchemy 모델
│   │   ├── ml_models/          # 머신러닝 모델
│   │   ├── infrastructure/     # DB, API 클라이언트
│   │   └── core/               # 설정, 예외
│   ├── tests/                  # 테스트
│   ├── notebooks/              # Jupyter 노트북
│   └── pyproject.toml          # 의존성 관리
├── frontend/                   # React 프론트엔드
├── data/                       # 데이터 저장소
├── docker-compose.yml          # 인프라 구성
└── ROADMAP.html                # 프로젝트 로드맵
```

## 🚀 빠른 시작

### 1. 사전 요구사항

- **Python 3.10+** ([다운로드](https://www.python.org/downloads/))
- **Docker Desktop** ([다운로드](https://www.docker.com/products/docker-desktop/))
- **Poetry** (선택적): `pip install poetry`

### 2. 환경 설정

```bash
# 저장소 클론
cd chat-project

# 가상환경 생성 (Poetry 사용 시)
cd backend
poetry install

# 또는 venv 사용
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 등 설정
```

### 3. Docker 인프라 실행 (다음 단계에서 구성 예정)

```bash
# PostgreSQL, Redis 시작
docker compose up -d

# 데이터베이스 마이그레이션
alembic upgrade head
```

### 4. 개발 서버 실행

```bash
# 백엔드 API 서버
cd backend
uvicorn src.main:app --reload

# API 문서: http://localhost:8000/docs
```

## 📊 개발 로드맵

### Phase 1: 기반 구축 (Week 1-2) ✅ 진행 중
- [x] 프로젝트 구조 생성
- [x] Python 환경 설정
- [ ] Docker 인프라 구성
- [ ] 데이터베이스 설계
- [ ] 외부 API 연동

### Phase 2: EDA (Week 3-4)
- [ ] 데이터 수집 스크립트
- [ ] 기술적 지표 계산 (15종+)
- [ ] EDA 노트북 작성
- [ ] 데이터 전처리 파이프라인

### Phase 3: 모델 개발 (Week 5-8)
- [ ] PyTorch LSTM/Transformer
- [ ] TensorFlow 모델
- [ ] XGBoost 앙상블
- [ ] 하이퍼파라미터 튜닝 (Optuna)
- [ ] XAI 구현 (SHAP)

### Phase 4: 백테스팅 (Week 9-10)
- [ ] 백테스팅 엔진
- [ ] 10년 시뮬레이션
- [ ] 투자 지표 산출
- [ ] 스트레스 테스트

### Phase 5: API & UI (Week 11-12)
- [ ] FastAPI 엔드포인트
- [ ] React 대시보드
- [ ] 실시간 예측 UI
- [ ] 배포 설정

## 🧪 테스트

```bash
# 단위 테스트
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트
pytest tests/test_api.py -v
```

## 📖 API 문서

개발 서버 실행 후:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 코드 품질

```bash
# 린터 (Ruff)
ruff check src/

# 포매터 (Black)
black src/

# 타입 체크 (mypy)
mypy src/
```

## 📝 라이선스

MIT License

## 👥 기여

이슈 및 PR은 언제든 환영합니다!

## 📞 문의

프로젝트 관련 문의: [이메일 주소]

---

**현재 상태**: Phase 1 진행 중 (프로젝트 기본 구조 완료)
