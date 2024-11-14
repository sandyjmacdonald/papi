import sys
import argparse
from papi.wrappers import NotionWrapper, TogglTrackWrapper
from papi import config, setup_logger
from papi.user import User
from papi.project import Project, check_project_id, user_id_from_project_id

def prompt_for_args():
    """Prompt the user for input interactively."""
    print("No command-line arguments provided. Enter the required information below:")
    print()
    
    user_id = input("Enter project PI three-letter ID (e.g., JAS): ").strip()
    if not user_id:
        user_name = input("Enter project PI name (e.g., John Andrew Smith): ").strip()
    else:
        user_name = None
    name = input("Enter project name (e.g., 'RNA-seq analysis'): ").strip()
    if not user_id and not user_name:
        project_id = input("Enter project ID (e.g., P2024-JAS-DEFG): ").strip()
        if check_project_id(project_id):
            user_id = user_id_from_project_id(project_id)
    else:
        project_id = None
    
    enable_logging_input = input("Enable logging? (y/n) [n]: ").strip().lower()
    enable_logging = enable_logging_input in ('y', 'yes')
    
    if enable_logging:
        log_level_choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        log_level = input(f"Set log level {log_level_choices} [INFO]: ").strip().upper()
        log_level = log_level if log_level else None
        if log_level is not None and log_level not in log_level_choices:
            print("Invalid log level. Defaulting to 'INFO'.")
            log_level = 'INFO'
        
        log_file = input("Path to log file (leave blank for none): ").strip()
        log_file = log_file if log_file else None
    else:
        log_level = None
        log_file = None
    
    enable_toggl_input = input("Create Toggl Track project? (y/n) [n]: ").strip().lower()
    enable_toggl = enable_toggl_input in ('y', 'yes')

    enable_notion_input = input("Create Notion project? (y/n) [n]: ").strip().lower()
    enable_notion = enable_notion_input in ('y', 'yes')
    
    # Create a Namespace object similar to argparse's
    return argparse.Namespace(
        user_id=user_id or None,
        user_name=user_name or None,
        name=name or None,
        project_id=project_id or None,
        enable_logging=enable_logging,
        log_level=log_level,
        log_file=log_file,
        enable_toggl=enable_toggl,
        enable_notion=enable_notion
    )

def main():
    """Main function of create-project script"""

    # Set up argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user_id", type=str, help="three-letter user (client) ID, e.g. JAS", required=False
    )
    parser.add_argument(
        "-v", "--user_name", type=str, help="user (client) name, e.g. John Andrew Smith", required=False
    )
    parser.add_argument(
        "-n", "--name", type=str, help="short project name, e.g. 'RNA-seq analysis', project ID will be auto-generated", required=False
    )
    parser.add_argument(
        "-p", "--project_id", type=str, help="full project ID, e.g. P2024-JAS-DEFG, if already generated", required=False
    )
    parser.add_argument(
        '--enable-toggl', action='store_true', help='create Toggl Track project'
    )
    parser.add_argument(
        '--enable-notion', action='store_true', help='create Notion project'
    )
    parser.add_argument(
        '--enable-logging', action='store_true', help='enable logging output for the papi library'
    )
    parser.add_argument(
        '--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='set the logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file', type=str, help='path to a file where logs should be written'
    )
    args = parser.parse_args()

    # Check if any arguments were provided
    if len(sys.argv) == 1:
        args = prompt_for_args()
    else:
        args = parser.parse_args()

    logger = setup_logger(args.enable_logging, args.log_level, args.log_file)

    user_id = args.user_id
    user_name = args.user_name
    project_name = args.name
    project_id = args.project_id
    enable_toggl = args.enable_toggl
    enable_notion = args.enable_notion

    if user_id and not user_name:
        user = User(user_id=user_id)
    elif user_name and not user_id:
        user = User(user_name)
    elif user_id and user_name:
        user = User(user_name, user_id=user_id)
    else:
        logger.warning("Please provide either a three-letter user ID and/or user name")
        return

    if project_id and not project_name:
        project = Project(id=project_id)
    elif project_name and not project_id:
        project = Project(name=project_name, user_id=user.user_id)
    elif project_id and project_name:
        project = Project(name=project_name, id=project_id)
    else:
        logger.warning("Please provide either a valid project ID and/or project name")
        return

    if enable_toggl:
        # Set up Toggl Track API wrapper
        #
        # NOTE: you must have added Toggl Track API key and password, with
        # variable names below to .env file in this directory
        if "TOGGL_TRACK_API_KEY" not in config and "TOGGL_TRACK_PASSWORD" not in config:
            logger.warning("Please create a .env file with TOGGL_TRACK_API_KEY and TOGGL_TRACK_PASSWORD set!")
            return
        toggl_api_key = config["TOGGL_TRACK_API_KEY"]
        toggl_api_password = config["TOGGL_TRACK_PASSWORD"]
        toggl = TogglTrackWrapper(toggl_api_key, toggl_api_password)

        # Tell wrapper which workspace to set as default
        toggl_workspace = config["TOGGL_TRACK_WORKSPACE"]
        toggl.set_default_workspace(toggl_workspace)

        # Create project on Toggl Track
        toggl_proj_id = toggl.create_project(project, toggl.default_workspace_id)

    if enable_notion:
        # Set up Notion API wrapper
        #
        # NOTE: you must have added your Notion API credentials and user and projects
        # database IDs with variable names below to .env file in this directory
        if "NOTION_API_SECRET"not in config and "NOTION_CLIENTS_DB" not in config and "NOTION_PROJECTS_DB" not in config:
            logger.warning("Please create a .env file with NOTION_API_SECRET and NOTION_CLIENTS_DB and NOTION_PROJECTS_DB set!")
            return  
        notion_api_secret = config["NOTION_API_SECRET"]
        notion_clients_db = config["NOTION_CLIENTS_DB"]
        notion_projects_db = config["NOTION_PROJECTS_DB"]
        notion = NotionWrapper(notion_api_secret)

        # Create project on Notion
        user_page_id = notion.get_user_page_id(notion_clients_db, user)
        if user_page_id is not None:
            notion_proj_id = notion.create_project(project, user, notion_projects_db, user_page_id=user_page_id)
        else:
            notion_proj_id = notion.create_project(project, user, notion_projects_db)

if __name__ == "__main__":
    main()