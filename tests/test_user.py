import os

# stub env before any papi imports
os.environ.setdefault("TOGGL_TRACK_API_KEY",  "fake_token")
os.environ.setdefault("TOGGL_TRACK_PASSWORD", "fake_pass")
os.environ.setdefault("NOTION_API_SECRET",    "fake_secret")

import pytest
import json
from tinydb import TinyDB, Query
from papi.user import UserDB, user_name_to_user_id, check_user_id, User

# Prepare a test JSON database file
working_dir = os.getcwd()
test_user_db = os.path.join(working_dir, "tests", "test_userdb.json")

# Initialize test DB content with two users
initial_data = {
    "_default": {
        "1": {"email": "jasmith@dummymail.com", "user_id": "JAS", "user_name": "John Adam Smith"},
        "2": {"email": "jsmith@dummymail.com", "user_id": "JS1", "user_name": "James Smith"}
    }
}
with open(test_user_db, "w") as out:
    json.dump(initial_data, out)

# Load fixture names
with open(test_user_db, "r") as f:
    db_dict = json.load(f)
user_names = [v["user_name"] for v in db_dict["_default"].values()]

# Additional users to insert
test_users = [
    ("Adam Brian Cooper", "ab.cooper@dummymail.com"),
    ("Angela Barbara Cartwright", "ab.cartwright@dummymail.com"),
    ("Andrew Baxter", "a.baxter@dummymail.com"),
    ("Alan Donald", "a.donald@dummymail.com"),
    ("Andrew Duncan", "a.duncan@dummymail.com"),
]

incorrect_user_name = "Alan Brian Charlie Donald"
incorrect_email = "ab.cooper@dummymail"

valid_user_ids = ["RST", "RT1"]
invalid_user_ids = ["RT12", "RSTU", "RT", 123]

@pytest.fixture()
def user_db() -> UserDB:
    return UserDB(test_user_db)

# Utility function tests

def test_user_name_to_user_id():
    for name in user_names:
        expected = "".join([word[0] for word in name.split()])
        assert user_name_to_user_id(name) == expected


def test_check_user_id_valid():
    for uid in valid_user_ids:
        assert check_user_id(uid)


def test_check_user_id_invalid():
    for uid in invalid_user_ids:
        assert not check_user_id(uid)

# DB creation/opening

def test_create_new_userdb(tmp_path):
    new_file = tmp_path / "new_userdb.json"
    UserDB(str(new_file))
    assert new_file.exists()


def test_open_existing_userdb(user_db):
    assert isinstance(user_db.db, TinyDB)
    Users = Query()
    for name in user_names:
        assert user_db.db.search(Users.user_name == name)

# insert_user tests

def test_insert_user(user_db):
    Users = Query()
    for name, email in test_users:
        u = User(user_name=name, user_id=None, email=email)
        new_uid = user_db.insert_user(u)
        recs = user_db.db.search(Users.user_id == new_uid)
        assert len(recs) == 1
        rec = recs[0]
        assert rec["user_name"] == name
        assert rec["email"] == email


def test_insert_existing_user_modifies_id(user_db):
    Users = Query()
    name = user_names[0]
    base_uid = user_name_to_user_id(name)
    u = User(user_name=name, user_id=None, email="dup@example.com")
    new_uid = user_db.insert_user(u)
    assert new_uid != base_uid
    recs = user_db.db.search(Users.user_id == new_uid)
    assert len(recs) == 1
    assert recs[0]["user_name"] == name

# validation errors

def test_incorrect_name_length(user_db):
    with pytest.raises(ValueError):
        u = User(user_name=incorrect_user_name, user_id=None, email="x@x.com")
        user_db.insert_user(u)


def test_incorrect_email(user_db):
    with pytest.raises(ValueError):
        u = User(user_name=test_users[0][0], user_id=None, email=incorrect_email)
        user_db.insert_user(u)

# search tests

def test_search_by_user_name(user_db):
    name = user_names[0]
    results = user_db.search_by_user_name(name)
    assert results and isinstance(results[0], dict)
    assert any(r.get("user_name") == name for r in results)


def test_search_by_user_id(user_db):
    uid = user_name_to_user_id(user_names[0])
    results = user_db.search_by_user_id(uid)
    assert results and isinstance(results[0], dict)
    assert any(r.get("user_id") == uid for r in results)
