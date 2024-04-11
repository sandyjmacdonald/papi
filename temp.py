# from papi.wrappers import AsanaWrapper
# from papi import ASANA_API_KEY, ASANA_PASSWORD
# from papi import config


# # Asana testing
# ASANA_WORKSPACE = config["ASANA_WORKSPACE"]
# ASANA_TEAM = config["ASANA_TEAM"]
# asana = AsanaWrapper(ASANA_API_KEY, ASANA_PASSWORD)
# workspace_id = asana.set_default_workspace(ASANA_WORKSPACE)
# asana.set_teams(workspace_id)
# team_id = asana.get_team_id_by_name(ASANA_TEAM)

# templates = asana.get_templates(team_id)
# template_id = templates["data"][0]["gid"]

# print(template_id)
# # team_id = asana.set_default_team(ASANA_TEAM)
# # me = asana.get_me()
# # print(me)

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

from papi.user import UserDB, Query, add

user_db = UserDB("test_userdb.json")
u = user_db.insert_user("John Adam Smith", email="jasmith@dummymail.com")
u = user_db.insert_user("James Smith", email="jsmith@dummymail.com")
# Users = Query()
# user_db.db.upsert({"email": "alan.scott@gmail.com"}, Users.userid == "AS1")
# print(u)
# result = user_db.check_matching_userids("AM2")
# print(len(result) > 0)
