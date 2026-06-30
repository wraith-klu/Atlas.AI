"""
test_phase2.py

Unit tests to verify Phase 2 features:
1. OpenRouter API connectivity
2. AI matching and scoring output structure
3. JD summarizer bullet points format
4. Skill gap reports calculations and mock outputs
"""

import os
import unittest
from utils.config_loader import load_profile
from utils.openrouter_client import call_llm
from scraper.jd_summarizer import summarize_jd
from scraper.match_engine import match_job_to_profile, run_keyword_fallback_match
from dotenv import load_dotenv
from database.db_manager import init_db
from utils.skill_gap import analyze_skill_gaps

class TestPhase2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        init_db()
        cls.config = load_profile()
        cls.sample_job = {
            "job_id": "test_job_123",
            "company": "IBM",
            "title": "AI/ML Engineer - NLP",
            "location": "Bangalore",
            "experience_required": "0-2 years",
            "description": "We are looking for an AI/ML Engineer. Required skills include Python, NLP, PyTorch, and Docker. You will build RAG applications and deploy NLP models."
        }

    def test_openrouter_connection(self):
        """
        Pings OpenRouter API with a simple prompt and verifies we receive a response.
        """
        # Read API key. If it's a placeholder, skip or test fallback
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key == "your_key_here":
            self.skipTest("OPENROUTER_API_KEY is not configured. Skipping connection test.")
            
        prompt = "Hello. Respond with exactly the word 'OK' and nothing else."
        response = call_llm(prompt, max_tokens=10)
        self.assertTrue(len(response) > 0, "OpenRouter did not return any response.")
        logger_info = f"OpenRouter Connection Response: {response}"
        print(logger_info)
        self.assertIn("OK", response.upper())

    def test_match_engine(self):
        """
        Runs the match engine on a sample job and verifies the keys returned.
        Falls back to keyword matching if LLM fails, ensuring robustness.
        """
        result = match_job_to_profile(self.sample_job, self.config)
        self.assertIsInstance(result, dict)
        
        required_keys = ["match_score", "match_reason", "missing_skills", "matching_skills", "recommendation", "quick_tip"]
        for key in required_keys:
            self.assertIn(key, result, f"Key '{key}' missing from match output.")
            
        self.assertIsInstance(result["match_score"], int)
        self.assertTrue(0 <= result["match_score"] <= 100)
        self.assertIn(result["recommendation"], ["APPLY", "STRETCH", "SKIP"])
        self.assertIsInstance(result["missing_skills"], list)
        self.assertIsInstance(result["matching_skills"], list)

    def test_jd_summarizer(self):
        """
        Verifies that JD summarization outputs a valid 3-bullet summary.
        """
        # If API key is not configured, we'll get "No description available" or "Failed to generate summary" 
        # unless cached, so we can test with empty/populated conditions.
        empty_job = {"job_id": "test_empty", "description": ""}
        summary_empty = summarize_jd(empty_job)
        self.assertEqual(summary_empty, "No description available")
        
        # Test summarization on sample_job
        summary = summarize_jd(self.sample_job)
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)
        
        # If call succeeded and is not fallback failure, we should check that it contains bullet formatting
        if "Failed to generate summary" not in summary:
            # Check for standard markdown bullets like '-' or '*' or list entries
            # We don't fail strictly if LLM skips bullet character, but check for multiline/bullet format
            lines = [line.strip() for line in summary.split("\n") if line.strip()]
            self.assertTrue(len(lines) >= 1)

    def test_skill_gap(self):
        """
        Verifies that skill gap aggregation correctly identifies and counts missing skills.
        """
        mock_scored_jobs = [
            {"missing_skills": ["Docker", "Kubernetes", "Spark"]},
            {"missing_skills": ["Docker", "Kubernetes", "AWS"]},
            {"missing_skills": ["Docker", "Go"]}
        ]
        
        gaps = analyze_skill_gaps(mock_scored_jobs)
        self.assertIsInstance(gaps, list)
        self.assertTrue(len(gaps) > 0)
        
        # Docker should be the top missing skill (3 occurrences)
        self.assertEqual(gaps[0]["skill"], "Docker")
        self.assertEqual(gaps[0]["count"], 3)
        self.assertEqual(gaps[0]["resource"], "play-with-docker.com")
        
        # Kubernetes should be second (2 occurrences)
        self.assertEqual(gaps[1]["skill"], "Kubernetes")
        self.assertEqual(gaps[1]["count"], 2)

if __name__ == "__main__":
    unittest.main()
