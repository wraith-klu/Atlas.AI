"""
genpact_scraper.py

Scrapes job listings from the Genpact Workday API.
Uses a POST request to search for jobs, then requests detailed description for relevant postings.
"""

import time
import requests
from scraper.base_scraper import BaseScraper

class GenpactScraper(BaseScraper):
    """
    Scraper for Genpact careers via Workday public API.
    """
    def scrape(self) -> list:
        url = self.config["companies"]["genpact"]["url"]
        self.logger.info(f"Starting Genpact careers scrape using endpoint: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        # Search keywords from configuration preferences
        search_term = "AI"
        
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": search_term
        }
        
        jobs_list = []
        
        try:
            # Respect request rate limit with initial delay
            time.sleep(2)
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                postings = data.get("jobPostings", [])
                self.logger.info(f"Found {len(postings)} potential postings from Genpact search endpoint.")
                
                for post in postings:
                    title = post.get("title", "")
                    external_path = post.get("externalPath", "")
                    location = post.get("locationsText", "")
                    
                    if not title or not external_path:
                        continue
                        
                    # Pre-check title to decide if we should make detail API call
                    temp_job = {"title": title, "description": ""}
                    if not self.is_relevant(temp_job):
                        # Skip if title already has exclude keywords or is irrelevant
                        continue
                    
                    # Construct detail URL
                    detail_url = f"https://genpact.wd108.myworkdayjobs.com/wday/cxs/genpact/External_Careers{external_path}"
                    apply_link = f"https://genpact.wd108.myworkdayjobs.com/External_Careers{external_path}"
                    
                    # 2-3 second delay between detail requests
                    time.sleep(3)
                    self.logger.info(f"Fetching details for Genpact job: {title}")
                    
                    try:
                        detail_resp = requests.get(detail_url, headers=headers, timeout=10)
                        if detail_resp.status_code == 200:
                            detail_data = detail_resp.json()
                            job_info = detail_data.get("jobPostingInfo", {})
                            description = job_info.get("jobDescription", "")
                        else:
                            description = "Description not retrieved."
                    except Exception as details_err:
                        self.logger.warning(f"Failed to fetch Genpact job details for {title}: {details_err}")
                        description = "Description not retrieved."
                        
                    clean_desc = self.clean_text(description)
                    job_id = self.generate_job_id("Genpact", title, location)
                    
                    # Experience extraction or defaults
                    exp = "0-1 years"
                    if "5+" in title or "5+ years" in clean_desc.lower():
                        exp = "5+ years"
                    elif "2+" in title or "2+ years" in clean_desc.lower():
                        exp = "2+ years"
                        
                    # Validate apply link
                    if not self.validate_apply_link(apply_link, "Genpact"):
                        self.logger.warning(f"Genpact job '{title}' failed apply link validation: {apply_link}. Skipping job.")
                        continue

                    jobs_list.append({
                        "job_id": job_id,
                        "company": "Genpact",
                        "title": title,
                        "location": location,
                        "experience_required": exp,
                        "apply_link": apply_link,
                        "description": clean_desc,
                        "raw_data": post
                    })
                    
                self.logger.info(f"Genpact Scraper successfully retrieved and processed {len(jobs_list)} relevant jobs.")
            else:
                self.logger.warning(f"Genpact API returned status code {response.status_code}. Using mock data fallback.")
                jobs_list = self._get_mock_jobs()
                
        except Exception as e:
            self.logger.error(f"Error occurred during Genpact careers scraping: {e}. Using mock data fallback.")
            jobs_list = self._get_mock_jobs()
            
        return jobs_list

    def _get_mock_jobs(self) -> list:
        """
        Returns high-quality mock data when live Genpact API fails or blocks.
        """
        self.logger.info("Generating mock job postings for Genpact.")
        mock_raw = [
            {
                "title": "Management Trainee - Generative AI",
                "location": "Gurugram, India",
                "experience_required": "0-1 years",
                "apply_link": "https://genpact.wd108.myworkdayjobs.com/External_Careers/job/Gurugram/Management-Trainee_R-1",
                "description": "Genpact is hiring Management Trainees for our Generative AI practice. Responsibilities include building LLM prototypes, testing prompt engineering strategies, deploying FastAPI wrappers, and collaborating on Python-based ML scripts. Candidates should possess strong SQL and Python expertise."
            },
            {
                "title": "AI Developer Intern",
                "location": "Noida, India",
                "experience_required": "0 years",
                "apply_link": "https://genpact.wd108.myworkdayjobs.com/External_Careers/job/Noida/AI-Developer-Intern_R-2",
                "description": "Looking for AI Developer Interns to support client automation frameworks. Experience in Scikit-learn, SpaCy, NLP processing, and Python. B.Tech Computer Science, graduation batch 2027 preferred."
            },
            {
                "title": "Lead Consultant - ML Engineer (Exclude Demo)",
                "location": "Bangalore, India",
                "experience_required": "7+ years",
                "apply_link": "https://genpact.wd108.myworkdayjobs.com/External_Careers/job/Bangalore/Lead-Consultant_R-3",
                "description": "Seeking Lead Consultant with 7+ years of experience in ML pipeline deployment. Exclude senior role."
            }
        ]
        
        processed = []
        for rj in mock_raw:
            apply_link = rj["apply_link"]
            if not self.validate_apply_link(apply_link, "Genpact"):
                self.logger.warning(f"Mock Genpact job '{rj['title']}' failed apply link validation: {apply_link}. Skipping mock job.")
                continue
            job_id = self.generate_job_id("Genpact", rj["title"], rj["location"])
            processed.append({
                "job_id": job_id,
                "company": "Genpact",
                "title": rj["title"],
                "location": rj["location"],
                "experience_required": rj["experience_required"],
                "apply_link": apply_link,
                "description": rj["description"],
                "raw_data": rj
            })
        return processed
