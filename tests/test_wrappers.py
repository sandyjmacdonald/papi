import os

# stub env before imports
os.environ.setdefault("TOGGL_TRACK_API_KEY",  "fake_token")
os.environ.setdefault("TOGGL_TRACK_PASSWORD", "fake_pass")
os.environ.setdefault("NOTION_API_SECRET",    "fake_secret")

import json
import uuid

import pytest
import httpx
import pendulum

from papi.wrappers import TogglTrackWrapper, NotionWrapper
from papi.project import Project
from papi.task import Task
from papi.user import User

#
# ——— TogglTrackWrapper tests ———
#

MOCK_ME = {"id": 123, "fullname": "Jane Doe"}
MOCK_WORKSPACES = [
    {"id": "w1", "name": "Alpha"},
    {"id": "w2", "name": "Beta"},
]
now_iso = pendulum.now().to_iso8601_string()
MOCK_PROJECTS = [
    {"id": 101, "name": "P2024-ABC-TEST – Project One", "created_at": now_iso, "at": now_iso},
    {"id": 102, "name": "NoMatchProject",            "created_at": now_iso, "at": now_iso},
]
MOCK_TIME_ENTRIES = [
    {"pid": 101, "duration": 3600},
    {"pid": 101, "duration": 1800},
    {"pid": 999, "duration": 7200},
]

def toggl_handler(request):
    url = str(request.url)
    # project creation must be first, before the GET /projects handler
    if request.method == "POST" and "/projects" in url:
        return httpx.Response(200, json={"id": 555}, request=request)
    # now handle GETs
    if url.endswith("/me"):
        return httpx.Response(200, json=MOCK_ME, request=request)
    if url.endswith("/me/workspaces"):
        return httpx.Response(200, json=MOCK_WORKSPACES, request=request)
    if url.endswith("/me/projects"):
        return httpx.Response(200, json=MOCK_PROJECTS, request=request)
    if "/time_entries" in url:
        return httpx.Response(200, json=MOCK_TIME_ENTRIES, request=request)
    if "/workspaces/" in url and url.endswith("/projects"):
        return httpx.Response(200, json=MOCK_PROJECTS, request=request)
    raise RuntimeError(f"Unhandled Toggl URL: {url}")

class MockToggl(TogglTrackWrapper):
    def connect(self):
        transport = httpx.MockTransport(toggl_handler)
        self.client = httpx.Client(
            transport=transport,
            auth=httpx.BasicAuth(self.api_token, self.password),
        )
        return self.client

@pytest.fixture
def toggl():
    return MockToggl("fake_token", "fake_pass")

def test_get_user_hours_aggregation_and_warnings(toggl):
    with pytest.warns(UserWarning):
        assert toggl.get_user_hours() is None

    start = pendulum.now().subtract(hours=6).to_rfc3339_string()
    times = toggl.get_user_hours(start_time=start)
    assert pytest.approx(times[101], rel=1e-3) == 1.5
    assert pytest.approx(times[999], rel=1e-3) == 2.0

def test_check_project_exists_and_create_project(toggl):
    toggl.set_workspaces()
    toggl.set_default_workspace("Alpha")
    with pytest.raises(TypeError):
        toggl.create_project("notaproject", "w1")

    # Use a validly-formed project ID
    new_id = toggl.create_project(Project(id="P2024-ABC-DEFG", name="X"), "w1")
    assert new_id == 555

    none = toggl.create_project(Project(id="P2024-ABC-TEST", name="Whatever"), "w1")
    assert none is None

#
# ——— NotionWrapper tests ———
#

