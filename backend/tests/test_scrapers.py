"""
test_scrapers.py

Unit tests to verify individual scraper engines and filter mechanics.
"""

import unittest
from utils.config_loader import load_profile
from scraper.ibm_scraper import IBMScraper
from scraper.infosys_scraper import InfosysScraper
from scraper.genpact_scraper import GenpactScraper
from scraper.delhivery_scraper import DelhiveryScraper
from scraper.zscaler_scraper import ZscalerScraper
from utils.filter_engine import apply_all_filters

class TestJobScrapers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_profile()

    def test_ibm_scraper(self):
        """
        Tests that the IBM Scraper returns a list of formatted jobs.
        """
        scraper = IBMScraper(self.config)
        jobs = scraper.scrape()
        self.assertIsInstance(jobs, list)
        if jobs:
            job = jobs[0]
            self.assertEqual(job["company"], "IBM")
            self.assertIn("job_id", job)
            self.assertIn("title", job)
            self.assertIn("location", job)
            self.assertIn("experience_required", job)
            self.assertIn("apply_link", job)
            self.assertIn("description", job)

    def test_infosys_scraper(self):
        """
        Tests that the Infosys Scraper returns a list of formatted jobs.
        """
        scraper = InfosysScraper(self.config)
        jobs = scraper.scrape()
        self.assertIsInstance(jobs, list)
        if jobs:
            job = jobs[0]
            self.assertEqual(job["company"], "Infosys")
            self.assertIn("job_id", job)
            self.assertIn("title", job)

    def test_genpact_scraper(self):
        """
        Tests that the Genpact Scraper returns a list of formatted jobs.
        """
        scraper = GenpactScraper(self.config)
        jobs = scraper.scrape()
        self.assertIsInstance(jobs, list)
        if jobs:
            job = jobs[0]
            self.assertEqual(job["company"], "Genpact")
            self.assertIn("job_id", job)
            self.assertIn("title", job)

    def test_delhivery_scraper(self):
        """
        Tests that the Delhivery Scraper returns a list of formatted jobs.
        """
        scraper = DelhiveryScraper(self.config)
        jobs = scraper.scrape()
        self.assertIsInstance(jobs, list)
        if jobs:
            job = jobs[0]
            self.assertEqual(job["company"], "Delhivery")
            self.assertIn("job_id", job)
            self.assertIn("title", job)

    def test_zscaler_scraper(self):
        """
        Tests that the Zscaler Scraper returns a list of formatted jobs.
        """
        scraper = ZscalerScraper(self.config)
        jobs = scraper.scrape()
        self.assertIsInstance(jobs, list)
        if jobs:
            job = jobs[0]
            self.assertEqual(job["company"], "Zscaler")
            self.assertIn("job_id", job)
            self.assertIn("title", job)
            
    def test_filter_engine(self):
        """
        Tests that the filter engine successfully filters inclusion and exclusion keywords.
        """
        dummy_jobs = [
            {
                "title": "Senior Machine Learning Architect",
                "location": "Bangalore",
                "experience_required": "8 years",
                "description": "Experienced leader required."
            },
            {
                "title": "AI/ML Engineer Intern",
                "location": "Bangalore",
                "experience_required": "0 years",
                "description": "Python, TensorFlow, SpaCy NLP knowledge."
            },
            {
                "title": "Software Engineer",
                "location": "London", # Irrelevant location
                "experience_required": "0-1 years",
                "description": "Python developer role."
            }
        ]
        filtered = apply_all_filters(dummy_jobs, self.config)
        
        # Out of the 3, only AI/ML Engineer Intern matches Bangalore + ML + experience <= 1 + no Senior tag.
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["title"], "AI/ML Engineer Intern")

    def test_validate_apply_link(self):
        """
        Tests apply link validation logic on correct and wrong examples.
        """
        scraper = DelhiveryScraper(self.config)
        
        correct_examples = [
            ("https://boards.greenhouse.io/zscaler/jobs/6234567", "Zscaler"),
            ("https://career.infosys.com/joblist/12345", "Infosys"),
            ("https://genpact.wd108.myworkdayjobs.com/External_Careers/job/Pune/Software-Engineer_R-98765", "Genpact"),
            ("https://www.naukri.com/job-listings-software-engineer-delhivery-bangalore-191025901234", "Delhivery")
        ]
        
        wrong_examples = [
            ("https://www.zscaler.com/careers/search", "Zscaler"),
            ("https://career.infosys.com", "Infosys"),
            ("https://www.delhivery.com/careers", "Delhivery")
        ]
        
        for url, company in correct_examples:
            self.assertTrue(scraper.validate_apply_link(url, company), f"Should have accepted: {url}")
            
        for url, company in wrong_examples:
            self.assertFalse(scraper.validate_apply_link(url, company), f"Should have rejected: {url}")

if __name__ == "__main__":
    unittest.main()

