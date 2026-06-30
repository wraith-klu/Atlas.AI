"""
match_engine.py

Matches candidate profile with job descriptions using OpenRouter LLM.
Provides a keyword-based fallback if the LLM calls fail.
"""

import json
from utils.openrouter_client import call_llm, parse_json_response
from utils.logger import get_logger
from database.db_manager import save_match_score

logger = get_logger("MatchEngine")

def run_keyword_fallback_match(job_dict: dict, user_profile: dict) -> dict:
    """
    Manual fallback scoring based on keyword overlap between candidate skills and JD.
    """
    logger.info("Running keyword-based fallback scoring...")
    title = job_dict.get("title", "").lower()
    description = job_dict.get("description", "").lower()
    
    candidate_skills = user_profile.get("preferences", {}).get("skills", [])
    
    matching_skills = []
    missing_skills = []
    
    # Simple check for skill presence in job description or title
    for skill in candidate_skills:
        skill_lower = skill.lower()
        # Word boundary or simple inclusion
        if f" {skill_lower} " in f" {description} " or f" {skill_lower} " in f" {title} " or description.startswith(skill_lower):
            matching_skills.append(skill)
        else:
            # We don't want to list ALL candidate skills as missing in JD unless they are mentioned.
            # Wait, in the prompt, missing_skills means: "skills in JD not in candidate profile".
            # For fallback, we don't know all JD skills, so we can check for common tools.
            pass
            
    # Estimate missing skills from common industry terms in JD that candidate doesn't have
    common_tools = [
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Jenkins", "CI/CD", 
        "Linux", "Spark", "Hadoop", "Scala", "Go", "C++", "TypeScript", 
        "Angular", "Vue", "Node.js", "Django", "Flask", "SQLAlchemy", "NoSQL", 
        "MongoDB", "Redis", "Elasticsearch"
    ]
    
    for tool in common_tools:
        if tool not in candidate_skills:
            if f" {tool.lower()} " in f" {description} ":
                missing_skills.append(tool)
                
    # Calculate score: percentage of matching candidate skills out of matches + missing
    total_relevant = len(matching_skills) + len(missing_skills)
    if total_relevant > 0:
        score = int((len(matching_skills) / total_relevant) * 100)
    else:
        # Default fallback score
        score = 50
        
    # Enforce range limits
    score = max(0, min(100, score))
    
    # Recommendation logic
    if score >= 70:
        recommendation = "APPLY"
    elif score >= 50:
        recommendation = "STRETCH"
    else:
        recommendation = "SKIP"
        
    return {
        "match_score": score,
        "match_reason": f"Fallback calculation: matched {len(matching_skills)} skills.",
        "missing_skills": missing_skills[:5],
        "matching_skills": matching_skills,
        "recommendation": recommendation,
        "quick_tip": "Review the required skills in the job description to align your resume."
    }

