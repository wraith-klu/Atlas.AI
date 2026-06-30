"""
phase2_runner.py

The main runner for Phase 2. Loads unscored jobs, performs JD summarization and
AI matching, prints ranked result tables, and generates a formatted skill gap report.
"""

import os
import time
import json
from datetime import datetime
from utils.config_loader import load_profile
from database.db_manager import (
    get_connection, 
    save_match_score, 
    get_jobs_by_recommendation, 
    get_top_matches
)
from scraper.jd_summarizer import summarize_jd
from scraper.match_engine import match_job_to_profile
from utils.skill_gap import generate_gap_report, analyze_skill_gaps
from utils.logger import get_logger

logger = get_logger("Phase2Runner")

def run_phase2() -> int:
    """
    Orchestrates the Phase 2 scoring and matching workflow.
    
    Returns:
        int: Number of new jobs scored.
    """
    logger.info("Starting Phase 2 AI scoring and matching...")
    
    # 1. Load user profile
    try:
        profile = load_profile()
        if not profile:
            logger.error("Failed to load user profile configuration.")
            return 0
    except Exception as e:
        logger.error(f"Error loading user profile: {e}")
        return 0
        
    # 2. Load all new unscored jobs
    conn = get_connection()
    unscored_jobs = []
    try:
        cursor = conn.cursor()
        # Look for jobs where match_score is 0 (default) and is_new is 1
        cursor.execute("SELECT * FROM jobs WHERE is_new = 1 AND match_score = 0.0")
        unscored_jobs = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error loading unscored jobs: {e}")
        return 0
    finally:
        conn.close()
        
    total_unscored = len(unscored_jobs)
    if total_unscored == 0:
        logger.info("No new unscored jobs found in the database. Proceeding to display reports.")
    else:
        logger.info(f"Found {total_unscored} new unscored jobs to evaluate.")
        
    # 3. Process each job
    scored_in_this_run = []
    for idx, job in enumerate(unscored_jobs, 1):
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        job_id = job.get("job_id")
        
        print(f"🤖 Scoring job {idx}/{total_unscored}: {company} — {title}")
        
        # a. Summarize JD (caches automatically inside summarize_jd)
        try:
            summary = summarize_jd(job)
        except Exception as e:
            logger.error(f"Error summarizing JD for job {job_id}: {e}")
            summary = "No description available"
            
        # b. Score job against profile
        try:
            match_data = match_job_to_profile(job, profile)
            
            # c. Save match results to DB
            save_match_score(
                job_id=job_id,
                score=match_data["match_score"],
                reason=match_data["match_reason"],
                missing_skills=match_data["missing_skills"],
                matching_skills=match_data["matching_skills"],
                recommendation=match_data["recommendation"],
                quick_tip=match_data["quick_tip"]
            )
            
            # Keep track for report
            job_copy = dict(job)
            job_copy.update(match_data)
            job_copy["jd_summary"] = summary
            scored_in_this_run.append(job_copy)
            
        except Exception as e:
            logger.error(f"Error scoring job {job_id} against profile: {e}")
            
        # d. Rate limiting protection delay
        time.sleep(1.5)
        
    # 4. Generate & Display Reports
    display_and_save_reports(total_unscored, scored_in_this_run)
    return total_unscored

def display_and_save_reports(total_scored_this_run: int, scored_this_run: list):
    """
    Gathers scored jobs from the database and prints/logs the formatted reports.
    """
    # Fetch all scored jobs to generate global statistics and gap analysis
    conn = get_connection()
    all_scored_jobs = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE match_score > 0.0")
        all_scored_jobs = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error loading scored jobs for reporting: {e}")
    finally:
        conn.close()
        
    total_scored = len(all_scored_jobs)
    
    apply_jobs = [j for j in all_scored_jobs if j.get("recommendation") == "APPLY"]
    stretch_jobs = [j for j in all_scored_jobs if j.get("recommendation") == "STRETCH"]
    skip_jobs = [j for j in all_scored_jobs if j.get("recommendation") == "SKIP"]
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Print Ranked Results Table (console)
    print("\n" + "="*80)
    print(f"RANKED RESULTS TABLE ({today_str})")
    print("="*80)
    print(f"{'RANK':<5} | {'COMPANY':<12} | {'TITLE':<30} | {'LOCATION':<15} | {'SCORE':<5} | {'RECOMMENDATION'}")
    print("-"*80)
    
    sorted_jobs = sorted(all_scored_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    for idx, job in enumerate(sorted_jobs, 1):
        company = job.get("company", "N/A")[:12]
        title = job.get("title", "N/A")[:30]
        location = job.get("location", "N/A")[:15]
        score = int(job.get("match_score", 0))
        rec = job.get("recommendation", "N/A")
        
        rec_symbol = "✅ APPLY" if rec == "APPLY" else ("⚠️ STRETCH" if rec == "STRETCH" else "❌ SKIP")
        print(f"{idx:<5} | {company:<12} | {title:<30} | {location:<15} | {score:>3}% | {rec_symbol}")
        
    print("="*80 + "\n")
    
    # 2. Build the detailed output report string
    report_lines = []
    report_lines.append(f"🤖 AI JOB AGENT — Phase 2 Results ({today_str})")
    report_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report_lines.append(f"Total jobs scored: {total_scored}")
    report_lines.append(f"✅ APPLY (score ≥ 70%): {len(apply_jobs)} jobs")
    report_lines.append(f"⚠️ STRETCH (score 50-69%): {len(stretch_jobs)} jobs")
    report_lines.append(f"❌ SKIP (score < 50%): {len(skip_jobs)} jobs")
    report_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    report_lines.append("🏆 TOP MATCHES:")
    top_matches = sorted_jobs[:10]  # Show top 10 matches
    for idx, job in enumerate(top_matches, 1):
        company = job.get("company", "N/A")
        title = job.get("title", "N/A")
        location = job.get("location", "N/A")
        score = int(job.get("match_score", 0))
        apply_link = job.get("apply_link", "N/A")
        
        # Parse matching/missing skills
        matching_skills = job.get("matching_skills", "[]")
        if isinstance(matching_skills, str):
            try:
                matching_skills = json.loads(matching_skills)
            except Exception:
                matching_skills = [matching_skills] if matching_skills else []
                
        missing_skills = job.get("missing_skills", "[]")
        if isinstance(missing_skills, str):
            try:
                missing_skills = json.loads(missing_skills)
            except Exception:
                missing_skills = [missing_skills] if missing_skills else []
                
        tip = job.get("quick_tip", "None")
        
        report_lines.append(f"{idx}. {company} — {title} | {location} | Score: {score}%")
        report_lines.append(f"   ✅ Matching: {', '.join(matching_skills) if matching_skills else 'None'}")
        report_lines.append(f"   ❌ Missing: {', '.join(missing_skills) if missing_skills else 'None'}")
        report_lines.append(f"   💡 Tip: {tip}")
        report_lines.append(f"   🔗 Apply: {apply_link}\n")
        
    report_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Add Skill Gap Report
    gap_report = generate_gap_report()
    report_lines.append(gap_report)
    report_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    full_report = "\n".join(report_lines)
    
    # Print the report to the console
    print(full_report)
    
    # Save the report to logs/phase2_report_YYYY-MM-DD.txt
    project_root = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    report_filename = f"phase2_report_{today_str}.txt"
    report_path = os.path.join(logs_dir, report_filename)
    
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        logger.info(f"Full report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Failed to save phase 2 report: {e}")

if __name__ == "__main__":
    run_phase2()
