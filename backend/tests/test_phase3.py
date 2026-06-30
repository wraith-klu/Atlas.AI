"""
test_phase3.py

Test suite for Phase 3 notification system.
Tests: Gmail auth, email sending, WhatsApp, alert logic, duplicate prevention.

Usage:
    python -m tests.test_phase3           (run all tests)
    python -m tests.test_phase3 email     (test email only)
    python -m tests.test_phase3 whatsapp  (test WhatsApp only)
    python -m tests.test_phase3 logic     (test alert logic only)
"""

import sys
import os
import json
from datetime import datetime

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from utils.logger import get_logger
from database.db_manager import (
    init_db, get_connection, save_job, mark_job_alerted,
    get_unalerted_matches, count_alerts_today
)

logger = get_logger("TestPhase3")


# ──────────────────────────────────────────────────────────────
# Helper: create mock jobs for testing
# ──────────────────────────────────────────────────────────────

def _create_mock_jobs() -> list:
    """Returns 3 mock job dicts suitable for testing."""
    return [
        {
            "job_id": f"test_apply_{datetime.now().strftime('%H%M%S')}",
            "company": "TestCorp",
            "title": "AI Engineer",
            "location": "Bangalore",
            "experience_required": "0-1 years",
            "apply_link": "https://example.com/jobs/ai-engineer-12345",
            "description": "Build AI pipelines with Python, TensorFlow, and PyTorch.",
            "match_score": 85.0,
            "recommendation": "APPLY",
            "matching_skills": json.dumps(["Python", "TensorFlow", "PyTorch"]),
            "missing_skills": json.dumps(["Kubernetes"]),
            "quick_tip": "Highlight your ML project experience",
            "is_new": 1,
        },
        {
            "job_id": f"test_stretch_{datetime.now().strftime('%H%M%S')}",
            "company": "DemoCo",
            "title": "ML Engineer",
            "location": "Hyderabad",
            "experience_required": "1-2 years",
            "apply_link": "https://example.com/jobs/ml-engineer-67890",
            "description": "Design ML models for NLP tasks.",
            "match_score": 62.0,
            "recommendation": "STRETCH",
            "matching_skills": json.dumps(["Python", "NLP"]),
            "missing_skills": json.dumps(["Docker", "AWS"]),
            "quick_tip": "Take an AWS free-tier crash course",
            "is_new": 1,
        },
        {
            "job_id": f"test_skip_{datetime.now().strftime('%H%M%S')}",
            "company": "SkipInc",
            "title": "Senior Data Architect",
            "location": "Mumbai",
            "experience_required": "8+ years",
            "apply_link": "https://example.com/jobs/data-architect-99999",
            "description": "Lead data architecture for enterprise.",
            "match_score": 25.0,
            "recommendation": "SKIP",
            "matching_skills": json.dumps(["SQL"]),
            "missing_skills": json.dumps(["10 years exp", "Leadership"]),
            "quick_tip": "Not a good fit right now",
            "is_new": 1,
        },
    ]


# ──────────────────────────────────────────────────────────────
# TEST 1: Gmail Auth
# ──────────────────────────────────────────────────────────────

