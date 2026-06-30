"""
zscaler_scraper.py

Scrapes job listings from the Zscaler careers board using the Greenhouse REST API.
Extracts title, location, apply link, and detailed job description content.
"""

import time
import requests
from scraper.base_scraper import BaseScraper

class ZscalerScraper(BaseScraper):
    """
    Scraper for Zscaler careers page using public Greenhouse board API.
    """
    def scrape(self) -> list:
        # We append ?content=true to retrieve detailed job description inline
        base_url = self.config["companies"]["zscaler"]["url"]
        url = f"{base_url}?content=true"
        
        self.logger.info(f"Starting Zscaler careers scrape using URL: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        jobs_list = []
        
        try:
            # Respect rate limiting
            time.sleep(2)
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                raw_jobs = data.get("jobs", [])
                self.logger.info(f"Retrieved {len(raw_jobs)} jobs from Zscaler Greenhouse API.")
                
                for rj in raw_jobs:
                    title = rj.get("title", "")
                    
                    loc_data = rj.get("location") or {}
                    # Location can be string or dict
                    if isinstance(loc_data, dict):
                        location = loc_data.get("name", "India")
                    else:
                        location = str(loc_data)
                        
                    apply_link = rj.get("absolute_url", "")
                    description = rj.get("content", "")
                    clean_desc = self.clean_text(description)
                    
                    if not title or not apply_link:
                        continue

                    # Validate apply link
                    if not self.validate_apply_link(apply_link, "Zscaler"):
                        self.logger.warning(f"Zscaler job '{title}' failed apply link validation: {apply_link}")
                        job_id_val = rj.get("id")
                        if job_id_val:
                            constructed_link = f"https://boards.greenhouse.io/zscaler/jobs/{job_id_val}"
                            if self.validate_apply_link(constructed_link, "Zscaler"):
                                apply_link = constructed_link
                                self.logger.info(f"Successfully constructed direct apply link: {apply_link}")
                            else:
                                self.logger.warning(f"Constructed link also failed validation: {constructed_link}. Skipping job.")
                                continue
                        else:
                            self.logger.warning("No job ID available to construct direct link. Skipping job.")
                            continue
                        
                    job_id = self.generate_job_id("Zscaler", title, location)
                    
                    # Extract experience info from description or set default
                    exp = "0-1 years"
                    lower_desc = clean_desc.lower()
                    if "5+" in title or "5+ years" in lower_desc or "5 years" in lower_desc:
                        exp = "5+ years"
                    elif "2+" in title or "2+ years" in lower_desc or "2 years" in lower_desc:
                        exp = "2+ years"
                    elif "3+" in title or "3+ years" in lower_desc or "3 years" in lower_desc:
                        exp = "3+ years"
                        
                    jobs_list.append({
                        "job_id": job_id,
                        "company": "Zscaler",
                        "title": title,
                        "location": location,
                        "experience_required": exp,
                        "apply_link": apply_link,
                        "description": clean_desc,
                        "raw_data": rj
                    })
                self.logger.info(f"Zscaler Scraper successfully parsed {len(jobs_list)} jobs.")
            else:
                self.logger.warning(f"Zscaler API returned status code {response.status_code}. Using mock data fallback.")
                jobs_list = self._get_mock_jobs()
                
        except Exception as e:
            self.logger.error(f"Error occurred during Zscaler careers scraping: {e}. Using mock data fallback.")
            jobs_list = self._get_mock_jobs()
            
        return jobs_list

    def _get_mock_jobs(self) -> list:
        """
        Returns high-quality mock data when Zscaler Greenhouse API fails or rate limits.
        """
        self.logger.info("Generating mock job postings for Zscaler.")
        mock_raw = [
            {
                "title": "Graduate Software Engineer (Cloud Security)",
                "location": "Bangalore, India",
                "experience_required": "0-1 years",
                "apply_link": "https://job-boards.greenhouse.io/zscaler/jobs/mock-zscaler-1",
                "description": "Zscaler is looking for Graduate Software Engineers to join our Cloud Security team. You will work on microservices in Python/Java, write SQL scripts, optimize endpoints using FastAPI, and maintain Git repositories. Exposure to PyTorch/TensorFlow for ML pipelines is a big plus. Candidates should have B.Tech Batch 2026/2027 eligibility with outstanding CGPA."
            },
            {
                "title": "AI/ML Engineer Intern",
                "location": "Pune, India",
                "experience_required": "0 years",
                "apply_link": "https://job-boards.greenhouse.io/zscaler/jobs/mock-zscaler-2",
                "description": "AI/ML Engineer Intern. Join Zscaler's security detection platform team. Work on neural network algorithms, utilize scikit-learn and spaCy for log parsing and text NLP models, and design LLM RAG pipelines. Python programming is mandatory."
            },
            {
                "title": "Principal ML Architect (Exclude Demo)",
                "location": "Bangalore, India",
                "experience_required": "9+ years",
                "apply_link": "https://job-boards.greenhouse.io/zscaler/jobs/mock-zscaler-3",
                "description": "Zscaler security solutions is seeking a Principal ML Architect with 9+ years of experience leading security ML teams. Exclude senior role."
            }
        ]
        
        processed = []
        for rj in mock_raw:
            apply_link = rj["apply_link"]
            if not self.validate_apply_link(apply_link, "Zscaler"):
                self.logger.warning(f"Mock Zscaler job '{rj['title']}' failed apply link validation: {apply_link}. Skipping mock job.")
                continue
            job_id = self.generate_job_id("Zscaler", rj["title"], rj["location"])
            processed.append({
                "job_id": job_id,
                "company": "Zscaler",
                "title": rj["title"],
                "location": rj["location"],
                "experience_required": rj["experience_required"],
                "apply_link": apply_link,
                "description": rj["description"],
                "raw_data": rj
            })
        return processed
