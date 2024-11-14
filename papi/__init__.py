import os
import logging
from dotenv import dotenv_values

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
config = dotenv_values(dotenv_path)

ASANA_API_KEY = config["ASANA_API_KEY"]
ASANA_PASSWORD = config["ASANA_PASSWORD"]

TOGGL_TRACK_API_KEY = config["TOGGL_TRACK_API_KEY"]
TOGGL_TRACK_PASSWORD = config["TOGGL_TRACK_PASSWORD"]

NOTION_API_SECRET = config["NOTION_API_SECRET"]
NOTION_CLIENTS_DB = config["NOTION_CLIENTS_DB"]
NOTION_PROJECTS_DB = config["NOTION_PROJECTS_DB"]

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