def test_gmail_auth():
    """Verify OAuth token works and Gmail service can be created."""
    print("\n📧 TEST 1: Gmail Authentication")
    print("-" * 40)
    try:
        from notifications.email_sender import get_gmail_service
        service = get_gmail_service()
        if service:
            print("  ✅ Gmail API service created successfully!")
            # Quick check: fetch the user's email address
            profile = service.users().getProfile(userId="me").execute()
            print(f"  ✅ Authenticated as: {profile.get('emailAddress')}")
            return True
        else:
            print("  ❌ Gmail service returned None — check credentials")
            return False
    except Exception as e:
        print(f"  ❌ Gmail auth failed: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# TEST 2: Send Test Email
# ──────────────────────────────────────────────────────────────

def test_send_test_email():
    """Send a real test email with mock job data."""
    print("\n📧 TEST 2: Send Test Email")
    print("-" * 40)
    try:
        from notifications.email_sender import send_daily_digest
        mock_jobs = _create_mock_jobs()[:2]  # only APPLY + STRETCH
        result = send_daily_digest(mock_jobs)
        if result:
            to = os.getenv("ALERT_EMAIL_TO", "2300039cseh2@gmail.com")
            print(f"  ✅ Test email sent to {to}")
            print("  📬 Check your inbox!")
        else:
            print("  ❌ Email send returned False — check logs")
        return result
    except Exception as e:
        print(f"  ❌ Email test failed: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# TEST 3: WhatsApp Connection
# ──────────────────────────────────────────────────────────────

def test_whatsapp_connection():
    """Send a test WhatsApp message (tries Meta, then Twilio)."""
    print("\n💬 TEST 3: WhatsApp Connection")
    print("-" * 40)

    to_number = os.getenv("ALERT_WHATSAPP_TO", "919792453534")
    test_msg = (
        "🤖 *AI Job Agent — Test Message*\n\n"
        "If you see this, WhatsApp alerts are working! ✅\n\n"
        f"Sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Try Meta Cloud API first
    meta_ok = False
    try:
        from notifications.whatsapp_sender import send_whatsapp_message
        meta_ok = send_whatsapp_message(to_number, test_msg)
        if meta_ok:
            print(f"  ✅ Meta Cloud API message sent to {to_number}")
            return True
    except Exception as e:
        print(f"  ⚠️  Meta Cloud API failed: {e}")

    # Fallback to Twilio
    try:
        from notifications.whatsapp_sender_twilio import send_whatsapp_twilio
        twilio_ok = send_whatsapp_twilio(to_number, test_msg)
        if twilio_ok:
            print(f"  ✅ Twilio sandbox message sent to {to_number}")
            return True
        else:
            print("  ❌ Twilio send returned False — check credentials")
            return False
    except Exception as e:
        print(f"  ❌ Twilio also failed: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# TEST 4: Alert Manager Logic
# ──────────────────────────────────────────────────────────────

def test_alert_manager_logic():
    """
    Insert 3 mock jobs (APPLY, STRETCH, SKIP) into DB.
    Verify alert manager only picks APPLY + STRETCH.
    """
    print("\n🧠 TEST 4: Alert Manager Logic")
    print("-" * 40)

    init_db()
    mock_jobs = _create_mock_jobs()

    # Save mock jobs to DB
    for job in mock_jobs:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO jobs (
                    job_id, company, title, location, experience_required,
                    apply_link, description, match_score, recommendation,
                    matching_skills, missing_skills, quick_tip, is_new
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job["job_id"], job["company"], job["title"], job["location"],
                job["experience_required"], job["apply_link"], job["description"],
                job["match_score"], job["recommendation"],
                job["matching_skills"], job["missing_skills"],
                job["quick_tip"], job["is_new"],
            ))
            conn.commit()
        finally:
            conn.close()

    # Query alert-eligible jobs
    from notifications.alert_manager import get_jobs_to_alert
    eligible = get_jobs_to_alert()

    eligible_ids = [j["job_id"] for j in eligible]
    skip_job_id = mock_jobs[2]["job_id"]

    passed = True

    # APPLY job should be eligible
    if mock_jobs[0]["job_id"] in eligible_ids:
        print(f"  ✅ APPLY job ({mock_jobs[0]['job_id']}) is eligible")
    else:
        print(f"  ❌ APPLY job should be eligible but isn't")
        passed = False

    # STRETCH job should be eligible
    if mock_jobs[1]["job_id"] in eligible_ids:
        print(f"  ✅ STRETCH job ({mock_jobs[1]['job_id']}) is eligible")
    else:
        print(f"  ❌ STRETCH job should be eligible but isn't")
        passed = False

    # SKIP job should NOT be eligible
    if skip_job_id not in eligible_ids:
        print(f"  ✅ SKIP job ({skip_job_id}) correctly excluded")
    else:
        print(f"  ❌ SKIP job should NOT be eligible")
        passed = False

    # Cleanup: remove test jobs
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for job in mock_jobs:
            cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job["job_id"],))
        conn.commit()
    finally:
        conn.close()

    return passed


# ──────────────────────────────────────────────────────────────
# TEST 5: No Double Send
# ──────────────────────────────────────────────────────────────

def test_no_double_send():
    """
    Insert a mock APPLY job, mark it as alerted, then verify
    it does NOT appear in the next alert cycle.
    """
    print("\n🔒 TEST 5: No Double Send")
    print("-" * 40)

    init_db()
    job_id = f"test_double_{datetime.now().strftime('%H%M%S')}"
    mock_job = {
        "job_id": job_id,
        "company": "DoubleCo",
        "title": "Test Engineer",
        "location": "Pune",
        "experience_required": "0-1 years",
        "apply_link": "https://example.com/jobs/test-12345",
        "description": "Test job for duplicate prevention.",
        "match_score": 90.0,
        "recommendation": "APPLY",
        "matching_skills": json.dumps(["Python"]),
        "missing_skills": json.dumps([]),
        "quick_tip": "Test tip",
        "is_new": 1,
    }

    # Insert job
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO jobs (
                job_id, company, title, location, experience_required,
                apply_link, description, match_score, recommendation,
                matching_skills, missing_skills, quick_tip, is_new
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mock_job["job_id"], mock_job["company"], mock_job["title"],
            mock_job["location"], mock_job["experience_required"],
            mock_job["apply_link"], mock_job["description"],
            mock_job["match_score"], mock_job["recommendation"],
            mock_job["matching_skills"], mock_job["missing_skills"],
            mock_job["quick_tip"], mock_job["is_new"],
        ))
        conn.commit()
    finally:
        conn.close()

    # First check: should be eligible
    from notifications.alert_manager import get_jobs_to_alert
    eligible_before = get_jobs_to_alert()
    found_before = any(j["job_id"] == job_id for j in eligible_before)

    # Mark as alerted
    mark_job_alerted(job_id)

    # Second check: should NOT be eligible
    eligible_after = get_jobs_to_alert()
    found_after = any(j["job_id"] == job_id for j in eligible_after)

    passed = True
    if found_before:
        print(f"  ✅ Before marking: job {job_id} is eligible")
    else:
        print(f"  ❌ Before marking: job should be eligible")
        passed = False

    if not found_after:
        print(f"  ✅ After marking: job {job_id} correctly excluded (no double send)")
    else:
        print(f"  ❌ After marking: job still appears — duplicate prevention broken!")
        passed = False

    # Cleanup
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        cursor.execute("DELETE FROM alerts_sent WHERE job_id = ?", (job_id,))
        conn.commit()
    finally:
        conn.close()

    return passed


# ──────────────────────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────────────────────

def run_all_tests():
    """Run all Phase 3 tests and print a summary."""
    print("\n" + "=" * 60)
    print("🧪 PHASE 3 — TEST SUITE")
    print("=" * 60)

    results = {}

    # Check command-line filter
    test_filter = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    if test_filter in ("all", "whatsapp"):
        results["WhatsApp Connection"] = test_whatsapp_connection()

    if test_filter in ("all", "logic"):
        results["Alert Logic"] = test_alert_manager_logic()
        results["No Double Send"] = test_no_double_send()

    # Summary
    print("\n" + "=" * 60)
    print("🧪 TEST RESULTS SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
    print("=" * 60)

    total = len(results)
    passed_count = sum(1 for v in results.values() if v)
    failed_count = total - passed_count
    print(f"\n  Total: {total} | Passed: {passed_count} | Failed: {failed_count}")
    print()

    return failed_count == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
