"""
filter_engine.py

Filters job postings by role keywords, locations, experience level, and exclusion keywords.
Supports sequential execution of all filters to isolate highly relevant listings.
"""

import re
from utils.logger import get_logger

logger = get_logger("FilterEngine")

def filter_by_role(jobs: list, role_keywords: list) -> list:
    """
    Checks if the job title or description contains any of the role keywords (case-insensitive).
    Uses regex word boundaries for short keywords (length <= 3) to avoid substring matching.
    """
    if not role_keywords:
        return jobs
        
    filtered = []
    for job in jobs:
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        
        match = False
        for kw in role_keywords:
            kw_lower = kw.lower()
            if len(kw_lower) <= 3:
                # Compile a regex for exact word match
                pattern = re.compile(rf"\b{re.escape(kw_lower)}\b")
                if pattern.search(title) or pattern.search(desc):
                    match = True
                    break
            else:
                if kw_lower in title or kw_lower in desc:
                    match = True
                    break
                
        if match:
            filtered.append(job)
            
    logger.debug(f"filter_by_role: Reduced jobs from {len(jobs)} to {len(filtered)}.")
    return filtered

def filter_by_location(jobs: list, preferred_locations: list) -> list:
    """
    Checks if the job location matches any preferred location (case-insensitive substring check).
    """
    if not preferred_locations:
        return jobs
        
    filtered = []
    for job in jobs:
        location = job.get("location", "").lower()
        
        match = False
        for pref in preferred_locations:
            pref_lower = pref.lower()
            if pref_lower in location:
                match = True
                break
                
        if match:
            filtered.append(job)
            
    logger.debug(f"filter_by_location: Reduced jobs from {len(jobs)} to {len(filtered)}.")
    return filtered

def filter_by_experience(jobs: list, experience_max: int = 1) -> list:
    """
    Excludes jobs requiring experience strictly greater than experience_max.
    Jobs with unspecified experience are preserved to avoid false negatives.
    """
    filtered = []
    for job in jobs:
        exp_str = job.get("experience_required", "")
        if not exp_str:
            # Keep unspecified experience jobs
            filtered.append(job)
            continue
            
        exp_lower = exp_str.lower()
        
        # Check explicit keywords indicating entry-level
        if any(kw in exp_lower for kw in ["fresher", "intern", "0 years", "0-1", "0 - 1"]):
            filtered.append(job)
            continue
            
        # Parse numbers from the experience string
        numbers = [int(x) for x in re.findall(r'\d+', exp_lower)]
        if not numbers:
            # If no numbers found, default to keeping the job
            filtered.append(job)
            continue
            
        # Take the first number as the minimum required experience
        min_required = numbers[0]
        if min_required > experience_max:
            # E.g., "2+ years", "3 years" -> Exclude
            continue
            
        # Additionally, if there are indicators like "5+ years", "3+ years" in description,
        # but the title was generic, we verify that the first number in the range is within bounds.
        # If the range is "1-3 years", we check if the minimum is <= experience_max
        if min_required <= experience_max:
            filtered.append(job)
            
    logger.debug(f"filter_by_experience: Reduced jobs from {len(jobs)} to {len(filtered)}.")
    return filtered

def filter_exclude_keywords(jobs: list, exclude_keywords: list) -> list:
    """
    Removes jobs containing any exclusion keywords in their title (e.g. senior, lead, manager).
    """
    if not exclude_keywords:
        return jobs
        
    filtered = []
    for job in jobs:
        title = job.get("title", "").lower()
        
        exclude = False
        for kw in exclude_keywords:
            if kw.lower() in title:
                exclude = True
                break
                
        if not exclude:
            filtered.append(job)
            
    logger.debug(f"filter_exclude_keywords: Reduced jobs from {len(jobs)} to {len(filtered)}.")
    return filtered

def apply_all_filters(jobs: list, config: dict) -> list:
    """
    Runs all 4 filters in sequence:
    1. Filter out exclude keywords in title
    2. Filter in by preferred role keywords in title/desc
    3. Filter in by preferred locations
    4. Filter out high experience requirement jobs
    
    Returns the final filtered list of jobs.
    """
    logger.info(f"Applying filters to {len(jobs)} raw jobs.")
    
    matching_conf = config.get("matching", {})
    preferences = config.get("preferences", {})
    
    exclude_kws = matching_conf.get("exclude_keywords", [])
    role_kws = matching_conf.get("role_keywords_include", [])
    locations = preferences.get("locations", [])
    exp_max = preferences.get("experience_max", 1)
    
    # Run filters sequentially
    filtered_jobs = filter_exclude_keywords(jobs, exclude_kws)
    filtered_jobs = filter_by_role(filtered_jobs, role_kws)
    filtered_jobs = filter_by_location(filtered_jobs, locations)
    filtered_jobs = filter_by_experience(filtered_jobs, exp_max)
    
    logger.info(f"Filtering completed. Relevant jobs found: {len(filtered_jobs)} / {len(jobs)}")
    return filtered_jobs
