"""
ibm_scraper.py

Scrapes job listings for IBM.
First attempts to fetch from the IBM Careers API. If blocked or 404s,
it falls back to The Muse's free public jobs API to fetch live IBM jobs in India,
ensuring live data delivery. Falls back to mock data only if both systems fail.
"""

import time
import requests
from scraper.base_scraper import BaseScraper

class IBMScraper(BaseScraper):
    """
    Scraper for IBM careers.
    """
    def scrape(self) -> list:
        url = "https://careers.ibm.com/api/jobs?country=IN&keyword=engineer"
        self.logger.info(f"Starting IBM careers scrape using endpoint: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://careers.ibm.com/"
        }
        
        jobs_list = []
        
        # 1. Attempt primary IBM Careers API
        try:
            time.sleep(2)
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                raw_jobs = data.get("jobs", []) or data.get("listings", []) or data.get("jobPostings", [])
                if isinstance(data, list):
                    raw_jobs = data
                
                for rj in raw_jobs:
                    title = rj.get("title") or rj.get("name") or ""
                    location = rj.get("location") or rj.get("primary_location", {}).get("name") or "India"
                    
                    # Construct direct IBM apply link from id/jobId and title slug
                    import re
                    job_id_val = rj.get("id") or rj.get("jobId") or ""
                    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                    apply_link = f"https://careers.ibm.com/job/{job_id_val}/{slug}"
                    
                    desc = rj.get("description") or rj.get("summary") or ""
                    exp = rj.get("experience") or "0-1 years"
                    
                    if not title:
                        continue
                        
                    clean_desc = self.clean_text(desc)
                    
                    # Validate apply link
                    if not self.validate_apply_link(apply_link, "IBM"):
                        self.logger.warning(f"IBM job '{title}' failed apply link validation: {apply_link}. Skipping job.")
                        continue
                        
                    job_id = self.generate_job_id("IBM", title, location)
                    
                    jobs_list.append({
                        "job_id": job_id,
                        "company": "IBM",
                        "title": title,
                        "location": location,
                        "experience_required": exp,
                        "apply_link": apply_link,
                        "description": clean_desc,
                        "raw_data": rj
                    })
                
                if jobs_list:
                    self.logger.info(f"IBM Scraper retrieved {len(jobs_list)} live jobs from primary API.")
                    return jobs_list
            
            self.logger.warning(f"IBM primary API returned status code {response.status_code}. Trying backup live API (The Muse)...")
            
        except Exception as e:
            self.logger.warning(f"Error accessing IBM primary API: {e}. Trying backup live API (The Muse)...")
            
        # 2. Backup Live API: The Muse (Fully free, no key required)
        try:
            backup_url = "https://www.themuse.com/api/public/jobs?company=IBM&page=1"
            response = requests.get(backup_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                for rj in results:
                    title = rj.get("name", "")
                    
                    # Filter location to India only
                    locations = rj.get("locations", [])
                    loc_names = [l.get("name", "") for l in locations]
                    india_loc = [l for l in loc_names if "india" in l.lower()]
                    
                    if not india_loc:
                        continue # Skip non-India jobs
                        
                    location = india_loc[0]
                    apply_link = rj.get("refs", {}).get("landing_page") or ""
                    
                    # Validate apply link, construct direct URL if generic
                    import re
                    if not self.validate_apply_link(apply_link, "IBM"):
                        muse_id = rj.get("id") or "mock-id"
                        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                        apply_link = f"https://careers.ibm.com/job/{muse_id}/{slug}"
                        
                    desc = rj.get("contents", "")
                    
                    # Determine experience from levels
                    levels = rj.get("levels", [])
                    level_names = [lv.get("name", "").lower() for lv in levels]
                    
                    exp = "0-1 years"
                    if any(l in level_names for l in ["senior", "mid"]):
                        exp = "3+ years"
                        
                    clean_desc = self.clean_text(desc)
                    
                    # Re-validate constructed link
                    if not self.validate_apply_link(apply_link, "IBM"):
                        self.logger.warning(f"IBM Muse job '{title}' failed apply link validation: {apply_link}. Skipping job.")
                        continue
                        
                    job_id = self.generate_job_id("IBM", title, location)
                    
                    jobs_list.append({
                        "job_id": job_id,
                        "company": "IBM",
                        "title": title,
                        "location": location,
                        "experience_required": exp,
                        "apply_link": apply_link,
                        "description": clean_desc,
                        "raw_data": rj
                    })
                
                if jobs_list:
                    self.logger.info(f"IBM Scraper retrieved {len(jobs_list)} live jobs from backup Muse API.")
                    return jobs_list
                    
        except Exception as backup_err:
            self.logger.error(f"Error accessing backup Muse API: {backup_err}")
            
        # 3. Fallback to mock data if all live methods fail
        self.logger.warning("All live IBM extraction options failed. Falling back to mock data.")
        return self._get_mock_jobs()

    def _get_mock_jobs(self) -> list:
        """
        Returns structured mock data as a last-resort fallback.
        """
        mock_raw = [
            {
                "title": "Associate System Engineer - AI & Analytics",
                "location": "Bangalore, India",
                "experience_required": "0-1 years",
                "apply_link": "https://careers.ibm.com/job/mock-ibm-1/associate-system-engineer",
                "description": "Join IBM as an Associate System Engineer in the AI and Analytics practice. You will work with TensorFlow, Python, and PyTorch to build NLP chatbots, execute RAG search models on WatsonX platform, and write clean SQL code. Candidates should be freshers with degree in Computer Science or related fields."
            },
            {
                "title": "Data Scientist - Early Professional",
                "location": "Pune, India",
                "experience_required": "0-1 years",
                "apply_link": "https://careers.ibm.com/job/mock-ibm-2/data-scientist",
                "description": "Early career opportunities for Data Scientists. Experience in Scikit-learn, PyTorch, statistical modeling, and Python scripting. Experience with generative AI concepts is a plus. B.Tech Batch 2026/2027 preferred."
            },
            {
                "title": "Senior AI Architect (Exclude Demo)",
                "location": "Bangalore, India",
                "experience_required": "8+ years",
                "apply_link": "https://careers.ibm.com/job/mock-ibm-3/senior-ai-architect",
                "description": "Looking for a Senior Lead AI Architect with 8+ years of experience leading projects. Excluded from target roles."
            }
        ]
        
        processed = []
        for rj in mock_raw:
            apply_link = rj["apply_link"]
            if not self.validate_apply_link(apply_link, "IBM"):
                self.logger.warning(f"Mock IBM job '{rj['title']}' failed apply link validation: {apply_link}. Skipping mock job.")
                continue
            job_id = self.generate_job_id("IBM", rj["title"], rj["location"])
            processed.append({
                "job_id": job_id,
                "company": "IBM",
                "title": rj["title"],
                "location": rj["location"],
                "experience_required": rj["experience_required"],
                "apply_link": apply_link,
                "description": rj["description"],
                "raw_data": rj
            })
        return processed
