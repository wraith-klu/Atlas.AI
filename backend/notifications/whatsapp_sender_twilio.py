"""
whatsapp_sender_twilio.py

Twilio WhatsApp Sandbox alternative — easiest way to test WhatsApp
alerts immediately (no Meta Business verification needed).

Setup:
  1. Sign up at https://twilio.com (free trial, ~$15.50 credit)
  2. Go to Console → Messaging → Try it Out → Send a WhatsApp message
  3. Join the sandbox by sending the code from your WhatsApp to the
     Twilio sandbox number (e.g. "join <word>-<word>")
  4. Copy Account SID + Auth Token from the Twilio Console dashboard
  5. Add to .env:
       TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
       TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
       TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger("WhatsAppTwilio")

# ─── Configuration from .env ─────────────────────────────────
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
ALERT_WHATSAPP_TO = os.getenv("ALERT_WHATSAPP_TO", "919792453534")


# ──────────────────────────────────────────────────────────────
# Parse helpers (shared logic)
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
# Send message via Twilio WhatsApp Sandbox
# ──────────────────────────────────────────────────────────────

def send_whatsapp_twilio(to_number: str, message: str) -> bool:
    """
    Sends a WhatsApp message through the Twilio sandbox.

    Args:
        to_number: Recipient phone number (digits only, e.g. 9792453534).
        message:   Plain text message body.

    Returns:
        True on success, False on failure.
    """
    if not TWILIO_SID or not TWILIO_AUTH_TOKEN:
        logger.warning(
            "Twilio credentials not configured — skipping Twilio WhatsApp. "
            "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env."
        )
        return False

    try:
        from twilio.rest import Client

        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

        # Ensure recipient is in whatsapp: format
        to_formatted = to_number if to_number.startswith("whatsapp:") else f"whatsapp:+{to_number}"
        # Strip any double "+" 
        to_formatted = to_formatted.replace("++", "+")

        msg = client.messages.create(
            from_=TWILIO_FROM,
            body=message,
            to=to_formatted,
        )
        logger.info(f"Twilio WhatsApp message sent — SID: {msg.sid}")
        return True

    except ImportError:
        logger.error(
            "twilio package not installed. Run: pip install twilio"
        )
        return False
    except Exception as e:
        logger.error(f"Twilio WhatsApp send failed: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# Build compact WhatsApp summary (same format as Meta sender)
# ──────────────────────────────────────────────────────────────

def build_whatsapp_summary(jobs_list: list) -> str:
    """
    Generates a compact plain-text WhatsApp message showing the
    top 3 highest-scored jobs.
    """
    today = datetime.now().strftime("%d %b %Y")
    total = len(jobs_list)

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
    if len(message) > 1000:
        message = message[:997] + "..."
    return message


# ──────────────────────────────────────────────────────────────
# Daily digest wrapper (Twilio)
# ──────────────────────────────────────────────────────────────

def send_daily_digest_whatsapp_twilio(jobs_list: list, to_number: str = None) -> bool:
    """
    Builds the summary and sends via Twilio sandbox.
    """
    if not jobs_list:
        logger.info("No jobs to include in Twilio WhatsApp digest.")
        return False

    to_number = to_number or ALERT_WHATSAPP_TO
    message = build_whatsapp_summary(jobs_list)
    return send_whatsapp_twilio(to_number, message)
