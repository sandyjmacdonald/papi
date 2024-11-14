import re
import time
import httpx
import json
import pendulum
import warnings
import logging
from typing import Protocol, runtime_checkable
from papi.project import Project
from papi.user import User

logger = logging.getLogger(__name__)

def get_project_ids(project_names):
    """This function takes a list of project names and finds and
    returns a list of project IDs.

    :param project_names: A list of project names.
    :type project_names: list
    :return: A list of project IDs.
    :rtype: list
    """
    logger.debug("Calling get_project_ids function")
    project_ids = []
    project_id_pattern = r"P[0-9]{4}-[A-Z]{2}[A-Z0-9]{1}-[A-Z]{4}"
    for project_name in project_names:
        match = re.search(project_id_pattern, project_name)
        if match:
            project_id = match.group()
            if project_id not in project_ids:
                project_ids.append(project_id)
    project_ids = sorted(project_ids)
    if len(project_ids):
        logger.info(f"{len(project_ids)} project IDs found")
    else:
        logger.info(f"No project IDs found")
    return project_ids


@runtime_checkable
class AsanaWrapper(Protocol):
    """This class is a wrapper around the Asana REST API, that adds specific
    helper functions for getting certain bits of data back from the API, and
    adds convenience functions for creating skeleton projects, for example.

    :param api_token: Asana API token.
    :type api_token: str
    :param password: Asana password.
    :type password: str
    """

    def __init__(self, api_token: str, password: str) -> None:
        """Constructor method"""
        logger.debug("Creating AsanaWrapper instance")
        self.api_token = api_token
        self.password = password
        self.client = None
        self.me = None
        self.my_id = None
        self.workspaces = None
        self.default_workspace_id = None
        self.teams = None
        self.default_team_id = None

    def connect(self) -> httpx.Client:
        """Creates a connection to the Asana REST API.

        :return: The httpx Client instance with appropriate authentication.
        :rtype: httpx.Client
        """
        logger.debug("Calling AsanaWrapper.connect method")
        auth = httpx.BasicAuth(username=self.api_token, password=self.password)
        self.client = httpx.Client(auth=auth)
        return self.client

    def get_me(self) -> dict:
        """Gets the Asana user's data back from the REST API and returns it as
        a dictionary.

        :return: A dictionary containing the user's Asana data.
        :rtype: dict
        """
        logger.debug("Calling AsanaWrapper.get_me method")
        client = self.connect()
        r = client.get("https://app.asana.com/api/1.0/users/me")
        r_json = r.json()
        logger.info("Asana user data retrieved")
        return r_json["data"]

    def set_me(self) -> None:
        """Sets this class' attributes from the data returned by the call to the
        ``get_me`` method, i.e. the user's Asana ID, and their workspaces.
        """
        logger.debug("Calling AsanaWrapper.set_me method")
        self.me = self.get_me()
        self.my_id = self.me["gid"]
        workspaces = self.me["workspaces"]
        self.workspaces = {}
        for workspace in workspaces:
            workspace_id = workspace["gid"]
            workspace_name = workspace["name"]
            self.workspaces[workspace_id] = workspace_name
        logger.info("AsanaWrapper attributes set")

    def set_workspaces(self) -> None:
        """Calls the ``set_me`` method and hence sets the user's Asnana workspaces."""
        logger.debug("Calling AsanaWrapper.set_workspaces method")
        self.set_me()

    def get_workspace_id_by_name(self, name: str) -> str:
        """Gets an Asana workspace ID from the associated Asana workspace name.

        :param name: Asnana workspace name.
        :type name: str
        :return: Asnana workspace ID.
        :rtype: str
        """
        logger.debug("Calling AsanaWrapper.get_workspace_id_by_name method")
        if self.workspaces is None:
            self.set_workspaces()
        for id in self.workspaces:
            if self.workspaces[id] == name:
                return id

    def set_default_workspace(self, name: str) -> str:
        """Sets the user's default Asana workspace. When other class methods are called,
        this is the workspace that will be used.

        :param name: Name of the Asana workspace to set as default.
        :type name: str
        :return: ID of the default Asana workspace that has been set.
        :rtype: str
        """
        logger.debug("Calling AsanaWrapper.set_default_workspace method")
        workspace_id = self.get_workspace_id_by_name(name)
        self.default_workspace_id = workspace_id
        logger.info("AsanaWrapper default workspace set")
        return self.default_workspace_id

    def get_teams(self, workspace_id: str) -> dict:
        """Gets the user's Asana teams using their Asana workspace ID.

        :param workspace_id: Asana workspace ID from which to get Asana teams.
        :type workspace_id: str
        :return: A dictionary containing the Asana teams data.
        :rtype: dict
        """
        logger.debug("Calling AsanaWrapper.get_teams method")
        params = {"workspace": workspace_id}
        client = self.connect()
        r = client.get(
            f"https://app.asana.com/api/1.0/users/{self.my_id}/teams", params=params
        )
        r_json = r.json()
        return r_json["data"]

    def set_teams(self, workspace_id: str) -> None:
        """Gets and sets the user's Asana teams using an Asana workspace ID.

        :param workspace_id: Asana workspace ID from which to set Asana teams.
        :type workspace_id: str
        """
        logger.debug("Calling AsanaWrapper.set_teams method")
        if self.workspaces is None:
            self.set_workspaces()
        teams = self.get_teams(workspace_id)
        self.teams = {}
        for team in teams:
            team_id = team["gid"]
            team_name = team["name"]
            self.teams[team_id] = team_name
        logger.info("AsanaWrapper user teams set")

    def get_team_id_by_name(self, name: str) -> str:
        """Gets the ID of an Asana team once a user's Asana teams have been set.

        :param name: Name of the Asana team for which the ID should be found.
        :type name: str
        :raises AttributeError: If the teams attribute is not set on the class,
            then raise an AttributeError.
        :return: The ID of the named Asana team.
        :rtype: str
        """
        logger.debug("Calling AsanaWrapper.get_team_id_by_name method")
        if self.teams is not None:
            for id in self.teams:
                if self.teams[id] == name:
                    return id
        else:
            raise AttributeError(
                "teams attribute has not been set, set with set_teams() method"
            )

    def set_default_team(self, name: str) -> str:
        """Sets a user's default Asana team using the name of the team.

        :param name: Name of the Asana team to set as default.
        :type name: str
        :return: The ID of the Asana team that has been set as default.
        :rtype: str
        """
        logger.debug("Calling AsanaWrapper.set_default_team method")
        team_id = self.get_team_id_by_name(name)
        self.default_team_id = team_id
        logger.info("AsanaWrapper default team set")
        return self.default_team_id

    def get_team_projects(self) -> dict:
        """Gets all of an Asana team's projects.

        :return: A dictionary containing the team's Asana projects.
        :rtype: dict
        """
        logger.debug("Calling AsanaWrapper.get_team_projects method")
        if self.default_team_id is not None:
            team_gid = self.default_team_id
            client = self.connect()
            r = client.get(f"https://app.asana.com/api/1.0/teams/{team_gid}/projects")
            r_json = r.json()
            return r_json["data"]

    def get_team_project_ids(self) -> list:
        """Gets project IDS from an Asana team's projects.

        :return: A list of unique project IDs.
        :rtype: list
        """
        logger.debug("Calling AsanaWrapper.get_team_project_ids method")
        projects = self.get_team_projects()
        project_names = [project["name"] for project in projects]
        project_ids = get_project_ids(project_names)
        return project_ids

    def get_team_project_user_ids(self) -> list:
        """Gets user IDS from an Asana team's projects.

        :return: A list of unique team project user IDs.
        :rtype: list
        """
        logger.debug("Calling AsanaWrapper.get_team_project_user_ids method")
        project_ids = self.get_team_project_ids()
        user_ids = sorted(list(set([pid.split("-")[1] for pid in project_ids])))
        return user_ids

    def create_project(
        self, project: Project, workspace_id: str, team_id: str, template_id: str = None
    ) -> str:
        """Creates a skeleton Asana project from a ``Project`` instance.

        :param project: ``Project`` instance, for which the Asana project
            should be created.
        :type project: Project
        :param workspace_id: ID of the Asana workspace in which the project
            should be created.
        :type workspace_id: str
        :param team_id: ID of the Asana team for which the project should
            be created.
        :type team_id: str
        :param template_id: Template ID to use when creating the project, defaults to None
        :type template_id: str, optional
        :raises TypeError: If the ``project`` parameter passed is not a valid
            ``Project`` instance, raise a TypeError.
        :return: The ID of the created Asana project.
        :rtype: str
        """
        logger.debug("Calling AsanaWrapper.create_project method")
        if not isinstance(project, Project):
            raise TypeError("Provided project is not a valid Project instance")

        data = {
            "name": project.id,
            "workspace": workspace_id,
            "team": team_id,
            "public": True,
        }

        if template_id is not None:
            client = self.connect()
            r = client.post(
                f"https://app.asana.com/api/1.0/project_templates/{template_id}/instantiateProject",
                data=data,
            )
            project = r.json()
            project_id = project["data"]["new_project"]["gid"]
            time.sleep(2.5)
            logger.info(f"Asana project {project_id} created")
            return project_id
        else:
            pass

    def get_templates(self, team_id: str) -> dict:
        """Gets the templates from the provided Asana team ID.

        :param team_id: ID of the Asana team from which to retrieve templates.
        :type team_id: str
        :return: A dictionary containing the retrieved Asana templates.
        :rtype: dict
        """
        logger.debug("Calling AsanaWrapper.get_templates method")
        client = self.connect()
        templates_r = client.get(
            f"https://app.asana.com/api/1.0/teams/{team_id}/project_templates"
        )
        templates = templates_r.json()
        return templates["data"]

    def get_user_projects(self):
        """Gets all of the Asana user's projects."""
        logger.debug("Calling AsanaWrapper.get_user_projects method")
        pass

    def check_project_exists(self, id):
        """Checks whether an Asana project containing the specified project ID
        already exists.
        """
        logger.debug("Calling AsanaWrapper.check_project_exists method")
        pass


