"""
db_manager.py

Handles SQLite database operations: initial tables creation, job insertions,
deduplication checks, retrieval of new/all jobs, alert history tracking,
and scraper run statistics logging.
"""

import os
import sqlite3
import json
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("DBManager")

def get_db_path() -> str:
    """
    Returns the path to the SQLite database file in the project root.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "job_agent.db")

def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    Enables Row factory for dictionary-like results.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Creates the required tables if they do not exist:
    1. jobs: Details of scraped and filtered jobs.
    2. alerts_sent: Logs job IDs for which notifications have been sent.
    3. scrape_logs: Tracks execution stats per company scraper run.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Create jobs table with all columns for Phase 2
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                company TEXT,
                title TEXT,
                location TEXT,
                experience_required TEXT,
                apply_link TEXT,
                description TEXT,
                date_found TEXT,
                is_new INTEGER DEFAULT 1,
                match_score REAL DEFAULT 0.0,
                match_reason TEXT,
                missing_skills TEXT,
                matching_skills TEXT,
                recommendation TEXT,
                quick_tip TEXT,
                jd_summary TEXT,
                raw_data TEXT
            )
        """)
        
        # Create alerts_sent table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts_sent (
                job_id TEXT PRIMARY KEY,
                sent_at TEXT
            )
        """)
        
        # Create scrape_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                status TEXT,
                jobs_found INTEGER,
                error TEXT,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        
        # Dynamic check and migration to add any missing columns to existing databases
        conn_alter = get_connection()
        try:
            cursor_alter = conn_alter.cursor()
            cursor_alter.execute("PRAGMA table_info(jobs)")
            existing_columns = [row["name"] for row in cursor_alter.fetchall()]
            
            new_columns = {
                "match_reason": "TEXT",
                "missing_skills": "TEXT",
                "matching_skills": "TEXT",
                "recommendation": "TEXT",
                "quick_tip": "TEXT",
                "jd_summary": "TEXT"
            }
            
            alter_needed = False
            for col_name, col_type in new_columns.items():
                if col_name not in existing_columns:
                    cursor_alter.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column {col_name} ({col_type}) to jobs table.")
                    alter_needed = True
                    
            if alter_needed:
                conn_alter.commit()
        except Exception as e:
            logger.error(f"Error checking/migrating jobs table schema: {e}")
            conn_alter.rollback()
        finally:
            conn_alter.close()
            
        logger.info("SQLite Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def job_exists(job_id: str) -> bool:
    """
    Checks if a job exists in the database by its unique job_id.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        logger.error(f"Error checking job existence for {job_id}: {e}")
        return False
    finally:
        conn.close()

