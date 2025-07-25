from celery import Celery
from asgiref.sync import async_to_sync
from app.middlewares.mail import mail, create_message
from app.core.config import settings
import ssl

celery_app = Celery(
    "granthub",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.broker_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
}
celery_app.conf.redis_backend_use_ssl = {
    'ssl_cert_reqs': ssl.CERT_NONE
}

@celery_app.task
def send_email(recipients: list[str], subject: str, html_message: str):
    message = create_message(
        recipients=recipients,
        subject=subject,
        body=html_message
    )
    async_to_sync(mail.send_message)(message)
    print("Email sent")
