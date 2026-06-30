"""
logger.py

Configures dual-destination logging (console + daily rotating log files under the 'logs/' folder).
Also adds remote monitoring alerts to Supabase error_logs and emergency WhatsApp pipeline alerts.
"""

import os
import logging
import requests
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """
    Sets up and returns a configured logger instance.
    Logs to both console and logs/job_agent_YYYY-MM-DD.log.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it does not exist
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(root_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] — %(message)s"
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler named job_agent_YYYY-MM-DD.log
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file_name = f"job_agent_{today_str}.log"
    log_file_path = os.path.join(logs_dir, log_file_name)
    
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# ──────────────────────────────────────────────────────────────
# Centralized Error Monitoring & Notification Fallbacks
# ──────────────────────────────────────────────────────────────

def log_to_supabase(level: str, module: str, message: str):
    """
    Logs critical errors directly to the Supabase error_logs table.
    Uses dynamic imports to prevent circular logging imports.
    """
    try:
        import database.supabase_client as db
        if db.USE_CLOUD_DB:
            db.log_error_remote(level, module, message)
    except Exception as e:
        print(f"[Remote Log Failure] Could not write error log to Supabase: {e}")


def send_pipeline_failure_alert(error_detail: str):
    """
    Emergency alerts sent via WhatsApp directly to the user if the entire scraper
    pipeline crashes or fails.
    """
    to_number = os.getenv("ALERT_WHATSAPP_TO", "919792453534")
    token = os.getenv("WHATSAPP_API_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_ID", "")
    
    alert_text = (
        f"🚨 *CRITICAL ERROR: AI Job Search Agent pipeline has CRASHED!*\n\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST\n"
        f"🔍 Details: {error_detail[:200]}...\n\n"
        f"Please check your GitHub Action runs or database connectivity."
    )
    
    # 1. Try Meta Cloud API
    if token and phone_id and token != "your_meta_or_twilio_token":
        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": alert_text}
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code in (200, 201):
                return True
        except Exception:
            pass

    # 2. Try Twilio sandbox fallback
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_num = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    
    if sid and auth_token:
        try:
            from twilio.rest import Client
            client = Client(sid, auth_token)
            to_formatted = to_number if to_number.startswith("whatsapp:") else f"whatsapp:+{to_number}"
            client.messages.create(body=alert_text, from_=from_num, to=to_formatted)
            return True
        except Exception as e:
            print(f"[Alert Send Failure] Twilio alert failed: {e}")
            
    return False