def match_job_to_profile(job_dict: dict, user_profile: dict) -> dict:
    """
    Scores how well the candidate matches the job posting using LLM.
    Falls back to manual keyword matching if LLM fails.
    
    Args:
        job_dict (dict): Details of the job.
        user_profile (dict): User profile config details.
        
    Returns:
        dict: Evaluated match result containing all 6 fields.
    """
    job_id = job_dict.get("job_id")
    company = job_dict.get("company", "N/A")
    title = job_dict.get("title", "N/A")
    location = job_dict.get("location", "N/A")
    experience_required = job_dict.get("experience_required", "N/A")
    description = job_dict.get("description", "")
    
    user_data = user_profile.get("user", {})
    preferences = user_profile.get("preferences", {})
    
    skills_list = ", ".join(preferences.get("skills", []))
    cgpa = user_data.get("cgpa", "9.61")
    degree = user_data.get("degree", "B.Tech CSE")
    
    # Construct LLM prompt
    prompt = f"""You are a technical recruiter AI. Score how well this candidate matches this job posting.

CANDIDATE PROFILE:
- Skills: {skills_list}
- Experience: Fresher (0 years), 2027 batch
- Degree: {degree}
- CGPA: {cgpa}
- Projects: ToxiGuard AI (NLP toxicity detection, 90%+ accuracy), Rigel AI (Code smell detection using AST + ML + LLM)
- Internship: AWS Academy AI/ML Intern (Apr-Jun 2025)

JOB POSTING:
- Company: {company}
- Title: {title}
- Location: {location}
- Experience Required: {experience_required}
- Description: {description}

Respond ONLY in this exact JSON format, nothing else:
{{
  "match_score": 85,
  "match_reason": "Strong NLP skills match JD requirements",
  "missing_skills": ["Docker", "Kubernetes"],
  "matching_skills": ["Python", "PyTorch", "NLP"],
  "recommendation": "APPLY",
  "quick_tip": "Highlight ToxiGuard AI project in resume"
}}

Scoring rules:
1. match_score: 0-100 integer. Be realistic: since candidate is a fresher, do not give 90+ unless it's a perfect match for a junior/fresher role. Deduct score if the job demands more years of experience (e.g. 3+ years), or skills the candidate lacks.
2. recommendation: 
   - APPLY if score >= 70
   - STRETCH if score 50-69 (good to try)
   - SKIP if score < 50
3. missing_skills: list of specific technical skills or tools mentioned in the JD that are not in the candidate's profile.
4. matching_skills: list of technical skills present in both the JD and the candidate's profile.
5. quick_tip: one actionable tip to improve the candidate's application or resume for this specific role.
"""
    
    # Try calling the LLM
    try:
        response_text = call_llm(prompt, max_tokens=400)
        result = parse_json_response(response_text)
        
        # Verify the structure has all 6 keys
        required_keys = ["match_score", "match_reason", "missing_skills", "matching_skills", "recommendation", "quick_tip"]
        if result and all(k in result for k in required_keys):
            # Normalize fields
            try:
                result["match_score"] = int(result["match_score"])
            except (ValueError, TypeError):
                result["match_score"] = 50
                
            # Double check recommendation logic consistency
            score = result["match_score"]
            if score >= 70:
                result["recommendation"] = "APPLY"
            elif score >= 50:
                result["recommendation"] = "STRETCH"
            else:
                result["recommendation"] = "SKIP"
                
            # Log successful evaluation
            logger.info(f"AI matched job {job_id} ({company} - {title}) with score {score}%")
            return result
        else:
            logger.warning(f"LLM returned invalid/incomplete JSON for job {job_id}. Retrying with a simpler prompt...")
            simpler_prompt = f"""You are a recruiter bot. Grade this job match:
Candidate: B.Tech CSE (9.61 CGPA, Fresher, skills: {skills_list})
Job: {company} - {title} ({experience_required} experience)
Provide a JSON block with exactly these keys:
{{
  "match_score": 75,
  "match_reason": "simple reasoning",
  "missing_skills": [],
  "matching_skills": [],
  "recommendation": "APPLY",
  "quick_tip": "None"
}}
JSON:"""
            response_text = call_llm(simpler_prompt, max_tokens=200)
            result = parse_json_response(response_text)
            if result and all(k in result for k in required_keys):
                try:
                    result["match_score"] = int(result["match_score"])
                except (ValueError, TypeError):
                    result["match_score"] = 50
                score = result["match_score"]
                if score >= 70:
                    result["recommendation"] = "APPLY"
                elif score >= 50:
                    result["recommendation"] = "STRETCH"
                else:
                    result["recommendation"] = "SKIP"
                logger.info(f"AI matched job {job_id} ({company} - {title}) with score {score}% on retry.")
                return result
            else:
                logger.warning(f"LLM retry prompt failed to return valid JSON for job {job_id}. Falling back...")
    except Exception as e:
        logger.error(f"Error during LLM matching for job {job_id}: {e}")
        
    # Keyword fallback
    fallback_result = run_keyword_fallback_match(job_dict, user_profile)
    return fallback_result
