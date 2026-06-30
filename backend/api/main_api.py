"""
main_api.py

FastAPI REST API backend for the AI Job Search Agent.
Enables user registration, preference updates, match history retrieval, and pipeline triggers.
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is on path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import database.supabase_client as db
from main import main as run_orchestrator
from utils.logger import get_logger

logger = get_logger("FastAPIBackend")

app = FastAPI(
    title="AI Job Search Agent API",
    description="Backend API for managing users, job matches, and alerting pipelines.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────────────────────

class UserRegisterSchema(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Saurabh Yadav"})
    whatsapp_number: str = Field(..., json_schema_extra={"example": "919792453534"})
    batch: Optional[int] = Field(None, json_schema_extra={"example": 2027})
    cgpa: Optional[float] = Field(None, json_schema_extra={"example": 9.61})
    skills: List[str] = Field(default=[], json_schema_extra={"example": ["Python", "SQL", "PyTorch"]})
    target_companies: List[str] = Field(default=[], json_schema_extra={"example": ["ibm", "zscaler"]})
    target_locations: List[str] = Field(default=[], json_schema_extra={"example": ["Bangalore", "Noida"]})
    target_roles: List[str] = Field(default=[], json_schema_extra={"example": ["Software Engineer", "AI Engineer"]})
    experience_max: int = Field(default=1, json_schema_extra={"example": 1})
    alert_mode: str = Field(default="digest", json_schema_extra={"example": "digest"})


class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(None)
    batch: Optional[int] = Field(None)
    cgpa: Optional[float] = Field(None)
    skills: Optional[List[str]] = Field(None)
    target_companies: Optional[List[str]] = Field(None)
    target_locations: Optional[List[str]] = Field(None)
    target_roles: Optional[List[str]] = Field(None)
    experience_max: Optional[int] = Field(None)
    alert_mode: Optional[str] = Field(None)

class PipelineResultSchema(BaseModel):
    jobs_found: int
    jobs_scored: int
    alerts_sent: int


# ──────────────────────────────────────────────────────────────
# Authentication Helper
# ──────────────────────────────────────────────────────────────

API_KEY = os.getenv("API_KEY", "super-secret-key-123")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Validates API requests executing operations that consume resource credits.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header credential."
        )
    return x_api_key


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """Simple status check."""
    return {"status": "running", "timestamp": datetime.utcnow().isoformat()}


@app.post("/users/register", status_code=status.HTTP_201_CREATED, tags=["Users"])
def register_user(user_data: UserRegisterSchema):
    """
    Registers a new user profile in the database and returns their UUID.
    """
    try:
        user_dict = {
            "name": user_data.name,
            "whatsapp_number": user_data.whatsapp_number,
            "batch": user_data.batch,
            "cgpa": user_data.cgpa,
            "skills": user_data.skills,
            "target_companies": user_data.target_companies,
            "target_locations": user_data.target_locations,
            "target_roles": user_data.target_roles,
            "experience_max": user_data.experience_max,
            "alert_mode": user_data.alert_mode
        }
        uid = db.get_or_create_user(user_data.whatsapp_number, user_dict)
        if not uid or uid == "00000000-0000-0000-0000-000000000000":
            raise HTTPException(
                status_code=500,
                detail="Could not create user. Verify Supabase availability or connection credentials."
            )
        return {"user_id": uid, "message": "User registered successfully."}
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/profile", tags=["Users"])
def get_user_profile(user_id: str):
    """
    Returns the complete profile configuration for a user.
    """
    client = db.get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase client is not initialized.")

    try:
        response = client.table("users").select("*").eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User profile not found.")
        return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/{user_id}/profile", tags=["Users"])
def update_user_profile(user_id: str, update_data: UserUpdateSchema):
    """
    Updates the preferences and targets on a user profile.
    """
    client = db.get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase client is not initialized.")

    try:
        # Filter fields that are provided
        updates = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            return {"message": "No update fields specified."}

        response = client.table("users").update(updates).eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found or update failed.")
        return {"message": "User profile updated successfully.", "profile": response.data[0]}
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/latest", tags=["Jobs"])
def get_latest_jobs(limit: int = Query(20, le=100)):
    """
    Returns the most recently found jobs.
    """
    client = db.get_supabase_client()
    if not client:
        # Fallback to local SQLite
        import database.db_manager as db_m
        return db_m.get_top_matches(limit)

    try:
        response = client.table("jobs").select("*").order("date_found", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error querying latest jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/matches/{user_id}", tags=["Jobs"])
def get_job_matches(
    user_id: str,
    recommendation: Optional[str] = Query(None, description="Filter by: APPLY, STRETCH, or SKIP"),
    limit: int = Query(10, le=50)
):
    """
    Fetches AI evaluated job matches for a specific user profile.
    """
    client = db.get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase integration required for user matches.")

    try:
        query = client.table("job_matches").select("*").eq("user_id", user_id)
        if recommendation:
            query = query.eq("recommendation", recommendation.upper())
        
        matches_resp = query.order("match_score", desc=True).limit(limit).execute()
        matches = matches_resp.data
        if not matches:
            return []

        # Resolve job details for matching records
        job_ids = [m["job_id"] for m in matches]
        jobs_resp = client.table("jobs").select("*").in_("job_id", job_ids).execute()
        jobs_map = {j["job_id"]: j for j in jobs_resp.data}

        results = []
        for m in matches:
            jid = m["job_id"]
            if jid in jobs_map:
                res = dict(jobs_map[jid])
                res.update(m)
                results.append(res)

        results.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
        return results
    except Exception as e:
        logger.error(f"Error retrieving user job matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/stats", tags=["Jobs"])
def get_jobs_stats():
    """
    Aggregates run statistics. Returns count by company and last scrape date.
    """
    client = db.get_supabase_client()
    if not client:
        # Local SQLite stats compatibility
        import database.db_manager as db_m
        return db_m.get_stats()

    try:
        # Total jobs count
        jobs_count_resp = client.table("jobs").select("id", count="exact").execute()
        total_jobs = jobs_count_resp.count if jobs_count_resp.count is not None else len(jobs_count_resp.data)

        # Scrape count by company
        jobs_resp = client.table("jobs").select("company").execute()
        by_company = {}
        for j in jobs_resp.data:
            co = j["company"]
            by_company[co] = by_company.get(co, 0) + 1

        # Last log time
        logs_resp = client.table("scrape_logs").select("timestamp").order("timestamp", desc=True).limit(1).execute()
        last_scrape = logs_resp.data[0]["timestamp"] if logs_resp.data else None

        return {
            "total_jobs": total_jobs,
            "by_company": by_company,
            "last_scrape_time": last_scrape
        }
    except Exception as e:
        logger.error(f"Error generating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/run-pipeline", response_model=PipelineResultSchema, tags=["Jobs"])
def run_pipeline_manually(x_api_key: str = Depends(verify_api_key)):
    """
    Runs the complete scraper matching notification pipeline manually.
    Requires header X-API-Key verify check to authenticate trigger.
    """
    try:
        logger.info("Manual pipeline run triggered via API.")
        results = run_orchestrator(force_alerts=True)
        return results
    except Exception as e:
        logger.error(f"Failed manual pipeline run: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")


@app.get("/alerts/history/{user_id}", tags=["Alerts"])
def get_user_alert_history(user_id: str, days: int = Query(7, le=30)):
    """
    Returns history of alerts sent to this user.
    """
    client = db.get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase integration required for alert history.")

    try:
        # Query matching alerts
        alerts_resp = client.table("alerts_sent").select("*").eq("user_id", user_id).execute()
        alerts = alerts_resp.data
        if not alerts:
            return []

        # Resolve job details for alerting events
        job_ids = [a["job_id"] for a in alerts]
        jobs_resp = client.table("jobs").select("*").in_("job_id", job_ids).execute()
        jobs_map = {j["job_id"]: j for j in jobs_resp.data}

        results = []
        for a in alerts:
            jid = a["job_id"]
            if jid in jobs_map:
                res = dict(jobs_map[jid])
                res["sent_at"] = a["sent_at"]
                results.append(res)

        results.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
        return results
    except Exception as e:
        logger.error(f"Error querying user alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# Simple In-Memory Rate Limiter
# ──────────────────────────────────────────────────────────────
from collections import defaultdict
import time as _time

_rate_buckets: dict = defaultdict(list)
_RATE_WINDOW = 60  # seconds
_RATE_LIMIT = 5    # requests per window per endpoint-key


def _check_rate_limit(key: str):
    """Raise 429 if more than _RATE_LIMIT calls in the window."""
    now = _time.time()
    bucket = _rate_buckets[key]
    # Purge old entries
    _rate_buckets[key] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(_rate_buckets[key]) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {_RATE_LIMIT} requests per {_RATE_WINDOW}s."
        )
    _rate_buckets[key].append(now)


# ──────────────────────────────────────────────────────────────
# AI Tool Endpoints
# ──────────────────────────────────────────────────────────────

class TailorResumeRequest(BaseModel):
    resume_text: str = Field(..., json_schema_extra={"example": "Experienced Python developer..."})
    job_description: str = Field(..., json_schema_extra={"example": "We are looking for a backend engineer..."})
    job_title: Optional[str] = ""
    company: Optional[str] = ""


class CoverLetterRequest(BaseModel):
    company: str = Field(..., json_schema_extra={"example": "Zscaler"})
    role_title: str = Field(..., json_schema_extra={"example": "AI Engineer"})
    jd_summary: Optional[str] = ""
    user_skills: Optional[dict] = {}
    extra_notes: Optional[str] = ""


@app.post("/tools/tailor-resume", tags=["AI Tools"], summary="Tailor a resume using AI")
async def tailor_resume(body: TailorResumeRequest):
    """Use the OpenRouter LLM to tailor a resume for a specific job description."""
    _check_rate_limit("tailor_resume")
    try:
        from utils.openrouter_client import call_llm
        prompt = (
            "You are a professional resume consultant. Rewrite the following resume to better match "
            f"the job description below. Keep all factual information but reorder, rephrase, and "
            f"emphasize skills and experiences that align with the role.\n\n"
            f"--- ORIGINAL RESUME ---\n{body.resume_text}\n\n"
            f"--- JOB DESCRIPTION ---\n{body.job_description}\n\n"
            f"--- JOB TITLE ---\n{body.job_title or 'N/A'}\n"
            f"--- COMPANY ---\n{body.company or 'N/A'}\n\n"
            f"Return ONLY the tailored resume text. No commentary."
        )
        result = call_llm(prompt)
        return {"tailored_resume": result}
    except ImportError:
        raise HTTPException(status_code=501, detail="LLM module not available.")
    except Exception as e:
        logger.error(f"Resume tailoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/generate-cover-letter", tags=["AI Tools"], summary="Generate a cover letter using AI")
async def generate_cover_letter(body: CoverLetterRequest):
    """Generate a professional cover letter tailored to the target company and role."""
    _check_rate_limit("cover_letter")
    try:
        from utils.openrouter_client import call_llm
        prompt = (
            "Write a professional, compelling cover letter for the following job application.\n\n"
            f"Company: {body.company}\n"
            f"Role: {body.role_title}\n"
            f"Job Summary: {body.jd_summary or 'Not provided'}\n"
            f"Candidate Skills: {body.user_skills or 'Not specified'}\n"
            f"Additional Notes: {body.extra_notes or 'None'}\n\n"
            "The letter should be 3-4 paragraphs, professional but personable. "
            "Return ONLY the cover letter text."
        )
        result = call_llm(prompt)
        return {"cover_letter": result}
    except ImportError:
        raise HTTPException(status_code=501, detail="LLM module not available.")
    except Exception as e:
        logger.error(f"Cover letter generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/skill-gaps", tags=["AI Tools"], summary="Get aggregated skill gaps from match data")
async def get_skill_gaps():
    """Analyze all scored jobs and return the most frequently missing skills."""
    _check_rate_limit("skill_gaps")
    try:
        from collections import Counter
        matches = db.get_all_match_scores()
        missing_counter = Counter()
        for m in matches:
            gaps = m.get("missing_skills") or m.get("skill_gaps") or []
            if isinstance(gaps, str):
                gaps = [s.strip() for s in gaps.split(",") if s.strip()]
            for skill in gaps:
                missing_counter[skill.strip().title()] += 1

        result = [
            {"skill": skill, "count": count}
            for skill, count in missing_counter.most_common(15)
        ]
        return result
    except Exception as e:
        logger.error(f"Skill gap analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# User Profile & Preferences Endpoints
# ──────────────────────────────────────────────────────────────

class UserPreferencesSchema(BaseModel):
    target_companies: Optional[List[str]] = []
    target_locations: Optional[List[str]] = []
    target_roles: Optional[List[str]] = []
    experience_max: Optional[int] = 1
    alert_mode: Optional[str] = "digest"


@app.get("/user/profile", tags=["User"], summary="Get user profile")
async def get_user_profile(x_user_id: Optional[str] = Header(None)):
    """Return a user's profile and preferences."""
    try:
        users = db.get_all_users()
        if x_user_id:
            user = next((u for u in users if str(u.get("id")) == x_user_id), None)
        else:
            user = users[0] if users else None
        if not user:
            return {"message": "No user found", "profile": None}
        return user
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/user/preferences", tags=["User"], summary="Update user preferences")
async def update_user_preferences(
    prefs: UserPreferencesSchema,
    x_user_id: Optional[str] = Header(None)
):
    """Update a user's search preferences."""
    try:
        users = db.get_all_users()
        if x_user_id:
            user = next((u for u in users if str(u.get("id")) == x_user_id), None)
        else:
            user = users[0] if users else None
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        user_id = user.get("id")
        db.update_user(user_id, prefs.model_dump())
        return {"message": "Preferences updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preferences update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Global Exception Handler
@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    logger.error(f"Unhandled endpoint exception: {exc}")
    # Write to remote error logs
    try:
        db.log_error_remote("ERROR", "FastAPIBackend", str(exc))
    except Exception:
        pass
    return {"detail": "An internal server error occurred."}
