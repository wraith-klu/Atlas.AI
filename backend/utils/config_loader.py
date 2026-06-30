"""
config_loader.py

Loads and parses user preferences, target companies, and job match keywords
from the YAML configuration file (`config/user_profile.yaml`).
"""

import os
import yaml

def get_project_root() -> str:
    """
    Returns the absolute path of the project's root folder.
    Assuming this file is located in <root>/utils/config_loader.py.
    """
    # Go up one level from 'utils' to get the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_profile(config_path: str = None) -> dict:
    """
    Loads and returns the user profile YAML config as a dictionary.
    
    Args:
        config_path (str, optional): Custom path to the yaml configuration.
                                     If None, loads from the default 'config/user_profile.yaml'.
    
    Returns:
        dict: Parsed configurations, or empty dict if errors occur.
    """
    if not config_path:
        root_dir = get_project_root()
        config_path = os.path.join(root_dir, "config", "user_profile.yaml")
        
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                return {}
            return data
    except yaml.YAMLError as e:
        print(f"Error parsing user_profile.yaml: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error loading profile configuration: {e}")
        raise
