"""
logger.py

Configures dual-destination logging (console + daily rotating log files under the 'logs/' folder).
"""

import os
import logging
from datetime import datetime

def get_logger(name: str) -> logging.Logger:
    """
    Sets up and returns a configured logger instance.
    Logs to both console and logs/job_agent_YYYY-MM-DD.log.
    
    Args:
        name (str): The name of the module/system setting up the logger.
        
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already configured
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it does not exist
    # Determine the directory relative to this script: project root is parent of 'utils'
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(root_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Format of logs: [TIMESTAMP] [LEVEL] [MODULE] — message
    # datefmt will output: 2026-06-28 10:57:00
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
