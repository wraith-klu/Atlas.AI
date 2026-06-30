"""
test_phase4.py

Test suite for Phase 4 cloud database migration, API, and workflow integrity.
"""

import os
import sys
import yaml
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

import database.supabase_client as db
from api.main_api import app

client_api = TestClient(app)


# ──────────────────────────────────────────────────────────────
# 1. Supabase Connection Test
# ──────────────────────────────────────────────────────────────

def test_supabase_connection():
    """Checks that the Supabase client can connect and select from tables if USE_CLOUD_DB is true."""
    if not db.USE_CLOUD_DB:
        pytest.skip("USE_CLOUD_DB is false. Skipping cloud database connection test.")

    client = db.get_supabase_client()
    assert client is not None, "Failed to initialize Supabase client."

    try:
        # Ping check on scrape_logs or jobs table
        response = client.table("scrape_logs").select("id").limit(1).execute()
        assert response.data is not None, "Failed connection check query on Supabase."
        print("\n✅ Supabase connection successful!")
    except Exception as e:
        if "PGRST205" in str(e) or "Could not find the table" in str(e):
            pytest.skip("Supabase tables not found in the database. Please paste and run database/supabase_schema.sql in the Supabase SQL editor.")
        else:
            pytest.fail(f"Supabase connection test failed: {e}")



# ──────────────────────────────────────────────────────────────
# 2. FastAPI Health Check Test
# ──────────────────────────────────────────────────────────────

def test_api_health_check():
    """Verifies that GET / returns a 200 running response."""
    response = client_api.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    print("\n✅ API Health check passed!")


# ──────────────────────────────────────────────────────────────
# 3. User Registration Test
# ──────────────────────────────────────────────────────────────

def test_user_registration():
    """Verifies user registration endpoint registers and returns a user_id."""
    if not db.USE_CLOUD_DB:
        pytest.skip("USE_CLOUD_DB is false. Skipping cloud user registration test.")

    payload = {
        "name": "Integration Test User",
        "whatsapp_number": "919999999999",
        "batch": 2027,
        "cgpa": 9.0,
        "skills": ["Python", "Docker"],
        "target_companies": ["ibm"],
        "target_locations": ["Bangalore"],
        "target_roles": ["Software Engineer"],
        "experience_max": 1,
        "alert_mode": "digest"
    }

    response = client_api.post("/users/register", json=payload)
    if response.status_code == 500 and ("Could not create user" in response.text or "PGRST205" in response.text or "Could not find the table" in response.text):
        pytest.skip("Supabase users table not created yet. Run migrations in Supabase SQL editor.")
    assert response.status_code == 201, f"Failed registration: {response.text}"

    data = response.json()
    assert "user_id" in data
    assert data["user_id"] != "00000000-0000-0000-0000-000000000000"
    print(f"\n✅ User registration test passed! Registered ID: {data['user_id']}")

    # Clean up test user from DB
    sb_client = db.get_supabase_client()
    if sb_client:
        try:
            sb_client.table("users").delete().eq("id", data["user_id"]).execute()
        except Exception:
            pass



# ──────────────────────────────────────────────────────────────
# 4. GET Latest Jobs Test
# ──────────────────────────────────────────────────────────────

def test_get_latest_jobs():
    """Verifies that the GET /jobs/latest endpoint returns a list."""
    response = client_api.get("/jobs/latest?limit=5")
    if response.status_code == 500 and ("PGRST205" in response.text or "Could not find the table" in response.text):
        pytest.skip("Supabase jobs table not created yet. Run migrations in Supabase SQL editor.")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"\n✅ Latest jobs endpoint returned list of size {len(data)}")



# ──────────────────────────────────────────────────────────────
# 5. Pipeline Trigger Mock Test
# ──────────────────────────────────────────────────────────────

def test_pipeline_trigger_unauthorized():
    """Verifies that triggering the pipeline without proper X-API-Key returns 401."""
    response = client_api.post("/jobs/run-pipeline")
    assert response.status_code == 401


# ──────────────────────────────────────────────────────────────
# 6. GitHub Actions YAML Syntax Validation
# ──────────────────────────────────────────────────────────────

def test_github_actions_yaml_valid():
    """Ensures the GitHub Actions workflow file has valid YAML syntax."""
    workflow_path = os.path.join(project_root, ".github", "workflows", "daily_job_search.yml")
    assert os.path.exists(workflow_path), f"Workflow file not found at: {workflow_path}"

    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            yaml_content = yaml.safe_load(f)
        assert yaml_content is not None
        # In python-yaml, the unquoted key 'on' is parsed as a boolean True
        assert "on" in yaml_content or True in yaml_content
        assert "jobs" in yaml_content
        print("\n✅ GitHub Actions workflow YAML syntax is valid!")
    except Exception as e:
        pytest.fail(f"YAML parsing failed for GitHub Actions workflow: {e}")



# ──────────────────────────────────────────────────────────────
# Runner helper
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
