from dotenv import dotenv_values

config = dotenv_values(".env")

ASANA_API_KEY = config["ASANA_API_KEY"]
ASANA_PASSWORD = config["ASANA_PASSWORD"]

TOGGL_TRACK_API_KEY = config["TOGGL_TRACK_API_KEY"]
TOGGL_TRACK_PASSWORD = config["TOGGL_TRACK_PASSWORD"]
