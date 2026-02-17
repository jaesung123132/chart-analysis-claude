# ISPAS API 서버 실행 가이드

## 방법 1: 로컬에서 바로 실행 (개발용)

### 1단계: 백엔드 디렉토리 이동
```bash
cd backend
```

### 2단계: 필수 패키지 설치
```bash
pip install -r requirements.txt
```

### 3단계: 환경변수 설정 (선택사항)
```bash
# .env 파일이 없으면 .env.example을 복사
cp .env.example .env
```

### 4단계: API 서버 실행
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**성공 메시지:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 5단계: API 접속 확인
브라우저에서 다음 URL 접속:
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/health

---

## 방법 2: Docker Compose로 실행 (프로덕션)

### 1단계: 환경변수 설정
```bash
cp backend/.env.example backend/.env
```

### 2단계: Docker Compose 실행
```bash
docker compose up -d
```

### 3단계: 로그 확인
```bash
docker compose logs -f backend
```

### 4단계: 서비스 중지
```bash
docker compose down
```

---

## 서비스 포트

| 서비스 | 포트 | 용도 |
|--------|------|------|
| FastAPI | 8000 | API 서버 |
| PostgreSQL | 5432 | 데이터베이스 |
| Redis | 6379 | 캐시 |

---

## 문제 해결

### 포트 충돌 오류
```bash
# 8000번 포트가 이미 사용 중인 경우
uvicorn src.main:app --reload --port 8001
```

### 패키지 설치 오류
```bash
# Python 버전 확인 (3.10 이상 필요)
python --version

# pip 업그레이드
pip install --upgrade pip
```
