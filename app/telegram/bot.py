"""
Telegram bot core functionality for Gestionale Fibra.

Provides the main bot class and initialization for webhook mode.
"""

from typing import Optional

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class TelegramBot:
    """
    Telegram bot for field technician operations.
    
    Provides methods for sending notifications and handling
    job-related commands.
    """
    
    def __init__(self):
        """Initialize the Telegram bot."""
        self._application = None
        self._bot = None
    
    @property
    def is_configured(self) -> bool:
        """Check if bot is properly configured."""
        return bool(settings.telegram_bot_token)
    
    async def initialize(self) -> None:
        """
        Initialize the bot application.
        
        Should be called during app startup.
        """
        if not self.is_configured:
            logger.warning("Telegram bot not configured - missing token")
            return
        
        try:
            from telegram import Bot
            from telegram.ext import Application
            
            self._application = (
                Application.builder()
                .token(settings.telegram_bot_token)
                .build()
            )
            self._bot = Bot(token=settings.telegram_bot_token)
            
            logger.info("Telegram bot initialized")
            
        except ImportError:
            logger.error("python-telegram-bot not installed")
        except Exception as e:
            logger.error("Failed to initialize Telegram bot", error=str(e))
    
    async def shutdown(self) -> None:
        """
        Shutdown the bot application.
        
        Should be called during app shutdown.
        """
        if self._application:
            await self._application.shutdown()
            logger.info("Telegram bot shutdown")
    
    async def set_webhook(self, webhook_url: Optional[str] = None) -> bool:
        """
        Set the webhook URL for receiving updates.
        
        Args:
            webhook_url: Webhook URL (uses config if not provided)
            
        Returns:
            bool: True if webhook was set successfully
        """
        if not self._bot:
            return False
        
        url = webhook_url or settings.telegram_webhook_url
        if not url:
            logger.warning("No webhook URL configured")
            return False
        
        try:
            await self._bot.set_webhook(url=url)
            logger.info("Telegram webhook set", url=url)
            return True
        except Exception as e:
            logger.error("Failed to set webhook", error=str(e))
            return False
    
    async def send_job_notification(
        self,
        chat_id: str,
        job_id: int,
        wr_number: str,
        customer_name: str,
        customer_address: str,
        scheduled_date: str,
    ) -> bool:
        """
        Send a new job notification to a technician.
        
        Args:
            chat_id: Telegram chat ID
            job_id: Work order ID
            wr_number: Work request number
            customer_name: Customer name
            customer_address: Customer address
            scheduled_date: Scheduled date
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self._bot:
            return False
        
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            message = (
                f"🔔 <b>Nuovo Lavoro Assegnato</b>\n\n"
                f"📋 <b>WR:</b> {wr_number}\n"
                f"👤 <b>Cliente:</b> {customer_name}\n"
                f"📍 <b>Indirizzo:</b> {customer_address}\n"
                f"📅 <b>Data:</b> {scheduled_date}\n"
            )
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Accetta",
                        callback_data=f"accept_{job_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Rifiuta",
                        callback_data=f"refuse_{job_id}"
                    ),
                ]
            ])
            
            await self._bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            
            logger.info(
                "Job notification sent",
                chat_id=chat_id,
                job_id=job_id,
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send job notification",
                error=str(e),
                chat_id=chat_id,
            )
            return False
    
    async def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = "HTML",
    ) -> bool:
        """
        Send a text message to a user.
        
        Args:
            chat_id: Telegram chat ID
            message: Message text
            parse_mode: Message parse mode
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self._bot:
            return False
        
        try:
            await self._bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to send message",
                error=str(e),
                chat_id=chat_id,
            )
            return False
    
    async def send_job_in_progress_options(
        self,
        chat_id: str,
        job_id: int,
    ) -> bool:
        """
        Send options for a job in progress (close, send photos).
        
        Args:
            chat_id: Telegram chat ID
            job_id: Work order ID
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self._bot:
            return False
        
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            message = (
                f"📋 <b>Lavoro in corso</b>\n\n"
                f"Puoi inviare foto o chiudere il lavoro quando completato."
            )
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📸 Invia Foto",
                        callback_data=f"photo_{job_id}"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "✅ Chiudi Lavoro",
                        callback_data=f"close_{job_id}"
                    ),
                ],
            ])
            
            await self._bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send in-progress options",
                error=str(e),
                chat_id=chat_id,
            )
            return False


# Singleton instance
telegram_bot = TelegramBot()
