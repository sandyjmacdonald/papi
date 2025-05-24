import argparse
import pyperclip
from papi.wrappers import TogglTrackWrapper
from papi import config, setup_logger
from papi.project import Project

def main():
    """Main function of create-toggl-project script"""

    # Set up argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user_id", type=str, help="three-letter user ID, e.g. JAS", required=False
    )
    parser.add_argument(
        "-g", "--workorder", type=str, help="workorder, e.g. R12345", required=False
    )
    parser.add_argument(
        "-n", "--name", type=str, help="short project name, e.g. 'RNA-seq analysis'", required=False
    )
    parser.add_argument(
        "-p", "--project_id", type=str, help="full project ID, e.g. P2024-JAS-ABCD, if already generated", required=False
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

    logger = setup_logger(args.enable_logging, args.log_level, args.log_file)

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

    user_id = args.user_id
    workorder = args.workorder
    project_name = args.name
    project_id = args.project_id

    if project_id and not project_name:
        project = Project(id=project_id)
    elif project_name and not project_id:
        if user_id:
            project = Project(name=project_name, user_id=user_id)
        else:
            logger.warning("Please provide either a valid project ID or valid three-letter user ID")
            return
    elif project_id and project_name:
        project = Project(name=project_name, id=project_id)
    else:
        logger.warning("Please provide either a valid project ID or valid three-letter user ID")
        return

    # Create project on Toggl Track
    #
    # If name and workorder were provided, then project name will
    # look like P2024-JAS-ABCD - RNA-seq analysis (R12345),
    # otherwise it will just be the project ID
    toggl_proj_id = toggl.create_project(project, toggl.default_workspace_id)

    pyperclip.copy(project.id)

    print()
    print(f"Project created with ID: {project.id} (copied to clipboard)")

if __name__ == "__main__":
    main()