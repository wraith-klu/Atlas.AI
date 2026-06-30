"""
jd_summarizer.py

Summarizes job descriptions using OpenRouter LLM.
Includes database caching to minimize API calls.
"""

from utils.openrouter_client import call_llm
from database.db_manager import get_connection, save_jd_summary
from utils.logger import get_logger

logger = get_logger("JDSummarizer")

def summarize_jd(job_dict: dict) -> str:
    """
    Summarizes a job description in exactly 3 bullet points.
    Checks the database cache first.
    
    Args:
        job_dict (dict): A dictionary containing job details: job_id, company, title, description.
        
    Returns:
        str: A 3-bullet point summary, or an error/empty message.
    """
    job_id = job_dict.get("job_id")
    title = job_dict.get("title", "N/A")
    company = job_dict.get("company", "N/A")
    description = job_dict.get("description", "").strip()
    
    if not job_id:
        logger.warning("Missing job_id in job dict. Cannot check cache or save summary.")
        return "No job ID provided"
        
    if not description:
        return "No description available"
        
    # Check DB cache first
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Query if jd_summary column exists and has content
        cursor.execute("SELECT jd_summary FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if row and row["jd_summary"]:
            cached_summary = row["jd_summary"].strip()
            if cached_summary:
                logger.info(f"Using cached summary for job: {job_id} ({company} - {title})")
                return cached_summary
    except Exception as e:
        logger.warning(f"Error checking cached summary in DB: {e}")
    finally:
        conn.close()
        
    # If not cached, call LLM
    logger.info(f"Generating summary for job: {job_id} ({company} - {title})")
    
    prompt = (
        "Summarize this job description in exactly 3 bullet points.\n"
        "Focus on: what they want, key skills needed, and what you will do day to day.\n\n"
        f"Job Title: {title}\n"
        f"Company: {company}\n"
        f"Description:\n{description}\n\n"
        "Return only the 3 bullet points, nothing else."
    )
    
    summary = call_llm(prompt, max_tokens=300)
    
    if not summary:
        logger.error(f"Failed to generate summary for job: {job_id}")
        return "Failed to generate summary"
        
    summary = summary.strip()
    
    # Save to database cache
    try:
        save_jd_summary(job_id, summary)
    except Exception as e:
        logger.error(f"Failed to cache summary for job {job_id} to DB: {e}")
        
    return summary
