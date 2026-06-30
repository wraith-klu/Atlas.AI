"""
supabase_client.py

Client wrapper for Supabase database operations.
Provides compatibility with local SQLite (db_manager.py) when USE_CLOUD_DB=false.
Supports multi-user profile structures where users can be registered dynamically.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import get_logger

# Import local SQLite manager for fallback
import database.db_manager as local_db

load_dotenv()
logger = get_logger("SupabaseClient")

USE_CLOUD_DB = os.getenv("USE_CLOUD_DB", "false").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

_client = None

def get_supabase_client():
    """
    Initialises and returns the Supabase client using the service key.
    """
    global _client
    if not USE_CLOUD_DB:
        return None

    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase URL or Service Key not configured in .env. Falling back to SQLite.")
        return None

    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Connected to Supabase client successfully.")
        return _client
    except Exception as e:
        logger.error(f"Failed to initialise Supabase client: {e}")
        return None


# ──────────────────────────────────────────────────────────────
# Database Wrapper Operations
# ──────────────────────────────────────────────────────────────

def save_job(job_dict: dict) -> bool:
    """
    Saves a job to the database. Upserts in Supabase, returns True if it was a new record.
    """
    if not USE_CLOUD_DB:
        return local_db.save_job(job_dict)

    client = get_supabase_client()
    if not client:
        return local_db.save_job(job_dict)

    job_id = job_dict.get("job_id")
    if not job_id:
        return False

    try:
        # Check if exists first to return correct boolean status
        exists = job_exists(job_id)
        if exists:
            return False

        date_found = job_dict.get("date_found") or datetime.utcnow().isoformat()
        raw_data = job_dict.get("raw_data") or job_dict

        data = {
            "job_id": job_id,
            "company": job_dict.get("company"),
            "title": job_dict.get("title"),
            "location": job_dict.get("location"),
            "experience_required": job_dict.get("experience_required"),
            "apply_link": job_dict.get("apply_link"),
            "description": job_dict.get("description"),
            "jd_summary": job_dict.get("jd_summary"),
            "date_found": date_found,
            "is_new": bool(job_dict.get("is_new", True)),
            "raw_data": raw_data if isinstance(raw_data, dict) else json.loads(raw_data)
        }

        client.table("jobs").upsert(data).execute()
        logger.info(f"[Supabase] Saved new job: [{data['company']}] {data['title']} ({job_id})")
        return True
    except Exception as e:
        logger.error(f"Error saving job {job_id} to Supabase: {e}")
        # Fallback to local SQLite
        return local_db.save_job(job_dict)


def job_exists(job_id: str) -> bool:
    """
    Checks if a job exists in the database.
    """
    if not USE_CLOUD_DB:
        return local_db.job_exists(job_id)

    client = get_supabase_client()
    if not client:
        return local_db.job_exists(job_id)

    try:
        response = client.table("jobs").select("job_id").eq("job_id", job_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error(f"Error checking job existence for {job_id} on Supabase: {e}")
        return local_db.job_exists(job_id)


def get_new_jobs(user_id=None) -> list:
    """
    Fetches all jobs that are marked is_new = true.
    """
    if not USE_CLOUD_DB:
        return local_db.get_new_jobs()

    client = get_supabase_client()
    if not client:
        return local_db.get_new_jobs()

    try:
        response = client.table("jobs").select("*").eq("is_new", True).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching new jobs from Supabase: {e}")
        return local_db.get_new_jobs()


def save_match_score(user_id: str, job_id: str, score_dict: dict) -> bool:
    """
    Saves or updates a user-job match evaluation details.
    """
    if not USE_CLOUD_DB:
        # Compatibility with old function signature
        local_db.save_match_score(
            job_id=job_id,
            score=score_dict.get("match_score", 0.0),
            reason=score_dict.get("match_reason", ""),
            missing_skills=score_dict.get("missing_skills", []),
            matching_skills=score_dict.get("matching_skills", []),
            recommendation=score_dict.get("recommendation", "SKIP"),
            quick_tip=score_dict.get("quick_tip", "")
        )
        # Also cache jd_summary on job if present
        if "jd_summary" in score_dict:
            local_db.save_jd_summary(job_id, score_dict["jd_summary"])
        return True

    client = get_supabase_client()
    if not client:
        return False

    try:
        # Upsert match score
        match_data = {
            "user_id": user_id,
            "job_id": job_id,
            "match_score": float(score_dict.get("match_score", 0.0)),
            "match_reason": score_dict.get("match_reason"),
            "missing_skills": score_dict.get("missing_skills", []),
            "matching_skills": score_dict.get("matching_skills", []),
            "recommendation": score_dict.get("recommendation"),
            "quick_tip": score_dict.get("quick_tip"),
            "scored_at": datetime.utcnow().isoformat()
        }
        client.table("job_matches").upsert(match_data, on_conflict="user_id,job_id").execute()

        # Update jd_summary on the jobs table if it was generated
        if "jd_summary" in score_dict:
            client.table("jobs").update({"jd_summary": score_dict["jd_summary"]}).eq("job_id", job_id).execute()

        logger.info(f"[Supabase] Saved match score ({match_data['match_score']}%) for user {user_id}, job {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving match score to Supabase for {job_id}: {e}")
        return False


def get_jobs_to_alert(user_id: str) -> list:
    """
    Queries jobs matched to a user with recommendation in APPLY or STRETCH,
    which have NOT yet been recorded in alerts_sent for that user.
    """
    if not USE_CLOUD_DB:
        # SQLite does not support multiple user profiles; fetch global alerts to send
        import database.db_manager as db_m
        conn = db_m.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT j.* FROM jobs j
                LEFT JOIN alerts_sent a ON j.job_id = a.job_id
                WHERE j.is_new = 1
                  AND j.recommendation IN ('APPLY', 'STRETCH')
                  AND a.job_id IS NULL
                ORDER BY j.match_score DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching SQLite alert jobs: {e}")
            return []
        finally:
            conn.close()

    client = get_supabase_client()
    if not client:
        return []

    try:
        # Step 1: Query matches for this user that are APPLY/STRETCH
        matches_resp = client.table("job_matches")\
            .select("job_id, match_score, match_reason, missing_skills, matching_skills, recommendation, quick_tip")\
            .eq("user_id", user_id)\
            .in_("recommendation", ["APPLY", "STRETCH"])\
            .execute()
        matches = matches_resp.data
        if not matches:
            return []

        # Step 2: Query already sent alerts for this user
        alerts_resp = client.table("alerts_sent").select("job_id").eq("user_id", user_id).execute()
        sent_job_ids = {a["job_id"] for a in alerts_resp.data}

        # Step 3: Filter matched jobs
        eligible_matches = [m for m in matches if m["job_id"] not in sent_job_ids]
        if not eligible_matches:
            return []

        # Step 4: Fetch job details
        job_ids = [m["job_id"] for m in eligible_matches]
        jobs_resp = client.table("jobs").select("*").in_("job_id", job_ids).execute()
        jobs_map = {j["job_id"]: j for j in jobs_resp.data}

        # Merge matching metadata back to job object for compatibility
        final_list = []
        for em in eligible_matches:
            jid = em["job_id"]
            if jid in jobs_map:
                job_obj = dict(jobs_map[jid])
                job_obj.update({
                    "match_score": em["match_score"],
                    "match_reason": em["match_reason"],
                    "missing_skills": em["missing_skills"],
                    "matching_skills": em["matching_skills"],
                    "recommendation": em["recommendation"],
                    "quick_tip": em["quick_tip"]
                })
                final_list.append(job_obj)

        # Sort matches by score descending
        final_list.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
        return final_list

    except Exception as e:
        logger.error(f"Error querying eligible jobs to alert on Supabase: {e}")
        return []


def mark_job_alerted(user_id: str, job_id: str):
    """
    Inserts a record into alerts_sent and marks the job's is_new status to false
    (if no other users require processing, but globally we mark is_new=false as completed).
    """
    if not USE_CLOUD_DB:
        local_db.mark_job_alerted(job_id)
        return

    client = get_supabase_client()
    if not client:
        local_db.mark_job_alerted(job_id)
        return

    try:
        now_str = datetime.utcnow().isoformat()
        # Insert alert run
        client.table("alerts_sent").upsert({
            "user_id": user_id,
            "job_id": job_id,
            "alert_type": "whatsapp",
            "sent_at": now_str
        }, on_conflict="user_id,job_id").execute()

        # Update global is_new status to false
        client.table("jobs").update({"is_new": False}).eq("job_id", job_id).execute()
        logger.info(f"[Supabase] Marked job {job_id} as alerted for user {user_id}")
    except Exception as e:
        logger.error(f"Error marking job {job_id} alerted on Supabase: {e}")


def get_or_create_user(whatsapp_number: str, profile_dict: dict) -> str:
    """
    Retrieves the user ID for a WhatsApp number, or registers a new user profile.
    """
    if not USE_CLOUD_DB:
        # SQLite compatibility fallback (dummy UUID)
        return "00000000-0000-0000-0000-000000000000"

    client = get_supabase_client()
    if not client:
        return "00000000-0000-0000-0000-000000000000"

    try:
        clean_num = whatsapp_number.replace("+", "").strip()
        response = client.table("users").select("id").eq("whatsapp_number", clean_num).execute()
        if response.data:
            return response.data[0]["id"]

        # If not exists, insert new user profile
        user_data = {
            "name": profile_dict.get("name", "Unknown User"),
            "whatsapp_number": clean_num,
            "batch": profile_dict.get("batch"),
            "cgpa": profile_dict.get("cgpa"),
            "skills": profile_dict.get("skills", []),
            "target_companies": profile_dict.get("target_companies", []),
            "target_locations": profile_dict.get("target_locations", []),
            "target_roles": profile_dict.get("target_roles", []),
            "experience_max": profile_dict.get("experience_max", 1),
            "alert_mode": profile_dict.get("alert_mode", "digest")
        }
        insert_resp = client.table("users").insert(user_data).execute()
        if insert_resp.data:
            new_id = insert_resp.data[0]["id"]
            logger.info(f"[Supabase] Registered user profile for {clean_num} -> ID: {new_id}")
            return new_id
        return None
    except Exception as e:
        logger.error(f"Error in get_or_create_user on Supabase: {e}")
        return None


def log_scrape(company: str, status: str, jobs_found: int, error_message: str = None):
    """
    Logs metadata about the scraper execution to scrape_logs.
    """
    if not USE_CLOUD_DB:
        local_db.log_scrape(company, status, jobs_found, error_message)
        return

    client = get_supabase_client()
    if not client:
        local_db.log_scrape(company, status, jobs_found, error_message)
        return

    try:
        data = {
            "company": company,
            "status": status,
            "jobs_found": jobs_found,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        client.table("scrape_logs").insert(data).execute()
        logger.info(f"[Supabase] Logged scrape run for {company}: Status={status}, Found={jobs_found}")
    except Exception as e:
        logger.error(f"Error logging scrape to Supabase: {e}")
        local_db.log_scrape(company, status, jobs_found, error_message)


def log_error_remote(level: str, module: str, message: str):
    """
    Saves a persistent record of runtime errors to the error_logs table.
    """
    if not USE_CLOUD_DB:
        return

    client = get_supabase_client()
    if not client:
        return

    try:
        data = {
            "level": level,
            "module": module,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        client.table("error_logs").insert(data).execute()
    except Exception as e:
        # Fallback to local printing to prevent recursion loop
        print(f"[Supabase Logging Error] Failed logging message to cloud: {e}. Message: {message}")
