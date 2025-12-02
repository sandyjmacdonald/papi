import os
import logging
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def load_config():
    config_path = os.environ.get("PAPI_CONFIG_FILE")
    if config_path:
        path = Path(config_path).expanduser()
    else:
        path = Path.home() / ".config" / "papi" / "config.toml"

    if not path.exists():
        raise RuntimeError(f"Config file not found: {path}")

    with path.open("rb") as f:
        raw = tomllib.load(f)

    config = {}

    toggl = raw.get("toggl", {})
    notion = raw.get("notion", {})

    mapping = {
        "TOGGL_TRACK_API_KEY": toggl.get("api_key"),
        "TOGGL_TRACK_PASSWORD": toggl.get("password"),
        "TOGGL_TRACK_WORKSPACE": toggl.get("workspace"),
        "NOTION_API_SECRET": notion.get("api_secret"),
        "NOTION_CLIENTS_DB": notion.get("clients_db"),
        "NOTION_PROJECTS_DB": notion.get("projects_db"),
        "NOTION_TASKS_DB": notion.get("tasks_db"),
        "NOTION_TEMPLATE_PAGE_ID": notion.get("template_page_id"),
        "NOTION_WORKORDERS_DB": notion.get("workorders_db"),
        "NOTION_TRAC_COSTS_DB": notion.get("trac_costs_db"),
    }

    for k, v in mapping.items():
        if v is not None:
            config[k] = v

    for key in mapping.keys():
        if key in os.environ:
            config[key] = os.environ[key]

    return config


config = load_config()

TOGGL_TRACK_API_KEY = config["TOGGL_TRACK_API_KEY"]
TOGGL_TRACK_PASSWORD = config["TOGGL_TRACK_PASSWORD"]
TOGGL_TRACK_WORKSPACE = config["TOGGL_TRACK_WORKSPACE"]
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
    "TOGGL_TRACK_WORKSPACE",
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
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()
        
        handler.setLevel(numeric_level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        if not logger.handlers:
            logger.addHandler(handler)
        
        logger.propagate = False
    else:
        logger.setLevel(logging.WARNING)
    
    return logger
