import re
import pendulum
from typing import Protocol, runtime_checkable
from tinydb import TinyDB, Query
from tinydb.operations import *


def user_name_to_user_id(user_name: str) -> str:
    """Generates a 3-character, uppercase, alphabetical user ID from a user name,
    e.g. John Adam Smith becomes JAS.

    :param user_name: A person's name.
    :type user_name: str
    :return: Three-character user ID.
    :rtype: str
    """
    user_name_parts = user_name.split()
    user_id = "".join([word[0] for word in user_name_parts]).upper()
    return user_id


def check_valid_email(email: str) -> bool:
    """Checks whether an email address string is correctly-formed, e.g.
    "ab.cooper@dummymail.com".

    :param email: Email address to check.
    :type email: str
    :return: True/False for whether the email is valid.
    :rtype: bool
    """
    valid_email = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    valid = valid_email.match(email)
    return valid


def check_user_id(user_id: str) -> bool:
    """Checks whether a user ID is correctly-formed, i.e. whether it is 3-characters
    long, consisting of either 3 uppercase letters, or 2 uppercase letters followed
    by a number.

    :param user_id: User ID to check.
    :type user_id: str
    :return: True/False for whether the user ID is valid.
    :rtype: bool
    """
    if not isinstance(user_id, str):
        return False
    else:
        valid = False
        pattern = re.compile(r"^[A-Z]{2}[A-Z0-9]{1}$")
        if pattern.match(user_id):
            valid = True
        return valid


@runtime_checkable
class User(Protocol):
    """This class represents a user, which consists of a user name, id,
    and optional email address.

    :param user_name: User name, e.g. John Smith.
    :type user_name: str
    :param email: Email address, defaults to None.
    :type email: str, optional
    :raises ValueError: If the name does not consist of either 2 or 3 parts, then
        a ValueError is raised.
    :raises ValueError: If the email address is not correctly formed, then a
        ValueError is raised.
    """

    def __init__(self, user_name: str, email: str = None):
        """Constructor method"""
        if len(user_name.split()) == 1 or len(user_name.split()) > 3:
            raise ValueError("Name must consist of two or three parts only")
        self.user_name = user_name
        if email is not None:
            valid_email = check_valid_email(email)
            if not valid_email:
                raise ValueError("Email address is malformed")
            self.email = email
        else:
            self.email = ""
        self.user_id = user_name_to_user_id(user_name)
        self.created_at = str(pendulum.now())

    def to_json(self):
        """Returns a user in JSON (dictionary) form.

        :return: JSON-formatted (i.e. dictionary) user.
        :rtype: dict
        """
        return {
            "user_name": self.user_name,
            "user_id": self.user_id,
            "email": self.email,
            "created_at": self.created_at,
        }


@runtime_checkable
class UserDB(Protocol):
    """This class represents a user database, which is a wrapper around a TinyDB
    database. The user database stores user IDs, names, and email addreses which
    are associated with projects.

    :param db_file: Path to a TinyDB json database file. If not supplied, then
        one will be created automatically as "userdb.json", defaults to None
    :type db_file: str, optional
    """

    def __init__(self, db_file: str = None) -> None:
        """Constructor method"""
        if db_file is not None:
            self.db = TinyDB(db_file, sort_keys=True, indent=4, separators=(",", ": "))
            self.db_file = db_file
        else:
            self.db_file = "userdb.json"
            self.db = TinyDB(
                self.db_file, sort_keys=True, indent=4, separators=(",", ": ")
            )

    def insert_user(self, user) -> User:
        """Inserts a user into the database, using a User instance.
        A non-clashing user ID will be added if necessary.

        :param user: A User instance.
        :type user: User
        :return: ID of the inserted user.
        :rtype: int
        """
        if len(user.user_name.split()) == 2:
            matches = self.check_matching_user_ids(user.user_id)
            if len(matches):
                matching_user_ids = [m["user_id"] for m in matches]
                highest_num = max([int(m[2]) for m in matching_user_ids])
                new_num = highest_num + 1
                user.user_id = f"{user.user_id}{new_num}"
            else:
                user.user_id = f"{user.user_id}1"
        elif len(user.user_name.split()) == 3:
            matches = self.check_matching_user_ids(user.user_id)
            if len(matches):
                first_last_initial = f"{user.user_id[0]}{user.user_id[-1]}"
                matches = self.check_matching_user_ids(first_last_initial)
                if len(matches):
                    matching_user_ids = [m["user_id"] for m in matches]
                    highest_num = max([int(m[2]) for m in matching_user_ids])
                    new_num = highest_num + 1
                    user.user_id = f"{first_last_initial}{new_num}"
                else:
                    user.user_id = f"{first_last_initial}1"
        self.db.insert(user.to_json())
        return user.user_id

    def search_by_user_name(self, user_name: str) -> list:
        """Searches the database using a supplied user name and returns matching
        documents.

        :param user_name: A person's name, e.g. John Adam Smith.
        :type user_name: str
        :return: A list of matching documents.
        :rtype: list
        """
        Users = Query()
        result = self.db.search(Users.user_name == user_name)
        return result

    def search_by_user_id(self, user_id: str) -> list:
        """Searches the database using a supplied user ID and returns matching
        documents.

        :param user_id: A user ID, e.g JAS or JS1.
        :type user_id: str
        :return: A list of matching documents.
        :rtype: list
        """
        Users = Query()
        result = self.db.search(Users.user_id == user_id)
        return result

    def check_matching_user_ids(self, user_id: str) -> list:
        """Checks for matching user IDs in the database and returns any matching
        documents. In contrast to the ``search_by_user_id`` functions, this searches
        2-letter user initials and those with a numerical suffix as well as 3-letter
        initials.

        :param user_id: A user ID, e.g JAS or JS1.
        :type user_id: str
        :return: A list of matching documents.
        :rtype: list
        """
        Users = Query()
        if user_id[-1].isnumeric() or len(user_id) == 2:
            result = self.db.search(Users.user_id.search(rf"^{user_id[0:2]}\d{{1}}"))
        else:
            result = self.db.search(Users.user_id == user_id)
        return result
