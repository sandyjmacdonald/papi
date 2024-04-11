import time
import httpx
from typing import Protocol, runtime_checkable
from papi.project import Project


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

    def check_project_exists(self):
        """Checks whether an Asana project containing the specified project ID already
        exists.
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

    def connect(self) -> httpx.Client:
        """Creates a connection to the Toggl Track REST API.

        :return: The httpx Client instance with appropriate authentication.
        :rtype: httpx.Client
        """
        auth = httpx.BasicAuth(user_name=self.api_token, password=self.password)
        self.client = httpx.Client(auth=auth)
        return self.client
