import re
import time
import httpx
import json
import pendulum
import warnings
from typing import Protocol, runtime_checkable
from papi.project import Project


def get_project_ids(project_names):
    """This function takes a list of project names and finds and
    returns a list of project IDs.

    :param project_names: A list of project names.
    :type project_names: list
    :return: A list of project IDs.
    :rtype: list
    """
    project_ids = []
    project_id_pattern = r"P[0-9]{4}-[A-Z]{2}[A-Z0-9]{1}-[A-Z]{4}"
    for project_name in project_names:
        match = re.search(project_id_pattern, project_name)
        if match:
            project_id = match.group()
            if project_id not in project_ids:
                project_ids.append(project_id)
    project_ids = sorted(project_ids)
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
        auth = httpx.BasicAuth(username=self.api_token, password=self.password)
        self.client = httpx.Client(auth=auth)
        return self.client

    def get_me(self) -> dict:
        """Gets the Asana user's data back from the REST API and returns it as
        a dictionary.

        :return: A dictionary containing the user's Asana data.
        :rtype: dict
        """
        client = self.connect()
        r = client.get("https://app.asana.com/api/1.0/users/me")
        r_json = r.json()
        return r_json["data"]

    def set_me(self) -> None:
        """Sets this class' attributes from the data returned by the call to the
        ``get_me`` method, i.e. the user's Asana ID, and their workspaces.
        """
        self.me = self.get_me()
        self.my_id = self.me["gid"]
        workspaces = self.me["workspaces"]
        self.workspaces = {}
        for workspace in workspaces:
            workspace_id = workspace["gid"]
            workspace_name = workspace["name"]
            self.workspaces[workspace_id] = workspace_name

    def set_workspaces(self) -> None:
        """Calls the ``set_me`` method and hence sets the user's Asnana workspaces."""
        self.set_me()

    def get_workspace_id_by_name(self, name: str) -> str:
        """Gets an Asana workspace ID from the associated Asana workspace name.

        :param name: Asnana workspace name.
        :type name: str
        :return: Asnana workspace ID.
        :rtype: str
        """
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
        workspace_id = self.get_workspace_id_by_name(name)
        self.default_workspace_id = workspace_id
        return self.default_workspace_id

    def get_teams(self, workspace_id: str) -> dict:
        """Gets the user's Asana teams using their Asana workspace ID.

        :param workspace_id: Asana workspace ID from which to get Asana teams.
        :type workspace_id: str
        :return: A dictionary containing the Asana teams data.
        :rtype: dict
        """
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
        if self.workspaces is None:
            self.set_workspaces()
        teams = self.get_teams(workspace_id)
        self.teams = {}
        for team in teams:
            team_id = team["gid"]
            team_name = team["name"]
            self.teams[team_id] = team_name

    def get_team_id_by_name(self, name: str) -> str:
        """Gets the ID of an Asana team once a user's Asana teams have been set.

        :param name: Name of the Asana team for which the ID should be found.
        :type name: str
        :raises AttributeError: If the teams attribute is not set on the class,
            then raise an AttributeError.
        :return: The ID of the named Asana team.
        :rtype: str
        """
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
        team_id = self.get_team_id_by_name(name)
        self.default_team_id = team_id
        return self.default_team_id

    def get_team_projects(self) -> dict:
        """Gets all of an Asana team's projects.

        :return: A dictionary containing the team's Asana projects.
        :rtype: dict
        """
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
        projects = self.get_team_projects()
        project_names = [project["name"] for project in projects]
        project_ids = get_project_ids(project_names)
        return project_ids

    def get_team_project_user_ids(self) -> list:
        """Gets user IDS from an Asana team's projects.

        :return: A list of unique team project user IDs.
        :rtype: list
        """
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
        client = self.connect()
        templates_r = client.get(
            f"https://app.asana.com/api/1.0/teams/{team_id}/project_templates"
        )
        templates = templates_r.json()
        return templates["data"]

    def get_user_projects(self):
        """Gets all of the Asana user's projects."""
        pass

    def check_project_exists(self, id):
        """Checks whether an Asana project containing the specified project ID
        already exists.
        """
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
        self.api_token = api_token
        self.password = password
        self.client = None
        self.me = None
        self.my_id = None
        self.workspaces = None
        self.default_workspace_id = None

    def connect(self) -> httpx.Client:
        """Creates a connection to the Toggl Track REST API.

        :return: The httpx Client instance with appropriate authentication.
        :rtype: httpx.Client
        """
        auth = httpx.BasicAuth(username=self.api_token, password=self.password)
        self.client = httpx.Client(auth=auth)
        return self.client

    def get_me(self) -> dict:
        """Gets the Toggl Track user's data back from the REST API and
        returns it as a dictionary.

        :return: A dictionary containing the user's Toggl Track data.
        :rtype: dict
        """
        client = self.connect()
        r = client.get("https://api.track.toggl.com/api/v9/me")
        r_json = r.json()
        return r_json

    def set_me(self) -> None:
        """Sets this class' attributes from the data returned by the call to the
        ``get_me`` method, i.e. the user's Toggl Track ID, etc.
        """
        self.me = self.get_me()
        self.my_id = self.me["id"]

    def get_workspaces(self) -> list:
        """Gets all of the Toggl Track user's workspaces.

        :return: A list containing the user's Toggl Track workspaces.
        :rtype: list
        """
        client = self.connect()
        r = client.get("https://api.track.toggl.com/api/v9/me/workspaces")
        r_json = r.json()
        return r_json

    def set_workspaces(self) -> None:
        """Calls the ``set_me`` method and hence sets the user's Asnana workspaces."""
        self.workspaces = self.get_workspaces()

    def get_workspace_id_by_name(self, name: str) -> str:
        """Gets an Toggl Track workspace ID from the associated workspace name.

        :param name: Toggl Track workspace name.
        :type name: str
        :return: Toggl Track workspace ID.
        :rtype: str
        """
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
        workspace_id = self.get_workspace_id_by_name(name)
        self.default_workspace_id = workspace_id
        return self.default_workspace_id

    def get_user_projects(self) -> dict:
        """Gets all of the Toggl Track user's projects.

        :return: A dictionary containing the user's Toggl Track projects.
        :rtype: dict
        """
        client = self.connect()
        r = client.get("https://api.track.toggl.com/api/v9/me/projects")
        r_json = r.json()
        return r_json

    def get_user_hours(self, start_time=None, end_time=pendulum.now().to_rfc3339_string()) -> dict:
        """Gets all of the Toggl Track user's tracked hours for a given 
        time period. If no end_time is given, then the current time is used.

        :return: A dictionary containing the Toggl Track projects and hours tracked.
        :rtype: dict
        """
        if start_time is not None:
            client = self.connect()
            r = client.get("https://api.track.toggl.com/api/v9/me/time_entries", params={"start_date": start_time, "end_date": end_time})
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
        projects = self.get_workspace_projects()
        project_names = [project["name"] for project in projects]
        project_ids = get_project_ids(project_names)
        return project_ids

    def get_workspace_project_user_ids(self) -> list:
        """Gets user IDS from a Toggl Track workspace's projects.

        :return: A list of unique workspace project user IDs.
        :rtype: list
        """
        project_ids = self.get_workspace_project_ids()
        user_ids = sorted(list(set([pid.split("-")[1] for pid in project_ids])))
        return user_ids

    def check_project_exists(self, id):
        """Checks whether a Toggl Track project containing the specified
        project ID already exists. If a name containing that ID is found,
        return the project details from Toggl Track.

        :return: A dictionary containing the matching project, if it exists.
        :rtype: dict
        """
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
            return project_id
        else:
            return None
