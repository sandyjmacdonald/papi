from papi.wrappers import AsanaWrapper
from papi import ASANA_API_KEY, ASANA_PASSWORD
from papi import config


# Asana testing
ASANA_WORKSPACE = config["ASANA_WORKSPACE"]
ASANA_TEAM = config["ASANA_TEAM"]
asana = AsanaWrapper(ASANA_API_KEY, ASANA_PASSWORD)
workspace_id = asana.set_default_workspace(ASANA_WORKSPACE)
asana.set_teams(workspace_id)
team_id = asana.get_team_id_by_name(ASANA_TEAM)

# templates = asana.get_templates(team_id)
# template_id = templates["data"][0]["gid"]

# print(template_id)
team_id = asana.set_default_team(ASANA_TEAM)
me = asana.get_me()
print(me)

project_ids = asana.get_team_project_ids()
print(project_ids)

user_ids = asana.get_team_project_user_ids()
print(user_ids)

# # from papi.project import Project

# # example_invalid_project_id = "P2024_RST_ABCD"
# # proj = Project(id=example_invalid_project_id)

# # team_id = asana.set_default_team(ASANA_TEAM)
# # me = asana.get_me()
# # print(me)

# # from papi.project import Project

# # example_invalid_project_id = "P2024_RST_ABCD"
# # proj = Project(id=example_invalid_project_id)

# from tinydb import TinyDB, Query

# db = TinyDB("db.json")
# rec = db.insert({"type": "apple", "count": 7})
# print(rec)

# from papi.user import UserDB, User, Query, add

# user_db = UserDB("userdb.json")
# usr = User("John Adam Smith", email="jasmith@dummymail.com")
# u = user_db.insert_user(usr)
# usr = User("James Smith", email="jsmith@dummymail.com")
# u = user_db.insert_user(usr)
# Users = Query()
# user_db.db.upsert({"email": "alan.scott@gmail.com"}, Users.userid == "AS1")
# print(u)
# result = user_db.check_matching_userids("AM2")
# print(len(result) > 0)

# from papi.wrappers import TogglTrackWrapper
# from papi import config
# from papi.project import Project
# from papi.user import UserDB, User

# user_db = UserDB()
# user = User("John Adam Smith")
# user_id = user_db.insert_user(user)
# proj = Project(user_id=user_id, grant_code="R12345", name="RNA-seq analysis")

# Toggl Track testing
# toggl_api_key = config["TOGGL_TRACK_API_KEY"]
# toggl_api_password = config["TOGGL_TRACK_PASSWORD"]
# toggl = TogglTrackWrapper(toggl_api_key, toggl_api_password)
# toggl.set_default_workspace("TF Data Science")
# project_ids = toggl.get_workspace_project_ids()
# print(project_ids)
# user_ids = toggl.get_workspace_project_user_ids()
# print(user_ids)

# toggl_proj = toggl.create_project(proj, toggl.default_workspace_id)
