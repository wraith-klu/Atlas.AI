"""
email_sender.py

Email notifications are DISABLED.
The user opted for WhatsApp-only alerts. This module provides
stub functions so that any existing imports do not break.
"""

from utils.logger import get_logger

logger = get_logger("EmailSender")


def get_gmail_service():
    """Stub — email is disabled."""
    logger.info("Email alerts disabled (WhatsApp-only mode).")
    return None


def build_email_html(jobs_list: list) -> str:
    """Stub — returns empty string."""
    return ""


def send_email(subject: str, html_body: str, to_email: str = None) -> bool:
    """Stub — always returns False."""
    logger.info("Email alerts disabled (WhatsApp-only mode). Skipping send.")
    return False


def send_daily_digest(jobs_list: list, to_email: str = None) -> bool:
    """Stub — always returns False."""
    logger.info("Email alerts disabled (WhatsApp-only mode). Skipping digest.")
    return False
