"""
base_scraper.py

Abstract base class for all target company careers scrapers.
Provides common utilities for data sanitization, custom ID generation, and basic relevance checks.
"""

import re
import hashlib
from abc import ABC, abstractmethod
from utils.logger import get_logger

class BaseScraper(ABC):
    """
    Abstract base class for scrapers.
    Each company-specific scraper must subclass this and implement the `scrape()` method.
    """
    def __init__(self, config: dict):
        """
        Initializes the scraper with user configurations.
        
        Args:
            config (dict): The complete profile configuration loaded via config_loader.
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        
    @abstractmethod
    def scrape(self) -> list:
        """
        Performs the scraping operation for the company.
        
        Returns:
            list: A list of dicts, each conforming to:
                {
                    "job_id": str,
                    "company": str,
                    "title": str,
                    "location": str,
                    "experience_required": str,
                    "apply_link": str,
                    "description": str,
                    "date_found": str (YYYY-MM-DD),
                    "raw_data": dict/any
                }
        """
        pass

    def clean_text(self, text: str) -> str:
        """
        Strips whitespace, normalizes spaces, and cleans target HTML tags or symbols.
        """
        if not text:
            return ""
        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]*>', ' ', text)
        # Normalize whitespace (replace tabs, newlines, duplicate spaces with single space)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def generate_job_id(self, company: str, title: str, location: str) -> str:
        """
        Generates a unique, standardized Job ID based on the company, title, and location.
        Returns a slug followed by the first 6 characters of the MD5 hash.
        Example: "ibm_associate_software_engineer_bangalore_abc123"
        """
        # Lowercase and clean strings for the slug
        comp_slug = re.sub(r'[^a-z0-9]', '', company.lower())
        
        # Replace non-alphanumeric with underscores, merge multiple underscores, strip
        title_slug = re.sub(r'[^a-z0-9]', '_', title.lower())
        title_slug = re.sub(r'_+', '_', title_slug).strip('_')
        
        loc_slug = re.sub(r'[^a-z0-9]', '_', location.lower())
        loc_slug = re.sub(r'_+', '_', loc_slug).strip('_')
        
        # Generate MD5 hash for the combination to ensure uniqueness
        raw_str = f"{comp_slug}|{title_slug}|{loc_slug}".encode('utf-8')
        md5_hash = hashlib.md5(raw_str).hexdigest()
        hash_suffix = md5_hash[:6]
        
        return f"{comp_slug}_{title_slug}_{loc_slug}_{hash_suffix}"

    def is_relevant(self, job: dict) -> bool:
        """
        Basic keyword check against role_keywords_include and exclude_keywords.
        Can be used by scrapers to perform early stage relevance filters.
        
        Returns:
            bool: True if the job is relevant based on basic keyword filters, False otherwise.
        """
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        
        matching_conf = self.config.get("matching", {})
        includes = matching_conf.get("role_keywords_include", [])
        excludes = matching_conf.get("exclude_keywords", [])
        
        # 1. Exclude keywords check
        for ex in excludes:
            if ex.lower() in title:
                self.logger.debug(f"Job title '{job.get('title')}' excluded due to keyword: '{ex}'")
                return False
                
        # 2. Include keywords check
        if not includes:
            return True
            
        for inc in includes:
            if inc.lower() in title or inc.lower() in description:
                return True
                
        self.logger.debug(f"Job title '{job.get('title')}' does not match any role include keywords.")
        return False

    def validate_apply_link(self, link: str, company: str) -> bool:
        """Reject generic/homepage links — only accept direct job URLs."""
        generic_patterns = [
            "/careers$", "/careers/search", "/joblist$", 
            "/careers/?$", company.lower() + ".com/careers/?$"
        ]
        import re
        for pattern in generic_patterns:
            if re.search(pattern, link.lower()):
                return False  # reject — too generic
        # Direct links usually contain a job ID, number, or slug
        # We generalized the pattern to also match the other valid direct link examples provided (e.g. joblist/123, job-listings-, workday paths with digits)
        has_identifier = bool(re.search(r'(job|jobs)/[\w-]+\d', link.lower()))
        if not has_identifier:
            has_identifier = bool(re.search(r'(job|jobs|joblist|job-listings)/[\w/-]*\d|job-listings-[\w-]+\d', link.lower()))
        return has_identifier

