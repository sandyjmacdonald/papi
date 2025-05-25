import re
import time
import httpx
import json
import pendulum
import warnings
import logging
from typing import Protocol, runtime_checkable
from pprint import pprint
from papi.project import Project, get_project_ids, decompose_project_name
from papi.task import Task
from papi.user import User

logger = logging.getLogger(__name__)


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
    
    def get_user_project_objects(self) -> list:
        """Gets all of the Toggl Track user's projects as Project instances.

        :return: A list of Project instances.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.get_user_project_objects method")
        user_projects_json = self.get_user_projects()
        user_project_names = [p["name"] for p in user_projects_json]
        user_project_created = [pendulum.parse(p["created_at"]) for p in user_projects_json]
        user_project_modified = [pendulum.parse(p["at"]) for p in user_projects_json]
        user_projects = []
        for i, n in enumerate(user_project_names):
            decomposed = decompose_project_name(n)
            if decomposed["project_id"] is not None:
                project_id = decomposed["project_id"]
                project_name = decomposed["project_name"]
                created_at = user_project_created[i]
                modified_at = user_project_modified[i]
                project = Project(id=project_id, name=project_name, created_at=created_at, modified_at=modified_at)
                user_projects.append(project)
        return user_projects

    def get_user_hours(
        self, start_time=None, end_time=pendulum.now().to_rfc3339_string()
    ) -> dict:
        """Gets all of the Toggl Track user's tracked hours for a given
        time period. If no end_time is given, then the current time is used. 
        Only works with start dates up to a maximum of three months ago.

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
            if isinstance(times_json, list):
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
                warnings.warn(times_json)
                return None
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

    def get_workspace_project_objects(self) -> list:
        """Gets all of the Toggl Track workspace's projects as Project instances.

        :return: A list of Project instances.
        :rtype: dict
        """
        logger.debug("Calling TogglTrackWrapper.get_workspace_project_objects method")
        workspace_projects_json = self.get_workspace_projects()
        workspace_project_names = [p["name"] for p in workspace_projects_json]
        workspace_projects = []
        workspace_project_created = [pendulum.parse(p["created_at"]) for p in workspace_projects_json]
        workspace_project_modified = [pendulum.parse(p["at"]) for p in workspace_projects_json]
        for i, n in enumerate(workspace_project_names):
            decomposed = decompose_project_name(n)
            if decomposed["project_id"] is not None:
                project_id = decomposed["project_id"]
                project_name = decomposed["project_name"]
                created_at = workspace_project_created[i]
                modified_at = workspace_project_modified[i]
                project = Project(id=project_id, name=project_name, created_at=created_at, modified_at=modified_at)
                workspace_projects.append(project)
        return workspace_projects

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
            if project.workorder is not None:
                name += f" ({project.workorder})"
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

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_secret}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def _fetch_template_page(self, template_page_id: str) -> dict:
        """Retrieve the template page’s properties."""
        r = httpx.get(
            f"https://api.notion.com/v1/pages/{template_page_id}",
            headers=self._headers()
        )
        r.raise_for_status()
        return r.json()

    def _fetch_template_blocks(self, template_page_id: str) -> list[dict]:
        """Page through and collect all child blocks of the template."""
        blocks: list[dict] = []
        url = f"https://api.notion.com/v1/blocks/{template_page_id}/children"
        params = {"page_size": 100}
        while True:
            r = httpx.get(url, headers=self._headers(), params=params)
            r.raise_for_status()
            js = r.json()
            blocks.extend(js["results"])
            if not js.get("has_more"):
                break
            params = {"start_cursor": js["next_cursor"], "page_size": 100}
        return blocks

    def _clean_properties(self, raw: dict) -> dict:
        """Strip out IDs, types, rollup/formula wrappers, leaving only the API-legal values."""
        clean = {}
        for name, meta in raw.items():
            t = meta.get("type")
            if t == "title":
                clean[name] = meta["title"]
            elif t == "rich_text":
                clean[name] = meta["rich_text"]
            elif t == "select":
                sel = meta.get("select")
                if sel and sel.get("name"):
                    clean[name] = {"name": sel["name"]}
            elif t == "multi_select":
                clean[name] = [
                    {"name": m["name"]} for m in meta.get("multi_select", []) if m.get("name")
                ]
            elif t == "status":
                st = meta.get("status")
                if st and st.get("name"):
                    clean[name] = {"name": st["name"]}
            elif t == "date":
                d = meta.get("date")
                if d and d.get("start"):
                    clean[name] = {"start": d["start"], **({"end": d["end"]} if d.get("end") else {})}
            elif t in ("people", "relation"):
                key = t
                clean[name] = [ {"id": x["id"]} for x in meta.get(key, []) if x.get("id") ]
        return clean

    def _clean_blocks(self, raw_blocks: list[dict]) -> list[dict]:
        ALLOWED = {
            "paragraph","heading_1","heading_2","heading_3",
            "to_do","bulleted_list_item","numbered_list_item",
            "toggle","quote","callout",
            "image","video","file","embed","bookmark",
        }
        clean = []
        for b in raw_blocks:
            t = b["type"]
            if t not in ALLOWED:
                continue
            minimal = { "type": t, t: b[t] }
            if b.get("has_children"):
                child_raw = self._fetch_template_blocks(b["id"])
                minimal["children"] = self._clean_blocks(child_raw)
            clean.append(minimal)
        return clean

    def _post_with_retries(
        self,
        url: str,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        **kwargs
    ) -> httpx.Response:
        """
        Perform an HTTP POST with a simple retry/backoff on ReadTimeout.

        :param url: The URL to send the POST request to.
        :type url: str
        :param max_retries: Maximum number of attempts before giving up.
        :type max_retries: int
        :param backoff_factor: Initial backoff delay in seconds, doubled each retry.
        :type backoff_factor: float
        :param kwargs: Any additional arguments to pass to httpx.post().
        :return: The successful HTTP response.
        :rtype: httpx.Response
        :raises RuntimeError: If all retries time out.
        """
        delay = backoff_factor
        for attempt in range(1, max_retries + 1):
            try:
                return httpx.post(url, **kwargs)
            except httpx.ReadTimeout:
                logger.warning(
                    f"Timeout on attempt {attempt}/{max_retries} for {url}, retrying in {delay}s…"
                )
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"All {max_retries} retries timed out for {url}")

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
        headers = self._headers()
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
        headers = self._headers()
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
            logger.info("Notion user not found")
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
        headers = self._headers()
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

    def check_project_exists(self, project: Project, projects_db_id: str) -> Project:
        """Checks whether a Notion project containing the specified
        project ID already exists. If a name containing that ID is found,
        return the existing project.

        :return: The Project instance, if it exists.
        :rtype: Project
        """
        logger.debug("Calling NotionWrapper.check_project_exists method")
        
        existing_projects = self.get_all_projects(projects_db_id)
        project_exists = project.id in [p.id for p in existing_projects]
        if project_exists:
            existing_project = self.get_project(projects_db_id=projects_db_id, project_id=project.id)
            return existing_project
        else:
            return

    def create_project(
        self,
        project: Project,
        user: User,
        projects_db_id: str,
        user_page_id: str | None = None,
        template_page_id: str | None = None,
    ) -> str:
        """
        Creates a new project on Notion, optionally cloning from a database template.

        :param project: A Project instance.
        :param user: A User instance.
        :param projects_db_id: ID of the Notion projects database.
        :param user_page_id: ID of the user in Notion (for the PI relation).
        :param template_page_id: If given, we’ll fetch that page’s properties & children
                                 and use them as the base for this new record.
        :return: The page ID of the created project.
        """
        logger.debug("Calling NotionWrapper.create_project method")
        headers = self._headers()

        existing_project = self.check_project_exists(project, projects_db_id=projects_db_id)
        if existing_project:
            logger.info(f"Project {project.id!r} already exists in Notion as page {existing_project.notion_page_id}")
            return

        if template_page_id:
            tpl_raw     = self._fetch_template_page(template_page_id)
            base_props  = self._clean_properties(tpl_raw["properties"])
            raw_blocks  = self._fetch_template_blocks(template_page_id)
            base_blocks = self._clean_blocks(raw_blocks)
        else:
            base_props, base_blocks = {}, []

        overrides = {
            "Project ID": [
                {
                    "type": "text",
                    "text": {"content": project.id}
                }
            ],
            "Description": [
                {
                    "type": "text",
                    "text": {"content": project.name}
                }
            ],
            "Slug": [
                {
                    "type": "text",
                    "text": {"content": project.name}
                }
            ],
            "PI": [{"id": user_page_id}] if user_page_id else [],
        }

        merged_props = {**base_props, **overrides}

        payload: dict = {
            "parent":     {"database_id": projects_db_id},
            "properties": merged_props,
        }
        if base_blocks:
            payload["children"] = base_blocks

        r = httpx.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError:
            print("→ Request JSON:")
            print(json.dumps(payload, indent=2))
            print("→ Notion error response:")
            print(r.json())
            raise

        new_page_id = r.json()["id"]
        logger.info(f"Notion project cloned from template as page ID {new_page_id}")
        project.notion_page_id = new_page_id

        patch_payload = {
            "properties": {
                "Owner": {
                    "people": []
                },
                "Status": {
                    "status": {"name": "Not Started"}
                },
                "Priority": {
                    "select": {"name": "Medium"}
                },
            }
        }

        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{new_page_id}",
            headers=headers,
            json=patch_payload,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as err:
            print("→ Patch payload:")
            print(json.dumps(patch_payload, indent=2))
            print("→ Notion error response:")
            print(resp.json())
            raise

        logger.info(
            f"Notion project cloned and properties normalized: page ID {new_page_id}"
        )
        return project


    def get_all_projects(self, projects_db_id: str) -> list:
        """
        Fetches all projects from the Notion Projects database, with timeout and retry.

        :param projects_db_id: ID of the Notion Projects database to query.
        :type projects_db_id: str
        :return: A list of Project instances for the returned projects.
        :rtype: list
        """
        logger.debug("Calling NotionWrapper.get_all_projects method")
        headers = self._headers()
        data = {}
        try:
            response = self._post_with_retries(
                f"https://api.notion.com/v1/databases/{projects_db_id}/query",
                headers=headers,
                json=data,
                timeout=httpx.Timeout(5.0, read=15.0),
            )
            response.raise_for_status()
        except httpx.ReadTimeout:
            logger.error("Notion query timed out after all retries")
            return []
        except httpx.HTTPError as err:
            logger.error(f"Failed to fetch projects: {err!r}")
            return []

        projects = []
        js = response.json()
        for p in js.get("results", []):
            project_id = p["properties"]["Project ID"]["title"][0]["plain_text"]
            project_name = p["properties"]["Description"]["rich_text"][0]["plain_text"]
            project_owner =[owner["name"] for owner in p["properties"]["Owner"]["people"]]
            project_status = p["properties"]["Status"]["status"]["name"]
            project_priority = p["properties"]["Priority"]["select"]["name"]
            notion_page_id = p["id"]
            if "TEMPLATE" not in project_name:
                user_id = p["properties"]["PI Code"]["rollup"]["array"][0]["rich_text"][0][
                    "plain_text"
                ]
                project = Project(
                    id=project_id,
                    name=project_name,
                    user_id=user_id,
                    owner=project_owner,
                    status=project_status,
                    priority=project_priority,
                    notion_page_id=notion_page_id
                )
                projects.append(project)

        if projects:
            logger.info(f"{len(projects)} Notion projects found")
        else:
            logger.warning("No Notion projects found")
        return projects

    def get_project(
        self,
        projects_db_id: str,
        project_id: str | None = None,
        notion_page_id: str | None = None,
    ) -> Project | None:
        """
        Fetches a single project, either by its custom "Project ID" property
        or by its Notion page ID.

        You must pass exactly one of `project_id` or `notion_page_id`.

        :param projects_db_id: ID of the Notion Projects database to query.
        :type projects_db_id: str
        :param project_id: The value of the "Project ID" property to match.
        :type project_id: str or None
        :param notion_page_id: The Notion page ID of the project to retrieve.
        :type notion_page_id: str or None
        :return: A Project instance if found, otherwise None.
        :rtype: Project | None
        """
        logger.debug("Calling NotionWrapper.get_project method")
        headers = self._headers()

        if bool(project_id) == bool(notion_page_id):
            logger.error("Must provide exactly one of project_id or notion_page_id")
            return None

        if project_id:
            body = {
                "page_size": 1,
                "filter": {
                    "property": "Project ID",
                    "title": {"equals": project_id}
                }
            }
            url = f"https://api.notion.com/v1/databases/{projects_db_id}/query"
            request = lambda: self._post_with_retries(
                url, headers=headers, json=body,
                timeout=httpx.Timeout(5.0, read=15.0),
            )

        else:
            url = f"https://api.notion.com/v1/pages/{notion_page_id}"
            request = lambda: httpx.get(
                url, headers=headers,
                timeout=httpx.Timeout(5.0, read=15.0),
            )

        try:
            resp = request()
            resp.raise_for_status()
        except httpx.ReadTimeout:
            logger.error("Notion project lookup timed out after retries")
            return None
        except httpx.HTTPError as err:
            logger.error(f"Failed to fetch project: {err!r}")
            return None

        # Extract the page dict, whether from query or retrieve
        if project_id:
            results = resp.json().get("results", [])
            if not results:
                logger.warning(f"No project found with Project ID={project_id!r}")
                return None
            page = results[0]
        else:
            page = resp.json()

        props = page.get("properties", {})

        try:
            pid = project_id or props["Project ID"]["title"][0]["plain_text"]
            name = props["Description"]["rich_text"][0]["plain_text"]
            owner = [u["name"] for u in props["Owner"]["people"]]
            status = props["Status"]["status"]["name"]
            priority = props["Priority"]["select"]["name"]
            user_id = props["PI Code"]["rollup"]["array"][0]["rich_text"][0]["plain_text"]
            nid = page["id"]
        except (KeyError, IndexError) as e:
            logger.error(f"Malformed project properties on page {nid!r}: {e!r}")
            return None

        project = Project(
            id=pid,
            name=name,
            user_id=user_id,
            owner=owner,
            status=status,
            priority=priority,
            notion_page_id=nid
        )

        logger.info(f"Notion project loaded: {pid!r} → page {nid}")
        return project

    def get_all_tasks(self, tasks_db_id: str, projects_db_id: str) -> list:
        """
        Fetches all tasks from the Notion Tasks database, handling pagination,
        timeout and retries.

        :param tasks_db_id: ID of the Notion Tasks database to query.
        :type tasks_db_id: str
        :param projects_db_id: ID of the Notion Projects database to query.
        :type projects_db_id: str
        :return: A list of Task instances for every task in the database.
        :rtype: list
        """
        logger.debug("Calling NotionWrapper.get_all_tasks method")
        headers = self._headers()
        tasks: list = []
        cursor: str | None = None

        while True:
            body: dict = {"page_size": 100}
            if cursor:
                body["start_cursor"] = cursor

            try:
                response = self._post_with_retries(
                    f"https://api.notion.com/v1/databases/{tasks_db_id}/query",
                    headers=headers,
                    json=body,
                    timeout=httpx.Timeout(5.0, read=15.0),
                )
                response.raise_for_status()
            except httpx.ReadTimeout:
                logger.error("Notion tasks query timed out after all retries")
                return []
            except httpx.HTTPError as err:
                logger.error(f"Failed to fetch tasks: {err!r}")
                return []

            js = response.json()
            for t in js.get("results", []):
                task_name = t["properties"]["Task"]["title"][0]["plain_text"]
                # project = self.get_project(projects_db_id=projects_db_id,
                #                            notion_page_id=t["properties"]["Project"]["relation"][0]["id"])
                # task_project_id = project.id
                task_project_id = None
                if t["properties"]["Status"]["status"] is not None:
                    task_status = t["properties"]["Status"]["status"]["name"]
                else:
                    task_status = None
                if t["properties"]["Priority"]["select"] is not None:
                    task_priority = t["properties"]["Priority"]["select"]["name"]
                else:
                    task_priority = None
                assigned_to = [person["name"] for person in t["properties"]["Assigned to"]["people"]]
                notion_page_id = t["id"]
                task = Task(name=task_name,
                            project_id=task_project_id,
                            status=task_status,
                            priority=task_priority,
                            assigned_to=assigned_to,
                            notion_page_id=notion_page_id)
                tasks.append(task)

            if not js.get("has_more"):
                break
            cursor = js["next_cursor"]

        if tasks:
            logger.info(f"{len(tasks)} Notion tasks fetched")
        else:
            logger.warning("No Notion tasks found")

        return tasks

    def get_project_tasks(
        self,
        project_id: str,
        tasks_db_id: str,
        projects_db_id: str
    ) -> list:
        """
        Fetches all tasks linked to a specific project, handling pagination,
        timeouts, and retries.

        :param project_id: The custom Project ID whose tasks you want to fetch.
        :type project_id: str
        :param tasks_db_id: ID of the Notion Tasks database to query.
        :type tasks_db_id: str
        :param projects_db_id: ID of the Notion Projects database to query for the project.
        :type projects_db_id: str
        :return: A list of Task instances for every task linked to that project.
        :rtype: list
        """
        logger.debug("Calling NotionWrapper.get_tasks_for_project method")

        # 1) Find the Notion page UUID for this project
        project = self.get_project(projects_db_id=projects_db_id, project_id=project_id)
        if not project:
            logger.warning(f"Project {project_id!r} not found; no tasks to fetch")
            return []

        project_page_id = project.notion_page_id
        headers = self._headers()
        project_tasks: list = []
        cursor: str | None = None

        # 2) Query the Tasks DB with a relation.contains filter
        while True:
            body: dict = {
                "page_size": 100,
                "filter": {
                    "property": "Project",
                    "relation": {"contains": project_page_id}
                }
            }
            if cursor:
                body["start_cursor"] = cursor

            try:
                response = self._post_with_retries(
                    f"https://api.notion.com/v1/databases/{tasks_db_id}/query",
                    headers=headers,
                    json=body,
                    timeout=httpx.Timeout(5.0, read=15.0),
                )
                response.raise_for_status()
            except httpx.ReadTimeout:
                logger.error("Notion tasks-for-project query timed out after all retries")
                return []
            except httpx.HTTPError as err:
                logger.error(f"Failed to fetch tasks for project {project_id!r}: {err!r}")
                return []

            js = response.json()
            for t in js.get("results", []):
                props = t["properties"]

                name = props["Task"]["title"][0]["plain_text"]
                status = (props["Status"]["status"]["name"]
                        if props["Status"]["status"] else None)
                priority = (props["Priority"]["select"]["name"]
                            if props["Priority"]["select"] else None)
                assigned = [u["name"] for u in props["Assigned to"]["people"]]
                tid = t["id"]

                task = Task(
                    name=name,
                    project_id=project_id,
                    status=status,
                    priority=priority,
                    assigned_to=assigned,
                    notion_page_id=tid
                )
                project_tasks.append(task)

            if not js.get("has_more"):
                break
            cursor = js["next_cursor"]

        if project_tasks:
            logger.info(f"{len(project_tasks)} tasks fetched for project {project_id!r}")
        else:
            logger.warning(f"No tasks found for project {project_id!r}")

        return project_tasks

    def add_task_to_project(
        self,
        task: Task,
        tasks_db_id: str,
        projects_db_id: str
    ) -> Task | None:
        """
        Creates a new task in the Notion Tasks database and links it to the given project.

        :param task: A Task instance containing the fields to set on creation.
        :type task: Task
        :param tasks_db_id: ID of the Notion Tasks database where the new task will be created.
        :type tasks_db_id: str
        :param projects_db_id: ID of the Notion Projects database in which to look up the project's page ID.
        :type projects_db_id: str
        :return: The same Task instance, with its `notion_page_id` populated on success; or None on failure.
        :rtype: Task | None
        """
        logger.debug("Calling NotionWrapper.add_task_to_project method")

        project_id = task.project_id
        project = self.get_project(projects_db_id=projects_db_id, project_id=project_id)
        if not project:
            logger.error(f"Cannot add task: project {project_id!r} not found")
            return None
        project_page_id = project.notion_page_id

        props: dict = {
            "Task": {
                "title": [
                    {"type": "text", "text": {"content": task.name or ""}}
                ]
            },
            "Project": {
                "relation": [{"id": project_page_id}]
            }
        }
        if task.status:
            props["Status"] = {"status": {"name": task.status}}
        if task.priority:
            props["Priority"] = {"select": {"name": task.priority}}
        if task.assigned_to:
            pass
            # props["Assigned to"] = {
            #     "people": [{"id": uid} for uid in task.assigned_to]
            # }

        payload = {
            "parent": {"database_id": tasks_db_id},
            "properties": props
        }

        try:
            r = self._post_with_retries(
                "https://api.notion.com/v1/pages",
                headers=self._headers(),
                json=payload,
                timeout=httpx.Timeout(5.0, read=15.0),
            )
            r.raise_for_status()
        except httpx.ReadTimeout:
            logger.error("Timed out creating task for project %r", project_id)
            return None
        except httpx.HTTPError as err:
            logger.error(f"Failed to create task for project {project_id!r}: {err!r}")
            return None

        created = r.json()
        task.notion_page_id = created.get("id")
        logger.info(f'Added task "{task.name!r}" with ID {task.notion_page_id} to {project_id}')
        return task