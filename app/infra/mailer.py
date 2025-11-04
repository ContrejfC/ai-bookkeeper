"""
Email delivery infrastructure with provider abstraction.

Supports:
- Resend (preferred, modern API)
- SendGrid (fallback, traditional)

Features:
- Template rendering with Jinja2
- Plain-text fallback
- Delivery tracking (message_id in logs)
- Provider failover
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from enum import Enum

logger = logging.getLogger(__name__)


class MailProvider(str, Enum):
    """Supported email providers."""
    RESEND = "resend"
    SENDGRID = "sendgrid"
    CONSOLE = "console"  # For testing - prints to stdout


class EmailTemplate(str, Enum):
    """Available email templates."""
    VERIFY_EMAIL = "verify_email"
    PASSWORD_RESET = "password_reset"
    TRIAL_ENDING = "trial_ending"
    SUPPORT_TICKET = "support_ticket"
    WELCOME = "welcome"


class MailerConfig:
    """Email configuration from environment."""
    
    def __init__(self):
        self.provider = MailProvider(
            os.getenv("MAIL_PROVIDER", "console").lower()
        )
        self.from_email = os.getenv("FROM_EMAIL", "noreply@ai-bookkeeper.app")
        self.reply_to = os.getenv("REPLY_TO_EMAIL", "support@ai-bookkeeper.app")
        self.support_inbox = os.getenv("SUPPORT_INBOX", "support@ai-bookkeeper.app")
        
        # Provider-specific API keys
        self.resend_api_key = os.getenv("RESEND_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        
        # Template directory
        template_dir = os.getenv(
            "EMAIL_TEMPLATE_DIR",
            str(Path(__file__).parent.parent / "templates" / "emails")
        )
        self.template_dir = Path(template_dir)
        
        # Ensure template directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)


class Mailer:
    """
    Email delivery service with provider abstraction.
    
    Usage:
        mailer = Mailer()
        result = await mailer.send(
            to="user@example.com",
            subject="Welcome!",
            template=EmailTemplate.WELCOME,
            context={"name": "Alice", "trial_days": 14}
        )
    """
    
    def __init__(self, config: Optional[MailerConfig] = None):
        self.config = config or MailerConfig()
        
        # Initialize Jinja2 environment for templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.config.template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        logger.info(
            f"Mailer initialized: provider={self.config.provider}, "
            f"from={self.config.from_email}"
        )
    
    async def send(
        self,
        to: str,
        subject: str,
        template: EmailTemplate,
        context: Dict[str, Any],
        cc: Optional[list] = None,
        bcc: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send email using configured provider.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            template: Template name from EmailTemplate enum
            context: Variables to render in template
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            
        Returns:
            Dict with:
            - success: bool
            - message_id: str (provider's message ID)
            - provider: str
            
        Raises:
            Exception if all providers fail
        """
        
        # Render templates
        html_body = self._render_template(f"{template.value}.html", context)
        text_body = self._render_template(f"{template.value}.txt", context)
        
        # Build email payload
        email_data = {
            "to": to,
            "from": self.config.from_email,
            "reply_to": self.config.reply_to,
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "cc": cc,
            "bcc": bcc
        }
        
        # Send via configured provider
        if self.config.provider == MailProvider.RESEND:
            return await self._send_resend(email_data)
        elif self.config.provider == MailProvider.SENDGRID:
            return await self._send_sendgrid(email_data)
        elif self.config.provider == MailProvider.CONSOLE:
            return self._send_console(email_data)
        else:
            raise ValueError(f"Unsupported mail provider: {self.config.provider}")
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context."""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.warning(
                f"Template {template_name} not found or failed to render: {e}"
            )
            # Return minimal fallback
            return f"[Template {template_name}] {context}"
    
    async def _send_resend(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Resend API."""
        try:
            import httpx
            
            if not self.config.resend_api_key:
                raise ValueError("RESEND_API_KEY not configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.config.resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": email_data["from"],
                        "to": [email_data["to"]],
                        "subject": email_data["subject"],
                        "html": email_data["html"],
                        "text": email_data["text"],
                        "reply_to": email_data.get("reply_to")
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                message_id = result.get("id", "unknown")
                
                logger.info(
                    f"Email sent via Resend: to={email_data['to']}, "
                    f"subject={email_data['subject']}, message_id={message_id}"
                )
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "provider": "resend"
                }
                
        except Exception as e:
            logger.error(f"Resend send failed: {e}")
            raise
    
    async def _send_sendgrid(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via SendGrid API."""
        try:
            import httpx
            
            if not self.config.sendgrid_api_key:
                raise ValueError("SENDGRID_API_KEY not configured")
            
            payload = {
                "personalizations": [{
                    "to": [{"email": email_data["to"]}]
                }],
                "from": {"email": email_data["from"]},
                "reply_to": {"email": email_data.get("reply_to", email_data["from"])},
                "subject": email_data["subject"],
                "content": [
                    {"type": "text/plain", "value": email_data["text"]},
                    {"type": "text/html", "value": email_data["html"]}
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.config.sendgrid_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=10.0
                )
                
                response.raise_for_status()
                
                # SendGrid returns X-Message-Id in headers
                message_id = response.headers.get("X-Message-Id", "unknown")
                
                logger.info(
                    f"Email sent via SendGrid: to={email_data['to']}, "
                    f"subject={email_data['subject']}, message_id={message_id}"
                )
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "provider": "sendgrid"
                }
                
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            raise
    
    def _send_console(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock email send for testing - prints to console."""
        import uuid
        
        message_id = f"console_{uuid.uuid4().hex[:8]}"
        
        print("\n" + "="*80)
        print(f"📧 EMAIL (Console Mode) - Message ID: {message_id}")
        print("="*80)
        print(f"To: {email_data['to']}")
        print(f"From: {email_data['from']}")
        print(f"Subject: {email_data['subject']}")
        print(f"Reply-To: {email_data.get('reply_to')}")
        print("-"*80)
        print(email_data['text'][:500])  # Truncate for readability
        print("="*80 + "\n")
        
        logger.info(
            f"Email sent via Console: to={email_data['to']}, "
            f"subject={email_data['subject']}, message_id={message_id}"
        )
        
        return {
            "success": True,
            "message_id": message_id,
            "provider": "console"
        }


# Global mailer instance
_mailer: Optional[Mailer] = None


def get_mailer() -> Mailer:
    """Get or create global mailer instance."""
    global _mailer
    if _mailer is None:
        _mailer = Mailer()
    return _mailer


async def send_verification_email(to: str, verification_code: str, verification_url: str) -> Dict[str, Any]:
    """Send email verification email."""
    mailer = get_mailer()
    return await mailer.send(
        to=to,
        subject="Verify your AI Bookkeeper account",
        template=EmailTemplate.VERIFY_EMAIL,
        context={
            "verification_code": verification_code,
            "verification_url": verification_url,
            "expires_in_hours": 24
        }
    )


async def send_password_reset_email(to: str, reset_code: str, reset_url: str) -> Dict[str, Any]:
    """Send password reset email."""
    mailer = get_mailer()
    return await mailer.send(
        to=to,
        subject="Reset your AI Bookkeeper password",
        template=EmailTemplate.PASSWORD_RESET,
        context={
            "reset_code": reset_code,
            "reset_url": reset_url,
            "expires_in_hours": 1
        }
    )


async def send_trial_ending_email(to: str, tenant_name: str, days_remaining: int) -> Dict[str, Any]:
    """Send trial ending notification."""
    mailer = get_mailer()
    return await mailer.send(
        to=to,
        subject=f"Your AI Bookkeeper trial ends in {days_remaining} days",
        template=EmailTemplate.TRIAL_ENDING,
        context={
            "tenant_name": tenant_name,
            "days_remaining": days_remaining,
            "upgrade_url": f"{os.getenv('FRONTEND_URL', 'https://app.ai-bookkeeper.app')}/pricing"
        }
    )


async def send_support_ticket_email(
    user_email: str,
    subject: str,
    message: str,
    request_id: str,
    tenant_id: str
) -> Dict[str, Any]:
    """Send support ticket to support inbox."""
    mailer = get_mailer()
    return await mailer.send(
        to=mailer.config.support_inbox,
        subject=f"[Support] {subject}",
        template=EmailTemplate.SUPPORT_TICKET,
        context={
            "user_email": user_email,
            "subject": subject,
            "message": message,
            "request_id": request_id,
            "tenant_id": tenant_id,
            "log_url": f"{os.getenv('BACKEND_URL')}/api/audit/{request_id}"
        },
        cc=[user_email]  # CC the user for confirmation
    )


async def send_welcome_email(to: str, name: str, trial_days: int) -> Dict[str, Any]:
    """Send welcome email after signup."""
    mailer = get_mailer()
    return await mailer.send(
        to=to,
        subject="Welcome to AI Bookkeeper!",
        template=EmailTemplate.WELCOME,
        context={
            "name": name,
            "trial_days": trial_days,
            "onboarding_url": f"{os.getenv('FRONTEND_URL', 'https://app.ai-bookkeeper.app')}/onboarding",
            "docs_url": f"{os.getenv('FRONTEND_URL')}/docs",
            "support_email": get_mailer().config.support_inbox
        }
    )

