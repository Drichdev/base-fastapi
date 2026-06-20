from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "base_fastapi_pro",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task settings
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Result settings
    result_expires=3600,  # 1 hour
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200_000,  # 200MB
)

# Auto-discover tasks in the tasks package
celery_app.autodiscover_tasks(["app.tasks"])
