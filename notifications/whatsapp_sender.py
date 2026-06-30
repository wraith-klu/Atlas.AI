"""
whatsapp_sender.py

WhatsApp alert sender using Meta WhatsApp Cloud API (free tier).
Falls back gracefully if credentials are not configured.
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("WhatsAppSender")

# ─── Configuration from .env ─────────────────────────────────
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
ALERT_WHATSAPP_TO = os.getenv("ALERT_WHATSAPP_TO", "919792453534")

META_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"


# ──────────────────────────────────────────────────────────────
# Parse helpers
# ──────────────────────────────────────────────────────────────

def _parse_skill_list(raw) -> list:
    """Normalise a skill field that may be a JSON string or a list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        except (json.JSONDecodeError, TypeError):
            return [raw] if raw else []
    return []


# ──────────────────────────────────────────────────────────────
# Send a raw WhatsApp text message (Meta Cloud API)
# ──────────────────────────────────────────────────────────────

def send_whatsapp_message(to_number: str, message_text: str) -> bool:
    """
    Sends a plain-text WhatsApp message via Meta WhatsApp Cloud API.

    Args:
        to_number:    Recipient phone number with country code (e.g. 919792453534).
        message_text: The text body to send.

    Returns:
        True on success, False on failure.
    """
    if not WHATSAPP_API_TOKEN or WHATSAPP_API_TOKEN == "your_meta_or_twilio_token":
        logger.warning(
            "WhatsApp API token not configured — skipping Meta Cloud API send. "
            "Set WHATSAPP_API_TOKEN in .env or use the Twilio sandbox module."
        )
        return False

    if not WHATSAPP_PHONE_ID or WHATSAPP_PHONE_ID == "your_phone_number_id":
        logger.warning(
            "WhatsApp Phone ID not configured — skipping Meta Cloud API send. "
            "Set WHATSAPP_PHONE_ID in .env."
        )
        return False

    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": str(to_number),
        "type": "text",
        "text": {"body": message_text},
    }

    try:
        resp = requests.post(META_API_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            logger.info(f"WhatsApp message sent to {to_number} via Meta Cloud API.")
            return True
        else:
            logger.error(
                f"WhatsApp API error ({resp.status_code}): {resp.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# Build WhatsApp plain-text summary (≤1000 chars)
# ──────────────────────────────────────────────────────────────

def build_whatsapp_summary(jobs_list: list) -> str:
    """
    Generates a compact plain-text WhatsApp message showing the
    top 3 highest-scored jobs.  Full details go via email.

    WhatsApp formatting: *bold*, _italic_, ~strikethrough~
    Kept under 1 000 characters to stay within message limits.
    """
    today = datetime.now().strftime("%d %b %Y")
    total = len(jobs_list)

    # Sort by score descending, pick top 3
    sorted_jobs = sorted(
        jobs_list,
        key=lambda j: float(j.get("match_score", 0)),
        reverse=True,
    )[:3]

    number_emojis = ["1️⃣", "2️⃣", "3️⃣"]

    lines = [
        "🤖 *AI Job Agent — Daily Update*",
        f"📅 {today}",
        "",
        f"Found *{total}* new matches today!",
        "",
        "🏆 *TOP PICKS:*",
        "",
    ]

    for idx, job in enumerate(sorted_jobs):
        company = job.get("company", "N/A")
        title = job.get("title", "N/A")
        location = job.get("location", "N/A")
        score = int(float(job.get("match_score", 0)))
        apply_link = job.get("apply_link", "N/A")

        lines.append(f"{number_emojis[idx]} *{company}* — {title}")
        lines.append(f"📍 {location} | 🎯 {score}% match")
        lines.append(f"🔗 {apply_link}")
        lines.append("")

    lines.append("💡 Check your email for full details + skill gap report!")

    message = "\n".join(lines)

    # Truncate if somehow over 1000 chars
    if len(message) > 1000:
        message = message[:997] + "..."

    return message


# ──────────────────────────────────────────────────────────────
# Daily digest wrapper
# ──────────────────────────────────────────────────────────────

def send_daily_digest_whatsapp(jobs_list: list, to_number: str = None) -> bool:
    """
    Builds the WhatsApp summary and sends it.

    Args:
        jobs_list:  List of job dicts (APPLY/STRETCH only).
        to_number:  Override for the recipient number.

    Returns:
        True on success, False on failure.
    """
    if not jobs_list:
        logger.info("No jobs to include in WhatsApp digest.")
        return False

    to_number = to_number or ALERT_WHATSAPP_TO
    message = build_whatsapp_summary(jobs_list)
    return send_whatsapp_message(to_number, message)
