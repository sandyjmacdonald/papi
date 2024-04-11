import pytest
import os
import json
from papi.user import UserDB, user_name_to_user_id, check_user_id
from tinydb import TinyDB, Query

working_dir = os.getcwd()
test_user_db = f"{working_dir}/papi/tests/test_userdb.json"

with open(test_user_db, "w") as out:
    out.write("""{
    "_default": {
        "1": {
            "email": "jasmith@dummymail.com",
            "user_id": "JAS",
            "user_name": "John Adam Smith"
        },
        "2": {
            "email": "jsmith@dummymail.com",
            "user_id": "JS1",
            "user_name": "James Smith"
        }
    }
}""")

with open(test_user_db, "r") as f:
    test_user_db_dict = json.load(f)

user_names = [
    test_user_db_dict["_default"][k]["user_name"]
    for k in test_user_db_dict["_default"].keys()
]

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


def test_user_name_to_user_id():
    for u in user_names:
        assert user_name_to_user_id(u) == "".join([w[0] for w in u.split()])


def test_check_user_id_valid() -> None:
    for valid_user_id in valid_user_ids:
        assert check_user_id(valid_user_id) is True


def test_check_user_id_invalid() -> None:
    for invalid_user_id in invalid_user_ids:
        assert check_user_id(invalid_user_id) is False


def test_create_new_userdb():
    new_user_db = "new_userdb.json"
    UserDB(new_user_db)
    assert os.path.exists(new_user_db)
    os.remove(new_user_db)


def test_create_existing_userdb(user_db):
    assert type(user_db.db) is TinyDB
    Users = Query()
    for u in user_names:
        result = user_db.db.search(Users.user_name == u)
        assert len(result) > 0


def test_open_default_userdb():
    user_db = UserDB()
    assert type(user_db.db) is TinyDB


def test_insert_user(user_db):
    for u in test_users:
        user_db.insert_user(u[0], email=u[1])
        Users = Query()
        result = user_db.db.search((Users.user_name == u[0]) & (Users.email == u[1]))
        assert len(result) > 0


def test_insert_existing_user(user_db):
    u = user_db.insert_user(user_names[0])
    inserted_user_id = user_db.db.get(doc_id=u)["user_id"]
    assert inserted_user_id != user_name_to_user_id(user_names[0])


def test_incorrect_name_length(user_db):
    with pytest.raises(ValueError):
        user_db.insert_user(incorrect_user_name)


def test_incorrect_email(user_db):
    with pytest.raises(ValueError):
        user_db.insert_user(test_users[0][0], email=incorrect_email)


def test_search_by_user_name(user_db):
    result = user_db.search_by_user_name(test_users[0][0])
    assert len(result) > 0


def test_search_by_user_id(user_db):
    user_id = "".join([w[0] for w in test_users[0][0].split()])
    result = user_db.search_by_user_id(user_id)
    assert len(result) > 0
