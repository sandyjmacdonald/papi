import random
import logging

logger = logging.getLogger(__name__)

def random_number(length):
    return "".join([str(random.randint(1, 9)) for i in range(length)])


def random_hex(length):
    chars = "0123456789abcdef"
    return "".join([str(random.choice(chars)) for i in range(length)])


def get_mock_asana_api_key():
    api_key = (
        f"{random_number(1)}/{random_number(16)}/{random_number(16)}:{random_hex(32)}"
    )
    return api_key


MOCK_ASANA_API_KEY = get_mock_asana_api_key()
MOCK_ASANA_PASSWORD = ""

mock_asana_my_id = random_number(16)
mock_asana_workspace_id = random_number(13)
mock_asana_team_id = random_number(16)

mock_me_response = {
    "data": {
        "gid": f"{mock_asana_my_id}",
        "email": "tobey.lambert@outlook.com",
        "name": "Tobey Lambert",
        "photo": {
            "image_21x21": "https://placehold.co/21x21.png",
            "image_27x27": "https://placehold.co/27x27.png",
            "image_36x36": "https://placehold.co/36x36.png",
            "image_60x60": "https://placehold.co/60x60.png",
            "image_128x128": "https://placehold.co/128x128.png",
        },
        "resource_type": "user",
        "workspaces": [
            {
                "gid": f"{mock_asana_workspace_id}",
                "name": "myworkspace",
                "resource_type": "workspace",
            }
        ],
    }
}

mock_asana_workspace_name = mock_me_response["data"]["workspaces"][0]["name"]
mock_asana_workspace_id = mock_me_response["data"]["workspaces"][0]["gid"]

mock_teams_response = {
    "data": [
        {
            "gid": f"{mock_asana_team_id}",
            "name": "myteam",
            "resource_type": "team",
        }
    ]
}

mock_template_id = random_number(16)

mock_templates_response = {
    "data": [
        {
            "gid": mock_template_id,
            "name": "Mock Template",
            "resource_type": "project_template",
        }
    ]
}

MOCK_TOGGL_TRACK_API_KEY = random_hex(16)
MOCK_TOGGL_TRACK_PASSWORD = "api_token"
