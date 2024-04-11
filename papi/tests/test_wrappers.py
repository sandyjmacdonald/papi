import pytest
import httpx
import json
from papi.wrappers import AsanaWrapper
from papi.mocks import (
    MOCK_ASANA_API_KEY,
    MOCK_ASANA_PASSWORD,
    mock_me_response,
    mock_teams_response,
    mock_templates_response,
    mock_asana_workspace_name,
    mock_asana_workspace_id,
    MOCK_TOGGL_TRACK_API_KEY,
    MOCK_TOGGL_TRACK_PASSWORD,
)
from papi.project import Project

mock_my_id = mock_me_response["data"]["gid"]

mock_team_id = mock_teams_response["data"][0]["gid"]
mock_team_name = mock_teams_response["data"][0]["name"]


def handler(request):
    print(request.url)
    if request.url == "https://app.asana.com/api/1.0/users/me":
        return httpx.Response(200, json=mock_me_response)
    elif str(request.url).startswith(
        f"https://app.asana.com/api/1.0/users/{mock_my_id}/teams"
    ):
        return httpx.Response(200, json=mock_teams_response)
    elif (
        request.url
        == f"https://app.asana.com/api/1.0/teams/{mock_team_id}/project_templates"
    ):
        return httpx.Response(200, json=mock_templates_response)


class MockAsanaWrapper(AsanaWrapper):
    def connect(self) -> httpx.Client:
        transport = httpx.MockTransport(handler)
        auth = httpx.BasicAuth(username=self.api_token, password=self.password)
        self.client = httpx.Client(transport=transport, auth=auth)
        return self.client


@pytest.fixture()
def asana() -> MockAsanaWrapper:
    return MockAsanaWrapper(MOCK_ASANA_API_KEY, MOCK_ASANA_PASSWORD)


def test_get_me(asana):
    me = asana.get_me()
    assert me == mock_me_response["data"]


def test_set_me(asana):
    asana.set_me()
    assert asana.my_id is not None
    assert asana.workspaces is not None


def test_get_teams(asana):
    workspace_id = asana.set_default_workspace(mock_asana_workspace_name)
    teams = asana.get_teams(workspace_id)
    assert teams == mock_teams_response["data"]


def test_set_teams(asana):
    asana.set_teams(mock_asana_workspace_id)
    assert asana.teams is not None


def test_get_team_id_by_name(asana):
    with pytest.raises(AttributeError):
        asana.get_team_id_by_name(mock_team_name)
    asana.set_teams(mock_asana_workspace_id)
    assert asana.get_team_id_by_name(mock_team_name) == mock_team_id


def test_set_default_team(asana):
    asana.set_teams(mock_asana_workspace_id)
    asana.set_default_team(mock_team_name)
    assert asana.default_team_id == mock_team_id


example_year = 2024
example_user_id = "RST"
example_suffix = "ABCD"
example_uuid = "2c173903-3b1c-4967-9a70-8f3a4607c06c"

proj = Project(
    year=example_year,
    user_id=example_user_id,
    suffix=example_suffix,
    p_uuid=example_uuid,
)


def test_get_templates(asana):
    templates = asana.get_templates(mock_team_id)
    assert templates == mock_templates_response["data"]


def test_create_project(asana):
    with pytest.raises(TypeError):
        asana.create_project("foo", mock_asana_workspace_id, mock_team_id)
    asana.create_project(proj, mock_asana_workspace_id, mock_team_id)
