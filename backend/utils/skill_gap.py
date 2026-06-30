"""
skill_gap.py

Analyzes missing skills across scored jobs and generates gap reports
with recommended free learning resources.
"""

import json
from collections import Counter
from database.db_manager import get_connection
from utils.logger import get_logger

logger = get_logger("SkillGapAnalyzer")

# Dictionary mapping common technical skills to free learning resources
FREE_RESOURCES = {
    "Docker": "play-with-docker.com",
    "Kubernetes": "kubernetes.io/docs/tutorials",
    "Spark": "spark.apache.org/docs/latest",
    "Hadoop": "hadoop.apache.org",
    "AWS": "aws.amazon.com/free",
    "Azure": "learn.microsoft.com",
    "GCP": "cloud.google.com/free",
    "FastAPI": "fastapi.tiangolo.com",
    "React.js": "react.dev",
    "React": "react.dev",
    "Django": "djangoproject.com",
    "Flask": "flask.palletsprojects.com",
    "Git": "git-scm.com/doc",
    "Python": "python.org/about/gettingstarted",
    "TensorFlow": "tensorflow.org/tutorials",
    "PyTorch": "pytorch.org/tutorials",
    "NLP": "huggingface.co/learn/nlp-course",
    "LLMs": "huggingface.co/learn",
    "RAG": "huggingface.co/learn",
    "Prompt Engineering": "learnprompting.org",
    "SQL": "w3schools.com/sql",
    "NoSQL": "mongodb.com/basics",
    "MongoDB": "learn.mongodb.com",
    "Redis": "redis.io/documentation",
    "CI/CD": "about.gitlab.com/stages-devops-lifecycle/continuous-integration",
    "Jenkins": "jenkins.io/doc",
    "Linux": "linuxjourney.com",
    "Docker/Kubernetes": "kubernetes.io/docs",
    "TypeScript": "typescriptlang.org/docs",
    "Node.js": "nodejs.org/en/docs",
    "Scala": "docs.scala-lang.org",
    "Go": "go.dev/doc",
    "C++": "learncpp.com",
    "REST APIs": "restfulapi.net"
}

def analyze_skill_gaps(all_jobs_with_scores: list) -> list:
    """
    Collects all missing skills across the list of scored jobs,
    counts their frequency, and returns the top 5 most-needed missing skills.
    
    Each item in the returned list is a dict:
    {
      "skill": "Docker",
      "count": 8,
      "resource": "play-with-docker.com"
    }
    """
    skill_counter = Counter()
    
    for job in all_jobs_with_scores:
        missing = job.get("missing_skills")
        if not missing:
            continue
            
        # Handle if it is stored as a JSON string in SQLite
        if isinstance(missing, str):
            try:
                missing_list = json.loads(missing)
            except Exception:
                # Fallback to comma-separated list if not valid JSON
                missing_list = [s.strip() for s in missing.split(",") if s.strip()]
        elif isinstance(missing, list):
            missing_list = missing
        else:
            missing_list = []
            
        for skill in missing_list:
            if not skill:
                continue
            # Normalize casing slightly to group identical skills, but try to preserve title casing
            cleaned_skill = skill.strip()
            # Standardize common variations
            lower_skill = cleaned_skill.lower()
            if lower_skill == "docker":
                cleaned_skill = "Docker"
            elif lower_skill == "kubernetes" or lower_skill == "k8s":
                cleaned_skill = "Kubernetes"
            elif lower_skill == "aws":
                cleaned_skill = "AWS"
            elif lower_skill == "spark":
                cleaned_skill = "Spark"
            elif lower_skill == "git":
                cleaned_skill = "Git"
                
            skill_counter[cleaned_skill] += 1
            
    # Get top 5 skills
    top_5 = skill_counter.most_common(5)
    
    results = []
    for skill, count in top_5:
        # Find a free learning resource or construct a fallback search link
        resource = FREE_RESOURCES.get(skill)
        if not resource:
            # Let's map search resource as fallback
            resource = f"google.com/search?q=free+course+to+learn+{skill.replace(' ', '+')}"
            
        results.append({
            "skill": skill,
            "count": count,
            "resource": resource
        })
        
    return results

def generate_gap_report() -> str:
    """
    Reads all scored jobs from DB, aggregates missing skills,
    and returns a formatted string report.
    """
    conn = get_connection()
    jobs = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT missing_skills FROM jobs WHERE match_score > 0")
        rows = cursor.fetchall()
        jobs = [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error reading scored jobs from DB for skill gap analysis: {e}")
    finally:
        conn.close()
        
    if not jobs:
        return "📊 SKILL GAP REPORT\nNo scored jobs found in database to analyze."
        
    top_gaps = analyze_skill_gaps(jobs)
    
    report_lines = [
        "📊 SKILL GAP REPORT",
        "Most needed skills you're missing:"
    ]
    
    if not top_gaps:
        report_lines.append("No missing skills identified across your jobs!")
    else:
        for idx, gap in enumerate(top_gaps, 1):
            report_lines.append(f"{idx}. {gap['skill']} (needed in {gap['count']} jobs) → Learn free: {gap['resource']}")
            
    return "\n".join(report_lines)