class TogglTrackWrapper(Protocol):
    """This class is a wrapper around the Toggl Track REST API, that adds specific
    helper functions for getting certain bits of data back from the API, and
    adds convenience functions for creating projects, for example.

    :param api_token: Toggl Track API token
    :type api_token: str
    :param password: Toggl Track password
    :type password: str
    """

    def __init__(self, api_token: str, password: str) -> None:
        """Constructor method"""
        logger.debug("Creating TogglTrackWrapper instance")
        self.api_token = api_token
        self.password = password
        self.client = None
        self.me = None
        self.my_id = None
        self.workspaces = None
        self.default_workspace_id = None
        logger.info("TogglTrackWrapper instance created")

    def connect(self) -> httpx.Client:
        """Creates a connection to the Toggl Track REST API.

        :return: The httpx Client instance with appropriate authentication.
        :rtype: httpx.Client
        """
        logger.debug("Calling TogglTrackWrapper.connect method")
        auth = httpx.BasicAuth(username=self.api_token, password=self.password)
        self.client = httpx.Client(auth=auth)
        return self.client

    def get_me(self) -> dict:
        """Gets the Toggl Track user's data back from the REST API and
        returns it as a dictionary.

        :return: A dictionary containing the user's Toggl Track data.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.get_me method")
        client = self.connect()
        r = client.get("https://api.track.toggl.com/api/v9/me")
        r_json = r.json()
        logger.info("Toggl Track user data retrieved")
        return r_json

    def set_me(self) -> None:
        """Sets this class' attributes from the data returned by the call to the
        ``get_me`` method, i.e. the user's Toggl Track ID, etc.
        """
        logger.debug("Calling TogglTrackWrapper.set_me method")
        self.me = self.get_me()
        self.my_id = self.me["id"]
        logger.info("TogglTrackWrapper attributes set")

    def get_workspaces(self) -> list:
        """Gets all of the Toggl Track user's workspaces.

        :return: A list containing the user's Toggl Track workspaces.
        :rtype: list
        """
        logger.debug("Calling TogglTrackWrapper.get_workspaces method")
        client = self.connect()
        r = client.get("https://api.track.toggl.com/api/v9/me/workspaces")
        r_json = r.json()
        return r_json

    def set_workspaces(self) -> None:
        """Calls the ``set_me`` method and hence sets the user's Asnana workspaces."""
        logger.debug("Calling TogglTrackWrapper.set_workspaces method")
        self.workspaces = self.get_workspaces()
        logger.info("Toggl Track user workspaces set")

    def get_workspace_id_by_name(self, name: str) -> str:
        """Gets an Toggl Track workspace ID from the associated workspace name.

        :param name: Toggl Track workspace name.
        :type name: str
        :return: Toggl Track workspace ID.
        :rtype: str
        """
        logger.debug("Calling TogglTrackWrapper.get_workspace_id_by_name method")
        if self.workspaces is None:
            self.set_workspaces()
        for workspace in self.workspaces:
            if workspace["name"] == name:
                return workspace["id"]

    def set_default_workspace(self, name: str) -> str:
        """Sets the user's default Toggl Track workspace. When other class
        methods are called, this is the workspace that will be used.

        :param name: Name of the Toggl Track workspace to set as default.
        :type name: str
        :return: ID of the default Toggl Track workspace that has been set.
        :rtype: str
        """
        logger.debug("Calling TogglTrackWrapper.set_default_workspace method")
        workspace_id = self.get_workspace_id_by_name(name)
        self.default_workspace_id = workspace_id
        logger.info("Toggl Track default workspace set")
        return self.default_workspace_id

    def get_user_projects(self) -> dict:
        """Gets all of the Toggl Track user's projects.

        :return: A dictionary containing the user's Toggl Track projects.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.get_user_projects method")
        client = self.connect()
        r = client.get("https://api.track.toggl.com/api/v9/me/projects")
        r_json = r.json()
        return r_json

    def get_user_hours(
        self, start_time=None, end_time=pendulum.now().to_rfc3339_string()
    ) -> dict:
        """Gets all of the Toggl Track user's tracked hours for a given
        time period. If no end_time is given, then the current time is used.

        :return: A dictionary containing the Toggl Track projects and hours tracked.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.get_user_hours method")
        if start_time is not None:
            client = self.connect()
            r = client.get(
                "https://api.track.toggl.com/api/v9/me/time_entries",
                params={"start_date": start_time, "end_date": end_time},
            )
            times_json = r.json()
            times = {}
            for t in times_json:
                pid = t["pid"]
                seconds = t["duration"]
                hours = seconds / 60 / 60
                if pid not in times:
                    times[pid] = hours
                else:
                    times[pid] += hours
            return times
        else:
            warnings.warn("Please provide a valid start date/time in RFC3339 format!")
            return None

    def get_workspace_projects(self) -> dict:
        """Gets all of a Toggl Track workspace's projects.

        :return: A dictionary containing the workspace's Toggl Track projects.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.get_workspace_projects method")
        if self.default_workspace_id is None:
            if self.workspaces is None:
                self.set_workspaces()
                self.default_workspace_id = self.workspaces[0]["id"]
            else:
                self.default_workspace_id = self.workspaces[0]["id"]
        workspace_id = self.default_workspace_id
        client = self.connect()
        r = client.get(
            f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects"
        )
        r_json = r.json()
        return r_json

    def get_workspace_project_ids(self) -> list:
        """Gets project IDS from a Toggl Track workspace's projects.

        :return: A list of unique project IDs.
        :rtype: list
        """
        logger.debug("Calling TogglTrackWrapper.get_workspace_project_ids method")
        projects = self.get_workspace_projects()
        project_names = [project["name"] for project in projects]
        project_ids = get_project_ids(project_names)
        return project_ids

    def get_workspace_project_user_ids(self) -> list:
        """Gets user IDS from a Toggl Track workspace's projects.

        :return: A list of unique workspace project user IDs.
        :rtype: list
        """
        logger.debug("Calling TogglTrackWrapper.get_workspace_project_user_ids method")
        project_ids = self.get_workspace_project_ids()
        user_ids = sorted(list(set([pid.split("-")[1] for pid in project_ids])))
        return user_ids

    def check_project_exists(self, id: str) -> str:
        """Checks whether a Toggl Track project containing the specified
        project ID already exists. If a name containing that ID is found,
        return the project details from Toggl Track.

        :return: A dictionary containing the matching project, if it exists.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.check_project_exists method")
        projects = self.get_workspace_projects()
        matching_project = {}
        for project in projects:
            if id in project["name"]:
                matching_project = project
        return matching_project

    def create_project(
        self,
        project: Project,
        workspace_id: str,
    ) -> str:
        """Creates a skeleton Toggl Track project from a ``Project`` instance.

        :param project: ``Project`` instance, for which the Toggl Track project
            should be created.
        :type project: Project
        :param workspace_id: ID of the Toggl Track workspace in which the project
            should be created.
        :type workspace_id: str
        :raises TypeError: If the ``project`` parameter passed is not a valid
            ``Project`` instance, raise a TypeError.
        :return: The ID of the created Toggl Track project or None.
        :rtype: str
        """
        logger.debug("Calling TogglTrackWrapper.create_project method")
        if not isinstance(project, Project):
            raise TypeError("Provided project is not a valid Project instance")
        if self.default_workspace_id is None:
            if self.workspaces is None:
                self.set_workspaces()
                self.default_workspace_id = self.workspaces[0]["id"]
            else:
                self.default_workspace_id = self.workspaces[0]["id"]
        workspace_id = self.default_workspace_id
        if not self.check_project_exists(project.id):
            name = project.id
            if project.name != "":
                name += f" - {project.name}"
            if project.grant_code is not None:
                name += f" ({project.grant_code})"
            data = {
                "name": name,
                "active": True,
                "auto_estimates": False,
                "is_private": False,
                "color": "#2da608",
            }
            client = self.connect()
            r = client.post(
                f"https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/projects",
                data=json.dumps(data),
            )
            project = r.json()
            project_id = project["id"]
            time.sleep(2.5)
            logger.info(f"Toggl Track project {project_id} created")
            return project_id
        else:
            logger.warning("Toggl Track project not created")
            return None


