"""
main.py

The main orchestrator for the AI Job Search Agent.
Loads configuration, initializes the SQLite database, executes all enabled scrapers,
applies the filtering engine, commits new listings to the database, and prints
a formatted execution report.
"""

import sys
from utils.config_loader import load_profile
from utils.logger import get_logger
from utils.filter_engine import apply_all_filters
from database.db_manager import init_db, save_job, log_scrape, get_stats

# Import company scrapers
from scraper.ibm_scraper import IBMScraper
from scraper.infosys_scraper import InfosysScraper
from scraper.genpact_scraper import GenpactScraper
from scraper.delhivery_scraper import DelhiveryScraper
from scraper.zscaler_scraper import ZscalerScraper

logger = get_logger("MainOrchestrator")

def main():
    logger.info("Initializing AI Job Search Agent execution...")
    
    # 1. Load config profile
    try:
        config = load_profile()
        logger.info("User configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load user configuration: {e}")
        sys.exit(1)
        
    # 2. Initialize Database
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)
        
    # Scrapers mapping
    scraper_classes = {
        "ibm": ("IBM", IBMScraper),
        "infosys": ("Infosys", InfosysScraper),
        "genpact": ("Genpact", GenpactScraper),
        "delhivery": ("Delhivery", DelhiveryScraper),
        "zscaler": ("Zscaler", ZscalerScraper)
    }
    
    summary_data = []
    new_jobs_today = []
    
    # 3. Loop through scrapers
    for key, (display_name, ScraperClass) in scraper_classes.items():
        comp_config = config.get("companies", {}).get(key, {})
        if not comp_config.get("enabled", True):
            logger.info(f"Scraper for {display_name} is disabled. Skipping.")
            continue
            
        logger.info(f"Running scraper engine for {display_name}...")
        status = "SUCCESS"
        error_msg = None
        raw_count = 0
        filtered_count = 0
        new_saved_count = 0
        
        try:
            # Instantiate scraper with config
            scraper = ScraperClass(config)
            
            # a. Run scraper
            raw_jobs = scraper.scrape()
            raw_count = len(raw_jobs)
            
            # b. Apply filters
            filtered_jobs = apply_all_filters(raw_jobs, config)
            filtered_count = len(filtered_jobs)
            
            # c. Save new relevant jobs to DB
            for job in filtered_jobs:
                is_new = save_job(job)
                if is_new:
                    new_saved_count += 1
                    new_jobs_today.append(job)
                    
            logger.info(f"{display_name} execution: Raw={raw_count}, Filtered={filtered_count}, New Saved={new_saved_count}")
            
        except Exception as e:
            status = "FAILED"
            error_msg = str(e)
            logger.error(f"Error executing scraper for {display_name}: {e}")
            
        # d. Log scraping run details to DB
        log_scrape(display_name, status, raw_count, error_msg)
        
        summary_data.append({
            "company": display_name,
            "raw": raw_count,
            "filtered": filtered_count,
            "new": new_saved_count,
            "status": status
        })
        
    # 4. Print Summary Table
    print("\n" + "="*70)
    print("                      JOB SEARCH AGENT SUMMARY REPORT")
    print("="*70)
    print(f" {'Company':<15} | {'Jobs Found':<12} | {'After Filter':<13} | {'New Saved':<11} | {'Status':<8}")
    print("-"*70)
    
    total_raw = 0
    total_filtered = 0
    total_new = 0
    
    for row in summary_data:
        print(f" {row['company']:<15} | {row['raw']:<12} | {row['filtered']:<13} | {row['new']:<11} | {row['status']:<8}")
        total_raw += row["raw"]
        total_filtered += row["filtered"]
        total_new += row["new"]
        
    print("-"*70)
    print(f" {'Total':<15} | {total_raw:<12} | {total_filtered:<13} | {total_new:<11} |")
    print("="*70)
    
    # 5. Automatically run Phase 2 scoring if new jobs were found
    scored_count = 0
    apply_count = 0
    stretch_count = 0
    skip_count = 0
    if new_jobs_today:
        print("\n" + "="*70)
        print("🤖 Running Phase 2 matching and scoring engine...")
        print("="*70)
        try:
            from phase2_runner import run_phase2
            scored_count = run_phase2()

            # Tally recommendations for the summary
            from database.db_manager import get_jobs_by_recommendation
            apply_count = len(get_jobs_by_recommendation("APPLY"))
            stretch_count = len(get_jobs_by_recommendation("STRETCH"))
            skip_count = len(get_jobs_by_recommendation("SKIP"))
        except Exception as e:
            logger.error(f"Error running Phase 2 matching engine: {e}")

    # 6. Run Phase 3 — Notification Engine
    phase3_summary = {
        "jobs_eligible": 0,
        "whatsapp_sent": False, "jobs_marked": 0,
    }
    print("\n" + "="*70)
    print("💬 Running Phase 3 notification engine...")
    print("="*70)
    try:
        from phase3_runner import run_phase3
        phase3_summary = run_phase3(force=True)
    except Exception as e:
        logger.error(f"Error running Phase 3 notification engine: {e}")

    # 7. Print combined 3-phase output
    import time as _time
    elapsed = round(_time.time() - _start_time, 1) if '_start_time' in dir() else 0
    unique_companies = len(set(j.get('company', '').lower() for j in new_jobs_today))

    print("\n")
    print("🚀 AI JOB AGENT — FULL RUN COMPLETE")
    print("━" * 50)
    print(f"  🔍 Phase 1: {len(new_jobs_today)} new jobs found ({unique_companies or 5} companies scraped)")
    print(f"  🤖 Phase 2: {scored_count} jobs scored ({apply_count} APPLY, {stretch_count} STRETCH, {skip_count} SKIP)")
    alerted = phase3_summary.get("jobs_marked", 0)
    channel_str = "WhatsApp" if phase3_summary.get("whatsapp_sent") else "None (credentials not configured)"
    print(f"  📧 Phase 3: {alerted} jobs alerted via {channel_str}")
    print(f"  ⏱️  Total runtime: {elapsed}s")
    print("━" * 50)
    print()


if __name__ == "__main__":
    import time as _time
    _start_time = _time.time()
    main()
