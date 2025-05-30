import sys
import argparse
import json
import pyperclip
import httpx
from papi.wrappers import NotionWrapper, TogglTrackWrapper
from papi import config, setup_logger
from papi.user import User
from papi.project import Project, check_project_id, user_id_from_project_id
from papi.task import Task


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
        if not check_project_id(project_id):
            print("Invalid project ID format.")
            project_id = None
        else:
            user_id = user_id_from_project_id(project_id)
    else:
        project_id = None

    # Fixed logic: 'y' or empty means add the default task
    default_input = input("Add default task to get workorder? (y/n) [y]: ").strip().lower()
    default_workorder_task = default_input in ("", "y", "yes")
    no_default_workorder_task = not default_workorder_task

    enable_logging_input = input("Enable logging? (y/n) [n]: ").strip().lower()
    enable_logging = enable_logging_input in ("y", "yes")

    if enable_logging:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = input(f"Set log level {levels} [INFO]: ").strip().upper() or "INFO"
        if log_level not in levels:
            print("Invalid log level; defaulting to INFO.")
            log_level = "INFO"
        log_file = input("Path to log file (leave blank for none): ").strip() or None
    else:
        log_level = None
        log_file = None

    enable_toggl = input("Create Toggl Track project? (y/n) [n]: ").strip().lower() in ("y", "yes")
    enable_notion = input("Create Notion project? (y/n) [n]: ").strip().lower() in ("y", "yes")

    return argparse.Namespace(
        user_id=user_id or None,
        user_name=user_name or None,
        name=name or None,
        project_id=project_id or None,
        no_default_workorder_task=no_default_workorder_task,
        default_workorder_task=default_workorder_task,
        enable_logging=enable_logging,
        log_level=log_level,
        log_file=log_file,
        enable_toggl=enable_toggl,
        enable_notion=enable_notion,
    )


def main():
    """Main function of create-project script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_id", help="three-letter user ID, e.g. JAS")
    parser.add_argument("-v", "--user_name", help="user name, e.g. John Andrew Smith")
    parser.add_argument("-n", "--name", help="short project name, e.g. 'RNA-seq analysis'")
    parser.add_argument(
        "-p", "--project_id", help="full project ID, e.g. P2024-JAS-DEFG"
    )
    parser.add_argument(
        "--no-default-workorder-task",
        action="store_true",
        help="do not add default workorder task",
    )
    parser.add_argument(
        "--enable-toggl", action="store_true", help="create Toggl Track project"
    )
    parser.add_argument(
        "--enable-notion", action="store_true", help="create Notion project"
    )
    parser.add_argument(
        "--enable-logging",
        action="store_true",
        help="enable logging output for the papi library",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="set the logging level (default: INFO)",
    )
    parser.add_argument("--log-file", help="path to a file where logs should be written")

    args = parser.parse_args()
    if len(sys.argv) == 1:
        args = prompt_for_args()

    logger = setup_logger(args.enable_logging, args.log_level, args.log_file)

    # Determine whether to add the default workorder task
    if hasattr(args, "default_workorder_task"):
        default_workorder_task = args.default_workorder_task
    else:
        default_workorder_task = not args.no_default_workorder_task

    user_id = args.user_id
    user_name = args.user_name
    project_name = args.name
    project_id = args.project_id
    enable_toggl = args.enable_toggl
    enable_notion = args.enable_notion

    # Build User and Project
    if project_id and not project_name:
        project = Project(id=project_id)
        user_id = project.user_id
        user = User(user_id=user_id)
    elif project_name and not project_id:
        if user_id and not user_name:
            user = User(user_id=user_id)
        elif user_name and not user_id:
            user = User(user_name=user_name)
        else:
            user = User(user_name=user_name, user_id=user_id)
        project = Project(name=project_name, user_id=user.user_id)
    elif project_id and project_name:
        project = Project(name=project_name, id=project_id)
        user_id = project.user_id
        user = User(user_id=user_id)
    else:
        logger.warning(
            "Please provide either a valid project ID or a valid user ID/name."
        )
        return

    # Toggl Track
    if enable_toggl:
        if "TOGGL_TRACK_API_KEY" not in config or "TOGGL_TRACK_PASSWORD" not in config:
            logger.warning(
                "Set TOGGL_TRACK_API_KEY and TOGGL_TRACK_PASSWORD in your .env"
            )
            return
        toggl = TogglTrackWrapper(
            config["TOGGL_TRACK_API_KEY"], config["TOGGL_TRACK_PASSWORD"]
        )
        toggl.set_default_workspace(config["TOGGL_TRACK_WORKSPACE"])
        toggl_proj_id = toggl.create_project(project, toggl.default_workspace_id)

    # Notion
    if enable_notion:
        required = [
            "NOTION_API_SECRET",
            "NOTION_CLIENTS_DB",
            "NOTION_PROJECTS_DB",
            "NOTION_TEMPLATE_PAGE_ID",
            "NOTION_TASKS_DB",
        ]
        if any(r not in config for r in required):
            logger.warning(
                "Set NOTION_API_SECRET, NOTION_CLIENTS_DB, NOTION_PROJECTS_DB, NOTION_TEMPLATE_PAGE_ID, NOTION_TASKS_DB in your .env"
            )
            return

        notion = NotionWrapper(config["NOTION_API_SECRET"])
        user_page_id = notion.get_user_page_id(
            config["NOTION_CLIENTS_DB"], user
        )
        notion_project = notion.create_project(
            project,
            user,
            config["NOTION_PROJECTS_DB"],
            user_page_id=user_page_id,
            template_page_id=config["NOTION_TEMPLATE_PAGE_ID"],
        )

        if notion_project:
            # Copy to clipboard and print result
            pyperclip.copy(project.id)
            print(f"Project created with ID: {project.id} (copied to clipboard)")

            # Add default task to get workorder      
            if default_workorder_task:
                task = Task(
                    name="Get workorder for project",
                    project_id=project.id,
                )
                notion.add_task_to_project(
                    task,
                    tasks_db_id=config["NOTION_TASKS_DB"],
                    projects_db_id=config["NOTION_PROJECTS_DB"],
                )
                print(f"Default workorder task add to project {project.id}")
            return notion_project
        else:
            print(f"Project not created. {project.id} may exist in Notion already, or project ID clashes.")
            return

if __name__ == "__main__":
    main()