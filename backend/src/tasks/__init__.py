"""
Celery 애플리케이션 초기화

사용법:
    # Celery Worker 시작 (Redis 브로커 필요)
    celery -A backend.src.tasks worker --loglevel=info

    # Celery Beat 스케줄러 시작 (주기적 태스크)
    celery -A backend.src.tasks beat --loglevel=info

참고: Celery 없이도 POST /{ticker}/update-actuals API로 수동 실행 가능
"""
import os
from celery import Celery

# Redis 브로커 URL (환경변수 또는 기본값)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "ispas_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["backend.src.tasks.prediction_tasks"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    # Beat 스케줄 (매일 오전 9시 실제 가격 업데이트)
    beat_schedule={
        "update-actual-prices-daily": {
            "task": "backend.src.tasks.prediction_tasks.update_actual_prices_all",
            "schedule": 60 * 60 * 24,  # 24시간마다
        }
    }
)
