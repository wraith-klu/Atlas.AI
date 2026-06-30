"""
infosys_scraper.py

Scrapes job listings from the Infosys careers board using Playwright.
The site is an Angular SPA — plain HTTP requests only return the empty shell.
Playwright waits for the JS to render job cards before extracting data.
Falls back to structured mock data if rendering fails.
"""

import time
from scraper.base_scraper import BaseScraper


class InfosysScraper(BaseScraper):
    """
    Scraper for Infosys careers page (Angular SPA at career.infosys.com).
    Uses Playwright headless browser to render JavaScript content.
    """

    CAREERS_URL = "https://career.infosys.com/joblist"

    def scrape(self) -> list:
        self.logger.info("Starting Infosys careers scrape via Playwright (Angular SPA)...")
        jobs = []
        try:
            jobs = self._scrape_with_playwright()
            if jobs:
                self.logger.info(f"Infosys Playwright scrape returned {len(jobs)} live jobs.")
            else:
                self.logger.warning("Infosys Playwright returned 0 jobs — using mock data fallback.")
                jobs = self._get_mock_jobs()
        except Exception as e:
            self.logger.error(f"Infosys Playwright scrape failed: {e}. Using mock data fallback.")
            jobs = self._get_mock_jobs()
        return jobs

    # ──────────────────────────────────────────────────────────────
    def _scrape_with_playwright(self) -> list:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup

        jobs = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()

            self.logger.info(f"Navigating to: {self.CAREERS_URL}")
            page.goto(self.CAREERS_URL, wait_until="domcontentloaded", timeout=40000)

            # Give Angular time to bootstrap and fetch jobs from its backend
            page.wait_for_timeout(5000)

            # Try waiting for job card elements to appear
            job_card_selectors = [
                ".job-card",
                ".job-listing",
                ".opportunity-card",
                "[class*='job-card']",
                "[class*='jobCard']",
                "[class*='job-list'] > *",
                "app-job-card",
                "app-opportunity-card",
                ".mat-card",
            ]
            matched_selector = None
            for sel in job_card_selectors:
                try:
                    page.wait_for_selector(sel, timeout=5000)
                    matched_selector = sel
                    self.logger.info(f"Infosys: Matched selector '{sel}'")
                    break
                except Exception:
                    pass

            # Extra wait after selector found
            page.wait_for_timeout(2000)

            # Hand off rendered HTML to BeautifulSoup
            html = page.content()
            soup = BeautifulSoup(html, "lxml")

            # Try each card selector in BeautifulSoup
            cards = []
            if matched_selector:
                cards = soup.select(matched_selector)

            if not cards:
                # Generic fallback — scan for any element with job-like class names
                for sel in [".job-card", "[class*='job']", "[class*='opportunity']", ".mat-card"]:
                    cards = soup.select(sel)
                    if cards:
                        self.logger.info(f"Infosys BS4 fallback matched '{sel}': {len(cards)} items")
                        break

            self.logger.info(f"Infosys: Parsing {len(cards)} candidate elements from rendered HTML.")

            for card in cards:
                try:
                    # Extract title
                    title_el = (
                        card.find(class_=lambda c: c and "title" in c.lower())
                        or card.find(["h3", "h4", "h5", "a"])
                    )
                    title = self.clean_text(title_el.get_text()) if title_el else ""
                    if not title or len(title) < 4:
                        continue

                    # Extract apply link
                    link_el = card.find("a", href=True)
                    href = link_el["href"] if link_el else ""
                    if href and not href.startswith("http"):
                        href = f"https://career.infosys.com{href}"
                    apply_link = href or self.CAREERS_URL

                    # Extract location
                    loc_el = card.find(class_=lambda c: c and "location" in c.lower())
                    location = self.clean_text(loc_el.get_text()) if loc_el else "India"

                    # Extract description/summary
                    desc_el = card.find(class_=lambda c: c and (
                        "description" in c.lower() or "summary" in c.lower()
                    ))
                    description = self.clean_text(desc_el.get_text()) if desc_el else (
                        f"Infosys opening: {title}. Location: {location}."
                    )

                    # Extract experience if present
                    exp_el = card.find(class_=lambda c: c and "experience" in c.lower())
                    experience = self.clean_text(exp_el.get_text()) if exp_el else "0-1 years"

                    job_id = self.generate_job_id("Infosys", title, location)
                    # Validate apply link
                    if not self.validate_apply_link(apply_link, "Infosys"):
                        self.logger.warning(f"Infosys job '{title}' failed apply link validation: {apply_link}. Skipping job.")
                        continue

                    jobs.append({
                        "job_id": job_id,
                        "company": "Infosys",
                        "title": title,
                        "location": location,
                        "experience_required": experience,
                        "apply_link": apply_link,
                        "description": description,
                        "raw_data": {"source": "playwright_angular"},
                    })
                except Exception as card_err:
                    self.logger.debug(f"Infosys: Error parsing card: {card_err}")

            browser.close()
        return jobs

    # ──────────────────────────────────────────────────────────────
    def _get_mock_jobs(self) -> list:
        """Structured mock data used when live scraping is unavailable."""
        self.logger.info("Generating mock job postings for Infosys.")
        mock_raw = [
            {
                "title": "Systems Engineer Trainee (ML/NLP)",
                "location": "Bangalore, India",
                "experience_required": "0 years",
                "apply_link": "https://career.infosys.com/joblist/12345",
                "description": (
                    "Systems Engineer Trainee. Fresh graduates with strong knowledge in "
                    "Python, SQL, and NLP technologies. Familiarity with SpaCy, Scikit-learn, "
                    "and basic neural networks. Excellent analytical capabilities. Batch 2027 eligible."
                ),
            },
            {
                "title": "Associate ML Engineer",
                "location": "Gurugram, India",
                "experience_required": "0-1 years",
                "apply_link": "https://career.infosys.com/joblist/12346",
                "description": (
                    "Infosys AI and CogSci team hiring an Associate ML Engineer. Responsibilities: "
                    "Maintain training pipelines, integrate APIs with React frontend, write unit tests. "
                    "Skills: Python, TensorFlow, Git."
                ),
            },
            {
                "title": "Delivery Manager - AI Projects (Exclude Demo)",
                "location": "Bangalore, India",
                "experience_required": "10+ years",
                "apply_link": "https://career.infosys.com/joblist/12347",
                "description": "Project and Delivery Manager with 10+ years experience — excluded.",
            },
        ]
        processed = []
        for rj in mock_raw:
            apply_link = rj["apply_link"]
            if not self.validate_apply_link(apply_link, "Infosys"):
                self.logger.warning(f"Mock Infosys job '{rj['title']}' failed apply link validation: {apply_link}. Skipping mock job.")
                continue
            job_id = self.generate_job_id("Infosys", rj["title"], rj["location"])
            processed.append({
                "job_id": job_id,
                "company": "Infosys",
                "title": rj["title"],
                "location": rj["location"],
                "experience_required": rj["experience_required"],
                "apply_link": apply_link,
                "description": rj["description"],
                "raw_data": rj,
            })
        return processed
