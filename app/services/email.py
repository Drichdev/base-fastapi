import logging
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Jinja2 template environment
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)

# FastAPI-Mail configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    VALIDATE_CERTS=True,
)

fast_mail = FastMail(mail_config)


class EmailService:
    """Service for sending emails using templates."""

    @staticmethod
    def _render_template(template_name: str, context: dict) -> str:
        """Render a Jinja2 email template."""
        template = jinja_env.get_template(template_name)
        return template.render(**context)

    @classmethod
    async def send_email(
        cls,
        to: str,
        subject: str,
        template_name: str,
        context: dict | None = None,
    ) -> bool:
        """Send an email using a template.

        Returns True if sent successfully, False otherwise.
        """
        try:
            html_body = cls._render_template(template_name, context or {})
            message = MessageSchema(
                subject=subject,
                recipients=[to],
                body=html_body,
                subtype=MessageType.html,
            )
            await fast_mail.send_message(message)
            logger.info("Email sent to %s — subject: %s", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to)
            return False

    @classmethod
    async def send_welcome_email(cls, to: str, first_name: str) -> bool:
        """Send a welcome email after registration."""
        return await cls.send_email(
            to=to,
            subject=f"Welcome to {settings.APP_NAME}!",
            template_name="welcome.html",
            context={
                "first_name": first_name,
                "app_name": settings.APP_NAME,
            },
        )

    @classmethod
    async def send_reset_password_email(cls, to: str, first_name: str, reset_token: str) -> bool:
        """Send a password reset email."""
        return await cls.send_email(
            to=to,
            subject="Password Reset Request",
            template_name="reset_password.html",
            context={
                "first_name": first_name,
                "reset_token": reset_token,
                "app_name": settings.APP_NAME,
            },
        )

    @classmethod
    async def send_verification_email(cls, to: str, first_name: str, verification_token: str) -> bool:
        """Send an email verification token."""
        return await cls.send_email(
            to=to,
            subject="Veuillez vérifier votre adresse email",
            template_name="verify_email.html",
            context={
                "first_name": first_name,
                "verification_token": verification_token,
                "app_name": settings.APP_NAME,
            },
        )

