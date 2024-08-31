import os
from dotenv import dotenv_values

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
config = dotenv_values(dotenv_path)

ASANA_API_KEY = config["ASANA_API_KEY"]
ASANA_PASSWORD = config["ASANA_PASSWORD"]

TOGGL_TRACK_API_KEY = config["TOGGL_TRACK_API_KEY"]
TOGGL_TRACK_PASSWORD = config["TOGGL_TRACK_PASSWORD"]
