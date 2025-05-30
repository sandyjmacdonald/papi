import argparse
import pyperclip
from papi.wrappers import NotionWrapper
from papi import config, setup_logger
from papi.user import User
from papi.project import Project
from papi.task import Task

def main():
    """Main function of create-notion-project script"""

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
        "-p", "--project_id", type=str, help="full project ID, e.g. P2024-JAS-ABCD, if already generated", required=False
    )
    parser.add_argument(
        '--no-default-workorder-task', action='store_true', help='do not add default workorder task'
    )
    parser.add_argument(
        '--enable-logging', action='store_true', help='enable logging output for the papi library.'
    )
    parser.add_argument(
        '--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='set the logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file', type=str, help='path to a file where logs should be written'
    )
    args = parser.parse_args()

    logger = setup_logger(args.enable_logging, args.log_level, args.log_file)

    # Set up Notion API wrapper
    #
    # NOTE: you must have added your Notion API credentials and user and projects
    # database IDs with variable names below to .env file in this directory
    if (
        "NOTION_API_SECRET" not in config
        or "NOTION_CLIENTS_DB" not in config
        or "NOTION_PROJECTS_DB" not in config
        or "NOTION_TASKS_DB" not in config
        or "NOTION_TEMPLATE_PAGE_ID" not in config
    ):
        logger.warning(
            "Please create a .env file with NOTION_API_SECRET, NOTION_CLIENTS_DB, NOTION_PROJECTS_DB, NOTION_TASKS_DB, and NOTION_TEMPLATE_PAGE_ID set!"
        )
        return
    notion_api_secret = config["NOTION_API_SECRET"]
    notion_clients_db = config["NOTION_CLIENTS_DB"]
    notion_projects_db = config["NOTION_PROJECTS_DB"]
    notion_tasks_db = config["NOTION_TASKS_DB"]
    notion_template_page_id = config["NOTION_TEMPLATE_PAGE_ID"]
    notion = NotionWrapper(notion_api_secret)

    user_id = args.user_id
    user_name = args.user_name
    project_name = args.name
    project_id = args.project_id
    default_workorder_task = not args.no_default_workorder_task

    if project_id and not project_name:
        project = Project(id=project_id)
        user_id = project.user_id
        user = User(user_id=user_id)
    elif project_name and not project_id:
        if user_id and not user_name:
            user = User(user_id=user_id)
        elif user_name and not user_id:
            user = User(user_name)
        elif user_id and user_name:
            user = User(user_name, user_id=user_id)
        project = Project(name=project_name, user_id=user.user_id)
    elif project_id and project_name:
        project = Project(name=project_name, id=project_id)
        user_id = project.user_id
        user = User(user_id=user_id)
    else:
        logger.warning("Please provide either a valid project ID or valid three-letter user ID")
        return

    # Create project on Notion
    user_page_id = notion.get_user_page_id(notion_clients_db, user)
    if user_page_id is not None:
        notion_proj_id = notion.create_project(project, user, notion_projects_db, user_page_id=user_page_id, template_page_id=notion_template_page_id)
    else:
        notion_proj_id = notion.create_project(project, user, notion_projects_db, template_page_id=notion_template_page_id)
    
    if default_workorder_task:
        task = Task(
            name="Get workorder for project",
            project_id=project.id
        )
        notion.add_task_to_project(task, tasks_db_id=notion_tasks_db, projects_db_id=notion_projects_db)

    pyperclip.copy(project.id)

    print()
    print(f"Project created with ID: {project.id} (copied to clipboard)")

if __name__ == "__main__":
    main()