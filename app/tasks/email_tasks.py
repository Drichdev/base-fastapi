import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async code from sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="tasks.send_welcome_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email_task(self, email: str, first_name: str) -> dict:
    """Celery task: send a welcome email after user registration."""
    try:
        from app.services.email import EmailService

        result = _run_async(EmailService.send_welcome_email(to=email, first_name=first_name))
        logger.info("Welcome email task completed for %s — success: %s", email, result)
        return {"email": email, "success": result}
    except Exception as exc:
        logger.exception("Welcome email task failed for %s", email)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.send_reset_password_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_reset_password_email_task(self, email: str, first_name: str, reset_token: str) -> dict:
    """Celery task: send a password reset email."""
    try:
        from app.services.email import EmailService

        result = _run_async(
            EmailService.send_reset_password_email(
                to=email,
                first_name=first_name,
                reset_token=reset_token,
            )
        )
        logger.info("Reset password email task completed for %s — success: %s", email, result)
        return {"email": email, "success": result}
    except Exception as exc:
        logger.exception("Reset password email task failed for %s", email)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="tasks.send_verification_email",
    max_retries=3,
    default_retry_delay=60,
)
def send_verification_email_task(self, email: str, first_name: str, verification_token: str) -> dict:
    """Celery task: send an email verification token."""
    try:
        from app.services.email import EmailService

        result = _run_async(
            EmailService.send_verification_email(
                to=email,
                first_name=first_name,
                verification_token=verification_token,
            )
        )
        logger.info("Verification email task completed for %s — success: %s", email, result)
        return {"email": email, "success": result}
    except Exception as exc:
        logger.exception("Verification email task failed for %s", email)
        raise self.retry(exc=exc)