PAGE_UUID    = str(uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"))
USER_PAGE    = str(uuid.UUID("4b825dc6-8b6f-4c5f-bda6-1234567890ab"))
PROJECT_PAGE = str(uuid.uuid4())

NOTION_USERS_DB = {
    "results": [
        {
            "id": USER_PAGE,
            "properties": {
                "Code": {"rich_text":[{"plain_text":"XYZ"}]},
                "Name": {"title":[{"plain_text":"Zoe"}]},
                "Email": {"email":"zoe@example.com"},
            },
        }
    ]
}
NOTION_PROJ_DB = {
    "results": [
        {
            "id": PROJECT_PAGE,
            "properties": {
                "Project ID": {"title":[{"plain_text":"P2024-ABC-ONE"}]},
                "Description": {"rich_text":[{"plain_text":"One"}]},
                "Owner": {"people":[{"name":"Alice"}]},
                "Status": {"status":{"name":"Not Started"}},
                "Priority": {"select":{"name":"Medium"}},
                "PI Code": {"rollup":{"array":[{"rich_text":[{"plain_text":"ABC"}]}]}},
            },
        }
    ],
    "has_more": False
}

def mock_notion_get(url, headers=None, params=None, timeout=None):
    req = httpx.Request("GET", url, headers=headers)
    if url.endswith("/pages/tpl"):
        return httpx.Response(
            200,
            json={
                "properties": {
                    "A": {"type":"select","select":{"name":"foo"}},
                    "B": {"type":"multi_select","multi_select":[{"name":"bar"}]},
                }
            },
            request=req
        )
    if url.endswith("/blocks/tpl/children"):
        return httpx.Response(200, json={"results":[], "has_more":False}, request=req)
    raise RuntimeError(f"Unexpected GET {url}")

def mock_notion_post(url, headers=None, json=None, timeout=None):
    req = httpx.Request("POST", url, headers=headers, json=json)
    if url.endswith("/pages"):
        return httpx.Response(200, json={"id":PAGE_UUID}, request=req)
    if "/query" in url and "databases/users" in url:
        return httpx.Response(200, json=NOTION_USERS_DB, request=req)
    if "/query" in url and "databases/projects" in url:
        return httpx.Response(200, json=NOTION_PROJ_DB, request=req)
    if "/query" in url and "databases/tasks" in url:
        return httpx.Response(
            200,
            json={
                "results":[
                    {
                        "id":"t1",
                        "properties":{
                            "Task":{"title":[{"plain_text":"Do it"}]},
                            "Status":{"status":{"name":"In Progress"}},
                            "Priority":{"select":{"name":"High"}},
                            "Assigned to":{"people":[{"name":"Bob"}]},
                        }
                    }
                ],
                "has_more":False
            },
            request=req
        )

    if url.startswith(f"https://api.notion.com/v1/pages/{PAGE_UUID}"):
        return httpx.Response(200, json={}, request=req)

    raise RuntimeError(f"Unexpected POST {url}")

@pytest.fixture
def notion(monkeypatch):
    monkeypatch.setattr(httpx, "get",  mock_notion_get)
    monkeypatch.setattr(httpx, "post", mock_notion_post)
    monkeypatch.setattr(httpx, "patch", mock_notion_post)
    return NotionWrapper("fake_secret")

def test_fetch_and_clean_template(notion):
    props = notion._fetch_template_page("tpl")["properties"]
    assert "A" in props and "B" in props

def test_create_user_and_get_and_list_users(notion):
    u = User(user_name="Zoe", user_id="XYZ", email="zoe@example.com")
    pid = notion.create_user(u, clients_db_id="databases/users")
    assert pid == PAGE_UUID

    found = notion.get_user_page_id(clients_db_id="databases/users", user=u)
    assert found == USER_PAGE

    users = notion.get_users(clients_db_id="databases/users")
    assert len(users) == 1

def test_project_crud_and_queries(notion):
    proj = Project(id="P2024-XYZ-ONE", name="One", user_id="XYZ")
    assert notion.check_project_exists(proj, projects_db_id="databases/projects") is None

    created = notion.create_project(
        proj,
        user=User(user_name="Zoe Example", user_id="XYZ", email="zoe@example.com"),
        projects_db_id="databases/projects"
    )
    assert isinstance(created, Project)
    assert created.notion_page_id == PAGE_UUID

def test_tasks_fetch_and_add(notion):
    tasks = notion.get_all_tasks(tasks_db_id="databases/tasks", projects_db_id="databases/projects")
    assert len(tasks) == 1

    pts = notion.get_project_tasks("P2024-ABC-ONE", tasks_db_id="databases/tasks", projects_db_id="databases/projects")
    assert all(isinstance(t, Task) for t in pts)

    new_task = Task(name="New", project_id="P2024-ABC-ONE")
    added = notion.add_task_to_project(new_task, tasks_db_id="databases/tasks", projects_db_id="databases/projects")
    assert isinstance(added, Task)

    # with a missing project, should still return the Task (no exception)
    missing = notion.add_task_to_project(Task(name="X", project_id="NOPE"), tasks_db_id="databases/tasks", projects_db_id="databases/projects")
    assert isinstance(missing, Task)