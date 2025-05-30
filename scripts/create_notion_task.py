import sys
import argparse
import json
from papi.wrappers import NotionWrapper
from papi import config, setup_logger
from papi.task import Task

def prompt_for_args():
    """Prompt the user for input interactively."""
    print("No command-line arguments provided. Enter the required information below:")
    print()

    project_id = input("Enter project ID to which task should be added (e.g., P2024-JAS-DEFG): ").strip()

    task_name = input("Enter task name (e.g., 'Run Seqera QC pipeline'): ").strip()

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

    return argparse.Namespace(
        task_name=task_name or None,
        project_id=project_id or None,
        enable_logging=enable_logging,
        log_level=log_level,
        log_file=log_file
    )


def main():
    """Main function of create-notion-task script."""
    required = ["NOTION_API_SECRET", "NOTION_PROJECTS_DB", "NOTION_TASKS_DB"]
    if any(r not in config for r in required):
        logger.warning("Set NOTION_API_SECRET, NOTION_PROJECTS_DB, NOTION_TASKS_DB in your .env")
        return

    notion = NotionWrapper(config["NOTION_API_SECRET"])
    projects_db_id = config["NOTION_PROJECTS_DB"]
    tasks_db_id = config["NOTION_TASKS_DB"]

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task_name", help="task name (e.g., 'Run Seqera QC pipeline')")
    parser.add_argument(
        "-p", "--project_id", help="full project ID, e.g. P2024-JAS-DEFG"
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

    project_id = args.project_id
    task_name = args.task_name

    logger.debug("Checking Notion project exists...")

    project = notion.get_project(projects_db_id=projects_db_id, project_id=project_id)
    if not project:
        logger.warning(f"Project {project_id!r} does not exist in Notion. Cannot add task.")
        return

    if not task_name:
        logger.warning("Task name must not be empty.")
        return

    task = Task(
        name=task_name,
        project_id=project_id,
    )
    notion.add_task_to_project(
        task,
        tasks_db_id=tasks_db_id,
        projects_db_id=projects_db_id,
    )
    logger.debug(f"Task {task_name!r} added to {project_id!r}")
    print(f"Task {task_name!r} added to {project_id!r}")

if __name__ == "__main__":
    main()