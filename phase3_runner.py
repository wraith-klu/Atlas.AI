"""
phase3_runner.py

Phase 3 entry point — runs the notification alert cycle and
prints a formatted summary.

Usage:
    python phase3_runner.py              (respects digest/instant mode)
    python phase3_runner.py --force      (sends now regardless of mode)
"""

import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Ensure project root is on sys.path so imports work when run directly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv()

from utils.logger import get_logger
from database.db_manager import init_db
from notifications.alert_manager import run_alert_cycle

logger = get_logger("Phase3Runner")

ALERT_WHATSAPP_TO = os.getenv("ALERT_WHATSAPP_TO", "919792453534")


def run_phase3(force: bool = False) -> dict:
    """
    Runs the Phase 3 notification cycle and prints a summary.

    Args:
        force: If True, send alerts now regardless of digest timing.

    Returns:
        dict — the alert cycle summary.
    """
    start_time = time.time()

    logger.info("Starting Phase 3 — Notification Engine...")

    # Make sure DB tables exist
    init_db()

    # Run the alert cycle
    summary = run_alert_cycle(force=force)

    elapsed = round(time.time() - start_time, 1)

    # ── Pretty-print summary ──
    print("\n")
    print("💬 PHASE 3 — Notification Summary")
    print("━" * 45)

    if summary.get("skipped_reason"):
        print(f"  ⏭️  Skipped: {summary['skipped_reason']}")
    else:
        print(f"  Jobs eligible for alert : {summary['jobs_eligible']}")
        print(f"  ✅ WhatsApp sent        : {'Yes (' + ALERT_WHATSAPP_TO + ')' if summary['whatsapp_sent'] else 'No'}")
        print(f"  📌 Jobs marked alerted  : {summary['jobs_marked']}")

    print(f"  ⏱️  Elapsed              : {elapsed}s")
    print("━" * 45)
    print()

    return summary


# ──────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    run_phase3(force=force_flag)
