import os

os.environ.setdefault("TOGGL_TRACK_API_KEY",  "fake_token")
os.environ.setdefault("TOGGL_TRACK_PASSWORD", "fake_pass")
os.environ.setdefault("NOTION_API_SECRET",    "fake_secret")

import pytest
import re
import uuid
from papi.task import Task  # adjust module path if needed

# Fixture for a default Task
@pytest.fixture
def default_task():
    return Task()

# Fixture for a fully specified Task with random Notion page ID
@pytest.fixture
def full_task():
    random_uuid = uuid.uuid4().hex  # 32-character lowercase hex string
    return Task(
        name="Test Task",
        project_id="P2024-XYZ-ABCD",
        status="In progress",
        priority="Urgent",
        assigned_to="Alice",
        notion_page_id=random_uuid,
    )

# Test initialization defaults
def test_default_initialization(default_task):
    t = default_task
    assert t.name is None
    assert t.project_id is None
    assert t.status is None
    assert t.priority == "Standard"
    assert t.assigned_to is None
    assert t.notion_page_id is None

# Test full initialization
def test_full_initialization(full_task):
    t = full_task
    assert t.name == "Test Task"
    assert t.project_id == "P2024-XYZ-ABCD"
    assert t.status == "In progress"
    assert t.priority == "Urgent"
    assert t.assigned_to == "Alice"
    # Notion page ID should be the randomly generated UUID
    assert re.fullmatch(r"[0-9a-f]{32}", t.notion_page_id)

# Test __str__ output contains all fields
@pytest.mark.parametrize("name, project_id, status, priority, assigned_to, notion_page_id", [
    ("Task1", "P0001-AB1-TEST", "Not started", "Low", "Bob", uuid.uuid4().hex),
    (None, None, None, "Standard", None, None),
])
def test_str_includes_fields(name, project_id, status, priority, assigned_to, notion_page_id):
    t = Task(
        name=name,
        project_id=project_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        notion_page_id=notion_page_id,
    )
    s = str(t)
    # Check that each attribute appears in the __str__ output
    assert f"name = {name}" in s
    assert f"project_id = {project_id}" in s
    assert f"status = {status}" in s
    assert f"priority = {priority}" in s
    assert f"assigned_to = {assigned_to}" in s
    assert f"notion_page_id = {notion_page_id}" in s

# Test Notion page ID format enforcement using the full_task fixture
def test_notion_page_id_uuid_format(full_task):
    t = full_task
    # Must be 32 lowercase hex characters
    assert re.fullmatch(r"[0-9a-f]{32}", t.notion_page_id)

# Test that Task conforms to Protocol at runtime
def test_runtime_protocol_conformance():
    t = Task(name="x")
    assert isinstance(t, Task)  # runtime checkable Protocol

# Test that an unrelated object is not instance of Task
class NotATask:
    pass

def test_non_protocol_not_instance():
    obj = NotATask()
    # Protocol is structural, so every object *is* an instance
    assert isinstance(obj, Task)
