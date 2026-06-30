"""
alert_manager.py

Smart alert orchestrator for Phase 3/4.
Decides WHEN and WHAT to alert, dispatches to WhatsApp senders,
and marks jobs as alerted to prevent duplicate notifications.
Supports multi-user user_id checks via Supabase.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import get_logger
import database.supabase_client as db

load_dotenv()
logger = get_logger("AlertManager")

# ─── Configuration ────────────────────────────────────────────
ALERT_MODE = os.getenv("ALERT_MODE", "digest").strip().lower()     # "digest" or "instant"
DIGEST_TIME = os.getenv("DIGEST_TIME", "08:00").strip()            # HH:MM (24h)


# ──────────────────────────────────────────────────────────────
# Query helpers
# ──────────────────────────────────────────────────────────────

def get_jobs_to_alert(user_id: str = "00000000-0000-0000-0000-000000000000") -> list:
    """
    Fetches jobs that are alert-eligible for the given user.
    """
    return db.get_jobs_to_alert(user_id)


def should_send_now() -> bool:
    """
    Decides whether to send alerts right now based on ALERT_MODE.

    - "instant" → always True
    - "digest"  → True only if current HH:MM matches DIGEST_TIME
                   (with a 5-minute window to account for cron jitter)
    """
    if ALERT_MODE == "instant":
        return True

    # Digest mode: compare current HH:MM to DIGEST_TIME
    try:
        now = datetime.now()
        target_hour, target_min = map(int, DIGEST_TIME.split(":"))
        current_minutes = now.hour * 60 + now.minute
        target_minutes = target_hour * 60 + target_min

        # Allow a 5-minute window (e.g. 08:00 – 08:04)
        diff = abs(current_minutes - target_minutes)
        if diff <= 4:
            return True

        logger.info(
            f"Digest mode: current time {now.strftime('%H:%M')} is not within "
            f"the window for {DIGEST_TIME}. Skipping send."
        )
        return False
    except Exception as e:
        logger.error(f"Error parsing DIGEST_TIME '{DIGEST_TIME}': {e}")
        # On parse error, allow the send so alerts aren't silently dropped
        return True


def mark_alerted(user_id: str, jobs_list: list) -> int:
    """
    Marks every job in the list as alerted for the user so they won't be
    re-sent on the next cycle.

    Returns the count of jobs marked.
    """
    count = 0
    for job in jobs_list:
        job_id = job.get("job_id")
        if job_id:
            db.mark_job_alerted(user_id, job_id)
            count += 1
    logger.info(f"Marked {count} jobs as alerted for user {user_id}.")
    return count


# ──────────────────────────────────────────────────────────────
# Main orchestrator
# ──────────────────────────────────────────────────────────────

def run_alert_cycle(force: bool = False, user_id: str = None) -> dict:
    """
    Main Phase 3/4 alert orchestrator (WhatsApp-only).

    Steps:
      1. Resolve user ID
      2. Fetch un-alerted APPLY/STRETCH jobs
      3. Check if now is the right time (or force=True)
      4. Send WhatsApp digest (tries Meta first, falls back to Twilio)
      5. Mark jobs as alerted
      6. Return summary dict
    """
    summary = {
        "jobs_eligible": 0,
        "whatsapp_sent": False,
        "jobs_marked": 0,
        "skipped_reason": None,
    }

    # Resolve fallback user ID if not provided
    if not user_id:
        # Resolve from user_profile.yaml to keep backward compatibility
        from utils.config_loader import load_profile
        try:
            profile = load_profile()
            whatsapp_number = profile.get("user", {}).get("whatsapp", "919792453534")
            user_id = db.get_or_create_user(whatsapp_number, profile.get("user", {}))
        except Exception as e:
            logger.error(f"Error loading profile user in alert manager: {e}")
            user_id = "00000000-0000-0000-0000-000000000000"

    # 1. Get eligible jobs
    jobs = get_jobs_to_alert(user_id)
    summary["jobs_eligible"] = len(jobs)

    if not jobs:
        logger.info(f"No new APPLY/STRETCH matches to alert for user {user_id}.")
        summary["skipped_reason"] = "No eligible jobs"
        return summary

    # 2. Time check
    if not force and not should_send_now():
        summary["skipped_reason"] = (
            f"Digest mode — waiting for {DIGEST_TIME}"
        )
        return summary

    # 3. Send WhatsApp (Meta Cloud API first, then Twilio fallback)
    whatsapp_ok = False
    try:
        from notifications.whatsapp_sender import send_daily_digest_whatsapp
        whatsapp_ok = send_daily_digest_whatsapp(jobs)
    except Exception as e:
        logger.warning(f"Meta WhatsApp send failed: {e}")

    if not whatsapp_ok:
        try:
            from notifications.whatsapp_sender_twilio import send_daily_digest_whatsapp_twilio
            whatsapp_ok = send_daily_digest_whatsapp_twilio(jobs)
        except Exception as e:
            logger.warning(f"Twilio WhatsApp send also failed: {e}")

    summary["whatsapp_sent"] = whatsapp_ok

    # 4. Mark jobs as alerted (only if WhatsApp succeeded)
    if summary["whatsapp_sent"]:
        summary["jobs_marked"] = mark_alerted(user_id, jobs)
    else:
        logger.warning(
            f"WhatsApp send failed — jobs NOT marked as alerted for user {user_id}."
        )

    # 5. Log summary
    logger.info(
        f"Alert cycle complete for user {user_id}: {summary['jobs_eligible']} eligible, "
        f"whatsapp={'sent' if summary['whatsapp_sent'] else 'failed'}, "
        f"{summary['jobs_marked']} marked."
    )

    return summary