def save_job(job_dict: dict) -> bool:
    """
    Inserts a job into the database if it doesn't already exist.
    Returns True if it is a new insertion, and False if it is a duplicate.
    """
    job_id = job_dict.get("job_id")
    if not job_id:
        logger.warning("Attempted to save job dictionary with missing 'job_id'.")
        return False
        
    if job_exists(job_id):
        return False
        
    conn = get_connection()
    try:
        cursor = conn.cursor()
        date_found = job_dict.get("date_found") or datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO jobs (
                job_id, company, title, location, experience_required, 
                apply_link, description, date_found, is_new, match_score, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            job_dict.get("company"),
            job_dict.get("title"),
            job_dict.get("location"),
            job_dict.get("experience_required"),
            job_dict.get("apply_link"),
            job_dict.get("description"),
            date_found,
            job_dict.get("is_new", 1),
            job_dict.get("match_score", 0.0),
            json.dumps(job_dict.get("raw_data") or job_dict)
        ))
        conn.commit()
        logger.info(f"Saved new job: [{job_dict.get('company')}] {job_dict.get('title')} ({job_id})")
        return True
    except Exception as e:
        logger.error(f"Error saving job {job_id} to DB: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_new_jobs() -> list:
    """
    Fetches all jobs that are marked is_new = 1 and have NOT had an alert sent.
    Returns a list of dicts.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Query jobs not present in alerts_sent and has is_new = 1
        cursor.execute("""
            SELECT j.* FROM jobs j
            LEFT JOIN alerts_sent a ON j.job_id = a.job_id
            WHERE j.is_new = 1 AND a.job_id IS NULL
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching new jobs: {e}")
        return []
    finally:
        conn.close()

def get_all_jobs(company: str = None) -> list:
    """
    Fetches all processed jobs with an optional company filter.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if company:
            cursor.execute("SELECT * FROM jobs WHERE company = ?", (company,))
        else:
            cursor.execute("SELECT * FROM jobs")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching all jobs: {e}")
        return []
    finally:
        conn.close()

def mark_job_alerted(job_id: str):
    """
    Marks a job as alerted by saving it to the alerts_sent table
    and setting its is_new flag to 0.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Insert alert run
        cursor.execute("INSERT OR REPLACE INTO alerts_sent (job_id, sent_at) VALUES (?, ?)", (job_id, now_str))
        # Update is_new status in jobs table
        cursor.execute("UPDATE jobs SET is_new = 0 WHERE job_id = ?", (job_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error marking job {job_id} as alerted: {e}")
        conn.rollback()
    finally:
        conn.close()

def log_scrape(company: str, status: str, jobs_found: int, error: str = None):
    """
    Logs each scrape run details into the scrape_logs database table.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO scrape_logs (company, status, jobs_found, error, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (company, status, jobs_found, error, now_str))
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging scrape metadata for {company}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_stats() -> dict:
    """
    Returns statistics summaries: total jobs, new jobs, and count of jobs per company.
    """
    conn = get_connection()
    stats = {
        "total_jobs": 0,
        "new_jobs": 0,
        "company_stats": {}
    }
    try:
        cursor = conn.cursor()
        
        # Get total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        stats["total_jobs"] = cursor.fetchone()[0]
        
        # Get new (unalerted) jobs
        cursor.execute("""
            SELECT COUNT(*) FROM jobs j
            LEFT JOIN alerts_sent a ON j.job_id = a.job_id
            WHERE j.is_new = 1 AND a.job_id IS NULL
        """)
        stats["new_jobs"] = cursor.fetchone()[0]
        
        # Get jobs per company
        cursor.execute("SELECT company, COUNT(*) as count FROM jobs GROUP BY company")
        for row in cursor.fetchall():
            stats["company_stats"][row["company"]] = row["count"]
            
        return stats
    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")
        return stats
    finally:
        conn.close()

def save_match_score(job_id: str, score: float, reason: str, missing_skills, matching_skills, recommendation: str, quick_tip: str):
    """
    Updates the jobs table with the calculated match score and analysis fields.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Serialize lists if passed as python lists
        missing_str = json.dumps(missing_skills) if isinstance(missing_skills, list) else missing_skills
        matching_str = json.dumps(matching_skills) if isinstance(matching_skills, list) else matching_skills
        
        cursor.execute("""
            UPDATE jobs 
            SET match_score = ?,
                match_reason = ?,
                missing_skills = ?,
                matching_skills = ?,
                recommendation = ?,
                quick_tip = ?
            WHERE job_id = ?
        """, (score, reason, missing_str, matching_str, recommendation, quick_tip, job_id))
        conn.commit()
        logger.info(f"Updated match score ({score}%) for job ID: {job_id}")
    except Exception as e:
        logger.error(f"Error saving match score for job {job_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_jd_summary(job_id: str, summary: str):
    """
    Saves/caches the generated JD summary to avoid re-calling the API.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET jd_summary = ? WHERE job_id = ?", (summary, job_id))
        conn.commit()
        logger.info(f"Cached JD summary for job ID: {job_id}")
    except Exception as e:
        logger.error(f"Error saving JD summary for job {job_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_jobs_by_recommendation(recommendation: str) -> list:
    """
    Retrieves all jobs with a specific recommendation, ordered by match_score descending.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE recommendation = ? ORDER BY match_score DESC", (recommendation,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching jobs by recommendation '{recommendation}': {e}")
        return []
    finally:
        conn.close()

def get_top_matches(limit: int = 10) -> list:
    """
    Retrieves top N jobs sorted by match_score descending.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE match_score > 0 ORDER BY match_score DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching top matches: {e}")
        return []
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────
# Phase 3 — Alert helpers
# ──────────────────────────────────────────────────────────────

def get_unalerted_matches() -> list:
    """
    Fetches jobs with recommendation APPLY or STRETCH that have
    NOT yet been recorded in alerts_sent.

    Returns:
        list of dicts, sorted by match_score descending.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT j.* FROM jobs j
            LEFT JOIN alerts_sent a ON j.job_id = a.job_id
            WHERE j.recommendation IN ('APPLY', 'STRETCH')
              AND a.job_id IS NULL
            ORDER BY j.match_score DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching unalerted matches: {e}")
        return []
    finally:
        conn.close()


def get_alert_history(days: int = 7) -> list:
    """
    Returns alerts_sent rows joined with job details for the
    last *days* days.

    Returns:
        list of dicts with both job and alert columns.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT j.*, a.sent_at
            FROM alerts_sent a
            JOIN jobs j ON j.job_id = a.job_id
            WHERE a.sent_at >= date('now', ?)
            ORDER BY a.sent_at DESC
        """, (f"-{days} days",))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        return []
    finally:
        conn.close()


def count_alerts_today() -> int:
    """
    Returns the number of alerts sent today.
    Useful to prevent double-sends in digest mode.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM alerts_sent WHERE sent_at LIKE ?",
            (f"{today_str}%",)
        )
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error counting today's alerts: {e}")
        return 0
    finally:
        conn.close()
