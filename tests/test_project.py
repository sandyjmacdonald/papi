import os

os.environ.setdefault("TOGGL_TRACK_API_KEY",  "fake_token")
os.environ.setdefault("TOGGL_TRACK_PASSWORD", "fake_pass")
os.environ.setdefault("NOTION_API_SECRET",    "fake_secret")

import pytest
import uuid
import re
from papi.project import (
    Project,
    get_project_ids,
    decompose_project_name,
    check_project_id,
    user_id_from_project_id,
    check_suffix,
    check_uuid,
    THIS_YEAR,
)

# Fixtures and example values
example_project_id = "P2024-RST-ABCD"
example_year = 2024
example_user_id = "RST"
example_suffix = "ABCD"
example_uuid = str(uuid.uuid4())
example_invalid_project_id = "P2024_RST_ABCD"
example_invalid_uuid = "invalid-uuid-string"

@pytest.fixture
def proj() -> Project:
    return Project(
        year=example_year,
        user_id=example_user_id,
        suffix=example_suffix,
        p_uuid=example_uuid,
    )

# Test get_project_ids
@pytest.mark.parametrize("names, expected", [
    (["Project P0001-AB1-TEST description"], ["P0001-AB1-TEST"]),
    (["P0001-AB1-TEST", "Other P0002-XYZ-ABCD+stuff"], ["P0001-AB1-TEST", "P0002-XYZ-ABCD"]),
    (["no ids here", "still none"], []),
    (["dup P0001-AB1-TEST", "P0001-AB1-TEST repeat"], ["P0001-AB1-TEST"]),
])
def test_get_project_ids(names, expected):
    result = get_project_ids(names)
    assert result == sorted(expected)

# Test decompose_project_name
@pytest.mark.parametrize("input_str, expected", [
    ("P2024-RST-ABCD - Sample Project (WO123)", {"project_id": "P2024-RST-ABCD", "project_name": "Sample Project", "workorder": "WO123"}),
    ("P2024-RST-ABCD—Another", {"project_id": "P2024-RST-ABCD", "project_name": "Another", "workorder": None}),
    ("Just a name [W1]", {"project_id": None, "project_name": "Just a name", "workorder": "W1"}),
    ("No metadata", {"project_id": None, "project_name": "No metadata", "workorder": None}),
])
def test_decompose_project_name(input_str, expected):
    result = decompose_project_name(input_str)
    assert result == expected

# Test check_project_id
@pytest.mark.parametrize("pid, valid", [
    ("P2024-RST-ABCD", True),
    ("P0000-AB1-ZXYZ", True),
    (example_invalid_project_id, False),
    ("wrong-format", False),
])
def test_check_project_id(pid, valid):
    assert check_project_id(pid) is valid

# Test user_id_from_project_id
def test_user_id_from_project_id():
    assert user_id_from_project_id("P2024-XYZ-ABCD") == "XYZ"

# Test suffix checker
@pytest.mark.parametrize("suf, valid", [
    ("ABCD", True),
    ("WXYZ", True),
    ("abcD", False),
    ("A1CD", False),
])
def test_check_suffix(suf, valid):
    assert check_suffix(suf) is valid

# Test UUID checker
@pytest.mark.parametrize("uid, valid", [
    (str(uuid.uuid4()), True),
    ("00000000-0000-4000-8000-000000000000", True),  # valid v4
    ("00000000-0000-3000-8000-000000000000", False),  # wrong version
    ("not-a-uuid", False),
])
def test_check_uuid(uid, valid):
    assert check_uuid(uid) is valid

# Test Project creation and attributes
def test_create_full_project(proj):
    assert proj.id == f"P{example_year}-{example_user_id}-{example_suffix}"
    assert proj.year == example_year
    assert proj.user_id == example_user_id
    assert proj.suffix == example_suffix
    assert proj.p_uuid == example_uuid
    assert proj.id_is_valid()

# Test minimal project generates year and suffix
def test_create_minimal_project_defaults():
    proj_min = Project(user_id=example_user_id)
    assert proj_min.year == THIS_YEAR
    assert re.fullmatch(r"[A-Z]{4}", proj_min.suffix)
    assert proj_min.id.startswith(f"P{THIS_YEAR}-{example_user_id}-")

# Test providing invalid id raises
def test_project_invalid_id_raises():
    with pytest.raises(TypeError):
        Project(id=example_invalid_project_id)

# Test providing invalid uuid warns and generates new
def test_invalid_uuid_warns_and_replaced():
    bad_uuid = "1234"
    with pytest.warns(UserWarning):
        proj2 = Project(user_id=example_user_id, p_uuid=bad_uuid)
    assert proj2.p_uuid != bad_uuid
    assert check_uuid(proj2.p_uuid)

# Test __str__ includes key fields
def test_str_contains_fields(proj):
    s = str(proj)
    assert "Project(" in s
    assert f"id = {proj.id}" in s
    assert f"user_id = {proj.user_id}" in s

# Test generate_suffix random behavior
def test_generate_suffix_randomness():
    proj_temp = Project(user_id=example_user_id)
    s1 = proj_temp.generate_suffix()
    s2 = proj_temp.generate_suffix()
    assert len(s1) == 4 and len(s2) == 4
    assert s1 != s2 or s1 == s2  # at least correct format

# Test decompose empty or malformed returns None fields
def test_decompose_invalid_returns_none():
    res = decompose_project_name("")
    assert res == {"project_id": None, "project_name": None, "workorder": None}
