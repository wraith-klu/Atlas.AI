# AI Job Search Agent — Phase 1 Engine

An intelligent multi-agent pipeline designed to automatically scrape daily job postings from major tech company career pages, filter them based on a personal profile (matching skills, location preferences, role keywords, and experience thresholds), and catalog new opportunities in a local SQLite database.

## System Architecture

```text
ai-job-agent/
├── config/
│   └── user_profile.yaml       # User profile details and target company settings
├── database/
│   └── db_manager.py           # SQLite CRUD operations and scraper run logging
├── scraper/
│   ├── base_scraper.py         # Abstract base class with common scraping helpers
│   ├── ibm_scraper.py          # IBM Careers Scraper (API)
│   ├── infosys_scraper.py      # Infosys Careers Scraper (BeautifulSoup parser)
│   ├── genpact_scraper.py      # Genpact Workday careers API Scraper (POST requests)
│   ├── delhivery_scraper.py    # Delhivery Lever ATS Scraper (HTML parser)
│   └── zscaler_scraper.py      # Zscaler Greenhouse ATS Scraper (API)
├── utils/
│   ├── config_loader.py        # YAML profile configurations loader
│   ├── filter_engine.py        # Regex and keyword filtering mechanics
│   └── logger.py               # Combined stdout console and daily log rotation
├── logs/                       # Auto-generated daily log files
├── tests/
│   └── test_scrapers.py        # Automated test suite
├── main.py                     # Entrypoint orchestrator
├── requirements.txt            # Package dependencies
└── README.md                   # Setup guide
```

---

## Setup Instructions

### 1. Clone & Set Up Directory

Navigate to the project root directory:

```bash
cd ai-job-agent
```

### 2. Install Dependencies

Install Python libraries specified in the requirements file:

```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers (For future browser automation expansions)

```bash
playwright install chromium
```

### 4. Configure Your Profile

Modify `config/user_profile.yaml` to specify your details, including:

- Personal details (name, cgpa, batch)
- Skills list
- Preferred roles & locations
- Max experience years allowed (e.g. 1 year for freshers)
- Inclusion and exclusion keywords

### 5. Run the Search Agent

**Option A — Double-click (easiest):**

```text
run.bat
```

**Option B — Command Prompt (cmd.exe):**

```cmd
set PYTHONPATH=.
python main.py
```

**Option C — PowerShell:**

```powershell
$env:PYTHONPATH = "."; python main.py
```

### 6. Run Tests

**Command Prompt (cmd.exe):**

```cmd
set PYTHONPATH=.
python -m unittest discover -s tests -p "test_*.py"
```

**PowerShell:**

```powershell
$env:PYTHONPATH = "."; python -m unittest discover -s tests -p "test_*.py"
```
