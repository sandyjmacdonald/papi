import argparse
import warnings
from papi.wrappers import TogglTrackWrapper
from papi import config
from papi.project import Project

def main():
    """Main function of create-toggl-project script"""

    # Set up argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user_id", type=str, help="three-letter user ID, e.g. CRD", required=False
    )
    parser.add_argument(
        "-g", "--grant_code", type=str, help="grant code, e.g. R12345", required=False
    )
    parser.add_argument(
        "-n", "--name", type=str, help="short project name, e.g. 'RNA-seq analysis'", required=False
    )
    parser.add_argument(
        "-p", "--project_id", type=str, help="full project ID, e.g. P2024-ABC-DEFG, if already generated", required=False
    )
    args = parser.parse_args()

    # Set up Toggl Track API wrapper
    #
    # NOTE: you must have added Toggl Track API key and password, with
    # variable names below to .env file in this directory
    if not "TOGGL_TRACK_API_KEY" in config and not "TOGGL_TRACK_PASSWORD" in config:
        warnings.warn("Please create a .env file with TOGGL_TRACK_API_KEY and TOGGL_TRACK_PASSWORD set!")
        return
    toggl_api_key = config["TOGGL_TRACK_API_KEY"]
    toggl_api_password = config["TOGGL_TRACK_PASSWORD"]
    toggl = TogglTrackWrapper(toggl_api_key, toggl_api_password)

    # Tell wrapper which workspace to set as default
    toggl_workspace = config["TOGGL_TRACK_WORKSPACE"]
    toggl.set_default_workspace(toggl_workspace)

    user_id = args.user_id
    grant_code = args.grant_code
    project_name = args.name
    project_id = args.project_id

    if not project_id and user_id:
        # Create project instance, grant code and name are optional
        if grant_code and project_name:
            proj = Project(user_id=user_id, grant_code=grant_code, name=project_name)
        elif grant_code and not project_name:
            proj = Project(user_id=user_id, grant_code=grant_code)
        elif not grant_code and project_name:
            proj = Project(user_id=user_id, name=project_name)
        else:
            proj = Project(user_id=user_id)
    elif not user_id and project_id:
        # Create project instance, grant code and name are optional
        if grant_code and project_name:
            proj = Project(id=project_id, grant_code=grant_code, name=project_name)
        elif grant_code and not project_name:
            proj = Project(id=project_id, grant_code=grant_code)
        elif not grant_code and project_name:
            proj = Project(id=project_id, name=project_name)
        else:
            proj = Project(id=project_id)
    else:
        warnings.warn("Please provide either a three-letter user_id *or* a full project_id")
        return

    # Create project on Toggl Track
    #
    # If name and grant code were provided, then project name will
    # look like P2024-ABC-WXYZ - RNA-seq analysis (R12345),
    # otherwise it will just be the project ID
    toggl_proj_id = toggl.create_project(proj, toggl.default_workspace_id)
    print(f"Project '{toggl_proj_id}' created successfully!")

if __name__ == "__main__":
    main()