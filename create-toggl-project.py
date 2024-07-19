from papi.wrappers import TogglTrackWrapper
from papi import config
from papi.project import Project

# Set up Toggl Track API wrapper
#
# NOTE: you must have added Toggl Track API key and password, with
# variable names below to .env file in this directory
toggl_api_key = config["TOGGL_TRACK_API_KEY"]
toggl_api_password = config["TOGGL_TRACK_PASSWORD"]
toggl = TogglTrackWrapper(toggl_api_key, toggl_api_password)

# Tell wrapper which workspace to set as default
toggl.set_default_workspace("TF Data Science")

# Create project instance, grant code and name are optional
proj = Project(user_id="ABC", grant_code="R12345", name="RNA-seq analysis")

# Create project on Toggl Track
#
# If name and grant code were provided, then project name will
# look like P2024-ABC-WXYZ - RNA-seq analysis (R12345),
# otherwise it will just be the project ID
toggl_proj = toggl.create_project(proj, toggl.default_workspace_id)
