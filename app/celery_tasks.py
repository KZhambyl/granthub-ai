from __future__ import annotations
import os
import ssl
import asyncio
from typing import Optional

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from asgiref.sync import async_to_sync

from app.core.config import settings
from app.middlewares.mail import mail, create_message

# ВАЖНО: для ETL нам нужен AsyncSession напрямую, без FastAPI Depends
# Экспортируй из app.db.main объект AsyncSessionLocal (sessionmaker)
try:
    from app.db.main import AsyncSessionLocal  # предпочтительно
except Exception:
    AsyncSessionLocal = None

logger = get_task_logger(__name__)

celery_app = Celery(
    "granthub",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Базовая конфигурация Celery
celery_app.conf.update(
    timezone="Asia/Almaty",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_max_tasks_per_child=100,
    task_acks_late=True, # безопаснее при падениях
    broker_connection_retry_on_startup=True,
)

# SSL для Redis — только если нужен
if settings.CELERY_BROKER_URL.startswith("redis://") or settings.CELERY_BROKER_URL.startswith("rediss://"):
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}

# EMAIL

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    time_limit=30, # жёсткий таймаут задачи
)
def send_email(self, recipients: list[str], subject: str, html_message: str):
    """
    Отправка email через существующий mail middleware.
    """
    try:
        message = create_message(
            recipients=recipients,
            subject=subject,
            body=html_message,
        )
        # mail.send_message — async → исполняем синхронно в Celery
        async_to_sync(mail.send_message)(message)
        logger.info("Email sent to %s", recipients)
        return {"ok": True}
    except Exception as e:
        logger.exception("Email sending failed: %s", e)
        raise
