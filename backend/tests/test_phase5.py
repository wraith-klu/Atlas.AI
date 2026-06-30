"""
test_phase5.py

Test suite for Phase 5 AI Tool Endpoints, User preferences, and Rate Limiting.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.main_api import app
import database.supabase_client as db

client_api = TestClient(app)


# ──────────────────────────────────────────────────────────────
# 1. AI Resume Tailoring Test
# ──────────────────────────────────────────────────────────────

@patch("utils.openrouter_client.call_llm")
def test_tailor_resume_endpoint(mock_call_llm):
    """Verifies that the /tools/tailor-resume endpoint accepts request and calls LLM client."""
    mock_call_llm.return_value = "Mocked Tailored Resume Bullet Points"

    payload = {
        "resume_text": "Experienced Python backend dev.",
        "job_description": "We are looking for a backend engineer who knows Python and Docker.",
        "job_title": "Backend Engineer",
        "company": "IBM"
    }

    response = client_api.post("/tools/tailor-resume", json=payload)
    assert response.status_code == 200, f"Error: {response.text}"
    
    data = response.json()
    assert "tailored_resume" in data
    assert data["tailored_resume"] == "Mocked Tailored Resume Bullet Points"
    mock_call_llm.assert_called_once()
    print("\n✅ /tools/tailor-resume endpoint passed!")


# ──────────────────────────────────────────────────────────────
# 2. AI Cover Letter Generator Test
# ──────────────────────────────────────────────────────────────

@patch("utils.openrouter_client.call_llm")
def test_generate_cover_letter_endpoint(mock_call_llm):
    """Verifies that the /tools/generate-cover-letter endpoint behaves correctly."""
    mock_call_llm.return_value = "Mocked Cover Letter Content"

    payload = {
        "company": "Zscaler",
        "role_title": "AI/ML Engineer",
        "jd_summary": "Looking for experts in NLP.",
        "user_skills": {"Python": 5, "PyTorch": 3},
        "extra_notes": "Mention PyTorch projects"
    }

    response = client_api.post("/tools/generate-cover-letter", json=payload)
    assert response.status_code == 200, f"Error: {response.text}"

    data = response.json()
    assert "cover_letter" in data
    assert data["cover_letter"] == "Mocked Cover Letter Content"
    mock_call_llm.assert_called_once()
    print("\n✅ /tools/generate-cover-letter endpoint passed!")


# ──────────────────────────────────────────────────────────────
# 3. User Preferences endpoints
# ──────────────────────────────────────────────────────────────

def test_user_preferences_endpoints():
    """Verifies profile fetching and updating of user search preferences."""
    # We mock or check SQLite fallback profile
    response = client_api.get("/user/profile")
    assert response.status_code == 200

    profile = response.json()
    # It might return details if user exists or "profile": None / message
    if "id" in profile or ("profile" in profile and profile["profile"] is not None):
        user_id = profile.get("id") or profile["profile"].get("id")
        headers = {"x-user-id": str(user_id)}
        
        # Test updating preferences
        payload = {
            "target_companies": ["Zscaler", "IBM"],
            "target_locations": ["Remote", "Bangalore"],
            "target_roles": ["AI Engineer", "Software Engineer"],
            "experience_max": 2,
            "alert_mode": "instant"
        }
        update_resp = client_api.put("/user/preferences", json=payload, headers=headers)
        assert update_resp.status_code == 200, f"Error: {update_resp.text}"
        print("\n✅ Profile & Preferences read/write endpoints passed!")
    else:
        print("\n⚠️ Profile & Preferences endpoints test skipped (no users registered in db).")


# ──────────────────────────────────────────────────────────────
# 4. Rate Limiting Test
# ──────────────────────────────────────────────────────────────

def test_rate_limiting_enforcement():
    """Verifies that the API rate limiter triggers 429 when threshold is reached."""
    # Reset/clear the internal tracker bucket for the test target
    from api.main_api import _rate_buckets
    _rate_buckets["skill_gaps"] = []

    # Send multiple requests to trigger rate limit (threshold is 5)
    for i in range(5):
        resp = client_api.get("/tools/skill-gaps")
        # May be 200 or 500 depending on DB state, but shouldn't be 429 yet
        assert resp.status_code != 429

    # The 6th request must trigger a 429
    resp = client_api.get("/tools/skill-gaps")
    assert resp.status_code == 429, f"Rate limit failed: {resp.text}"
    assert "Rate limit exceeded" in resp.json()["detail"]
    print("\n✅ Rate limiter verification passed (returned 429)!")
