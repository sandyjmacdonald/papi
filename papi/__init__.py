import os
import logging
from dotenv import dotenv_values
from pathlib import Path

def load_config():
    user_env_path = Path.home() / ".config" / "papi" / ".env"
    config = {}

    if user_env_path.exists():
        config.update(dotenv_values(user_env_path))

    for key in (
        "TOGGL_TRACK_API_KEY",
        "TOGGL_TRACK_PASSWORD",
        "NOTION_API_SECRET",
        "NOTION_CLIENTS_DB",
        "NOTION_PROJECTS_DB",
        "NOTION_TASKS_DB",
        "NOTION_TEMPLATE_PAGE_ID",
        "NOTION_WORKORDERS_DB",
        "NOTION_TRAC_COSTS_DB",
    ):
        if key in os.environ:
            config[key] = os.environ[key]

    local_env_path = Path(__file__).parent / ".env"
    if local_env_path.exists():
        local_vals = dotenv_values(local_env_path)
        for k, v in local_vals.items():
            config.setdefault(k, v)

    return config

config = load_config()

TOGGL_TRACK_API_KEY = config["TOGGL_TRACK_API_KEY"]
TOGGL_TRACK_PASSWORD = config["TOGGL_TRACK_PASSWORD"]
NOTION_API_SECRET = config["NOTION_API_SECRET"]
NOTION_CLIENTS_DB = config["NOTION_CLIENTS_DB"]
NOTION_PROJECTS_DB = config["NOTION_PROJECTS_DB"]
NOTION_TASKS_DB = config["NOTION_TASKS_DB"]
NOTION_TEMPLATE_PAGE_ID = config["NOTION_TEMPLATE_PAGE_ID"]
NOTION_WORKORDERS_DB = config["NOTION_WORKORDERS_DB"]
NOTION_TRAC_COSTS_DB = config["NOTION_TRAC_COSTS_DB"]

required = [
    "TOGGL_TRACK_API_KEY",
    "TOGGL_TRACK_PASSWORD",
    "NOTION_API_SECRET",
    "NOTION_CLIENTS_DB",
    "NOTION_PROJECTS_DB",
    "NOTION_TASKS_DB",
    "NOTION_TEMPLATE_PAGE_ID",
    "NOTION_WORKORDERS_DB",
    "NOTION_TRAC_COSTS_DB",
]

missing = [k for k in required if k not in config]
if missing:
    raise RuntimeError(f"Missing required config values: {', '.join(missing)}")

def setup_logger(enable_logging: bool, log_level: str = 'INFO', log_file: str = None):
    logger = logging.getLogger('papi')
    
    if enable_logging:
        # Convert log_level string to logging level
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Create handler
        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        
        handler.setLevel(numeric_level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger if not already added
        if not logger.handlers:
            logger.addHandler(handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
    else:
        # Set a higher log level to suppress lower-level logs
        logger.setLevel(logging.WARNING)
    
    return logger