@runtime_checkable
class NotionWrapper(Protocol):
    """This class is a wrapper around the Notion API, that adds specific
    helper functions for getting certain bits of data back from the API, and
    adds convenience functions for creating clients, projects etc.

    :param api_secret: Notion API secret.
    :type api_secret: str
    """

    def __init__(self, api_secret: str) -> None:
        """Constructor method"""
        logger.debug("Creating NotionWrapper instance")
        self.api_secret = api_secret
        logger.info("NotionWrapper instance created")

    def create_user(self, user: User, clients_db_id: str) -> str:
        """Creates a Notion client (user) from a `User` instance.

        :param user: `User` instance, for which the Notion client, i.e. user
            should be created.
        :type project: User
        :param clients_db_id: ID of the Notion Clients database to which the user
            should be added.
        :type clients_db_id: str
        :return: The ID of the created client/user database page in Notion.
        :rtype: str
        """
        logger.debug("Calling NotionWrapper.create_user method")
        user_name = user.user_name
        user_id = user.user_id
        email = user.email
        headers = {
            "Authorization": f"Bearer {self.api_secret}",
            "Notion-Version": "2022-06-28",
        }
        data = {
            "parent": {"database_id": clients_db_id},
            "properties": {
                "Code": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": user_id, "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": user_id,
                            "href": None,
                        }
                    ],
                },
                "Type": {
                    "type": "select",
                    "select": {"name": "Individual", "color": "blue"},
                },
                "Email": {"type": "email", "email": email},
                "York User ID": {"type": "rich_text", "rich_text": []},
                "Name": {
                    "id": "title",
                    "type": "title",
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": user_name, "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": user_name,
                            "href": None,
                        }
                    ],
                },
            },
        }
        r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=data)
        r_json = r.json()
        page_id = r_json["id"]
        logger.info(f"Notion user created with page ID {page_id}")
        return page_id

    def get_user_page_id(self, clients_db_id: str, user: User) -> str:
        """Gets the Notion user page ID give a three-letter user ID.

        :param clients_db_id: ID of the Notion Clients database from which to get
        the clients.
        :type clients_db_id: str
        :param user: A User instance
        :type user: User
        :return: The Notion user page ID.
        :rtype: str
        """
        logger.debug("Calling NotionWrapper.get_user_page_id method")
        user_id = user.user_id
        headers = {
            "Authorization": f"Bearer {self.api_secret}",
            "Notion-Version": "2022-06-28",
        }
        data = {
            "filter": {
                "property": "Code",
                "rich_text": {
                    "equals": user_id
                }
            }
        }
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{clients_db_id}/query",
            headers=headers,
            json=data,
        )
        r_json = r.json()
        u = r_json["results"]
        if u:
            user_page_id = u[0]["id"]
            logger.info(f"Notion user found with page ID {user_page_id}")
            return user_page_id
        else:
            logger.warning("Notion user not found")
            return None

    def get_users(self, clients_db_id: str) -> list:
        """Gets the Notion clients (users) from the Clients database.

        :param clients_db_id: ID of the Notion Clients database from which to get
        the clients.
        :type clients_db_id: str
        :return: A list of User instances for the returned users from Notion.
        :rtype: list
        """
        logger.debug("Calling NotionWrapper.get_users method")
        headers = {
            "Authorization": f"Bearer {self.api_secret}",
            "Notion-Version": "2022-06-28",
        }
        data = {}
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{clients_db_id}/query",
            headers=headers,
            json=data,
        )
        r_json = r.json()
        users = []
        for u in r_json["results"]:
            user_id = u["properties"]["Code"]["rich_text"][0]["plain_text"]
            user_name = u["properties"]["Name"]["title"][0]["plain_text"]
            email = u["properties"]["Email"]["email"]
            user = User(user_name=user_name, user_id=user_id, email=email)
            users.append(user)
        if len(users):
            logger.info(f"{len(users)} Notion users found")
        else:
            logger.warning("No Notion users found")
        return users

    def create_project(self, project: Project, user: User, projects_db_id: str, user_page_id=None) -> str:
        """Creates a new project on Notion.
        
        :param project: A Project instance.
        :type project: Project
        :param user: A User instance.
        :type user: User
        :param projects_db_id: ID of the Notion projects database in which to add the project.
        :type projects_db_id: str
        :param user_page_id: ID of the user in Notion, if they've been added. Can get this with 
        get_user_page_id function.
        :type user_page_id: str
        :return: The page ID of the project created in Notion.
        :rtype: str
        """
        logger.debug("Calling NotionWrapper.create_project method")
        project_id = project.id
        project_name = project.name
        user_id = user.user_id
        if user_page_id is not None:
            pi_relation = [{"id": user_page_id}]
        else:
            pi_relation = []
        headers = {
            "Authorization": f"Bearer {self.api_secret}",
            "Notion-Version": "2022-06-28",
        }
        data = {
            "parent": {"database_id": projects_db_id},
            "properties": {
                "Status": {
                    "status": None,
                },
                "Description": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": project_name,
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": project_name,
                            "href": None,
                        }
                    ],
                },
                "Hourly Rate": {
                    "type": "number",
                    "number": 0.0,  # Set an appropriate number
                },
                "Slug": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": project_name, "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": project_name,
                            "href": None,
                        }
                    ],
                },
                "Type": {
                    "type": "select",  # Assuming Type is a select property
                    "select": None,
                },
                "PI Code": {
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": user_id, "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": user_id,
                            "href": None,
                        }
                    ],
                },
                "Priority": {
                    "type": "select",
                    "select": None,
                },
                "Tags": {
                    "type": "multi_select",
                    "multi_select": [],
                },
                "PI": {
                    "type": "relation",
                    "relation": pi_relation,
                    "has_more": False,
                },
                "Start Date": {
                    "type": "date",
                    # "date": {"start": "2024-09-12", "end": None, "time_zone": None},
                    "date": None,
                },
                "Owner": {
                    "type": "people",
                    "people": [],
                },
                "Project ID": {
                    "type": "title",
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": project_id, "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": project_id,
                            "href": None,
                        }
                    ],
                },
            },
        }
        r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=data)
        r_json = r.json()
        page_id = r_json["id"]
        logger.info(f"Notion project created with page ID {page_id}")
        return page_id

    def get_projects(self, projects_db_id: str) -> list:
        """Gets the Notion projects from the Clients database.

        :param projects_db_id: ID of the Notion Projects database from which to get
        the projects.
        :type projects_db_id: str
        :return: A list of Project instances for the returned projects from Notion.
        :rtype: list
        """
        logger.debug("Calling NotionWrapper.get_projects method")
        headers = {
            "Authorization": f"Bearer {self.api_secret}",
            "Notion-Version": "2022-06-28",
        }
        data = {}
        r = httpx.post(
            f"https://api.notion.com/v1/databases/{projects_db_id}/query",
            headers=headers,
            json=data,
        )
        r_json = r.json()
        projects = []
        for p in r_json["results"]:
            project_id = p["properties"]["Project ID"]["title"][0]["plain_text"]
            project_name = p["properties"]["Description"]["rich_text"][0]["plain_text"]
            user_id = p["properties"]["PI Code"]["rollup"]["array"][0]["rich_text"][0][
                "plain_text"
            ]
            project = Project(id=project_id, name=project_name)
            projects.append(project)
        if len(projects):
            logger.info(f"{len(projects)} Notion projects found")
        else:
            logger.warning("No Notion projects found")
        return projects
