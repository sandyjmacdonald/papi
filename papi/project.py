import pendulum
import string
import random
import re
import uuid
import warnings
import logging
from typing import Protocol, runtime_checkable
from papi.user import check_user_id

logger = logging.getLogger(__name__)

THIS_YEAR = pendulum.now().year


def get_project_ids(project_names) -> list:
    """This function takes a list of project names and finds and
    returns a list of project IDs.

    :param project_names: A list of project names.
    :type project_names: list
    :return: A list of project IDs.
    :rtype: list
    """
    logger.debug("Calling get_project_ids function")
    project_ids = []
    project_id_pattern = r"P[0-9]{4}-[A-Z]{2}[A-Z0-9]{1}-[A-Z]{4}"
    for project_name in project_names:
        match = re.search(project_id_pattern, project_name)
        if match:
            project_id = match.group()
            if project_id not in project_ids:
                project_ids.append(project_id)
    project_ids = sorted(project_ids)
    if len(project_ids):
        logger.info(f"{len(project_ids)} project IDs found")
    else:
        logger.info(f"No project IDs found")
    return project_ids

def decompose_project_name(project_name) -> dict:
    """This function takes a project name string and attempts
    to split out a project ID, name, and workorder.

    :param project_name: A project name string.
    :type project_name: str
    :return: A dictionary with the split-out parts.
    :rtype: dict
    """
    logger.debug("Calling decompose_project_name function")
    pattern = r"""
        ^
        (?P<project_id>P\d{4}-(?:[A-Z]{2}\d|[A-Z]{3})-[A-Z]{4})?
        (?:\s*[-–—]\s*|\s+)?
        (?P<project_name>[^()\[\]]+?)?
        (?:\s*[\(\[]\s*
            (?P<workorder>[^)\]]+)
        \s*[\)\]])?
        $
    """
    regex = re.compile(pattern, re.VERBOSE)
    match = regex.match(project_name)
    if match:
        project_id = match.group('project_id')
        project_name = match.group('project_name')
        workorder = match.group('workorder')
        return {
            "project_id": project_id,
            "project_name": project_name,
            "workorder": workorder
        }
    else:
        return {
            "project_id": None,
            "project_name": None,
            "workorder": None
        }

def check_project_id(id: str) -> bool:
    """Checks whether a project ID is correctly formed.

    :param id: Project ID to check.
    :type id: str
    :return: True/False for whether project ID is correctly formed.
    :rtype: bool
    """
    logger.debug("Calling check_project_id function")
    valid = False
    pattern = re.compile(r"^P[0-9]{4}-[A-Z]{2}[A-Z1-9]{1}-[A-Z]{4}$")
    if pattern.match(id):
        valid = True
        logger.info(f"Project ID '{id}' is valid")
    else:
        logger.info(f"Project ID '{id}' is not valid")
    return valid

def user_id_from_project_id(id: str) -> str:
    """Extracts a three-letter user ID from a project ID.

    :param id: Project ID to use.
    :type id: str
    :return: Three-letter user ID.
    :rtype: str
    """
    logger.debug("Calling user_id_from_project_id function")
    return id.split("-")[1]

def check_suffix(suffix: str) -> bool:
    """Checks whether a project suffix is correctly formed.

    :param suffix: Project suffix to check.
    :type suffix: str
    :return: True/False for whether project suffix is correctly formed.
    :rtype: bool
    """
    logger.debug("Calling check_suffix function")
    valid = False
    pattern = re.compile(r"^[A-Z]{4}$")
    if pattern.match(suffix):
        valid = True
        logger.info(f"Project suffix '{suffix}' is valid")
    else:
        logger.info(f"Project suffix '{suffix}' is not valid")
    return valid


def check_uuid(p_uuid: str) -> bool:
    """Checks whether a UUID is a valid version 4 UUID.

    :param p_uuid: The UUID to check.
    :type p_uuid: str
    :return: True/False for whether the UUID is valid.
    :rtype: bool
    """
    logger.debug("Calling check_uuid function")
    try:
        uuid_obj = uuid.UUID(p_uuid, version=4)
        logger.info(f"Project UUID '{p_uuid}' is valid")
    except ValueError:
        logger.error(f"Project UUID '{p_uuid}' is not valid")
        return False
    return str(uuid_obj) == p_uuid


@runtime_checkable
class Project(Protocol):
    """This class represents a project and all of its associated metadata.

    :param year: Year associated with the project. If no year is supplied, then the current
        year will be used.
    :type year: int, optional
    :param user_id: User ID associated with project. Must be a valid user ID, i.e. either
        3 uppercase alphabetical initials, or 2 uppercase alphabetical initials followed
        by a positive integer number.
    :type user_id: str, optional
    :param suffix: Project suffix; a 4-character, random, uppercase, alphabetical suffix.
        If not supplied, then this will be auto-generated.
    :type suffix: str, optional
    :param id: Fully-formed project ID that can be supplied directly, assuming it is valid.
        A valid project ID is of the form P2024-ABC-WXYZ where 2024 is the year associated
        with the project, ABC is a valid 3-character user ID, and WXYZ is a valid 4-character
        alphabetical suffix.
    :type id: str, optional
    :param p_uuid: A valid version 4 UUID that can be supplied directly. If not supplied, then
        this will be auto-generated.
    :type p_uuid: str, optional
    :param name: A short, descriptive project name, e.g. "Mouse long-read RNA-seq analysis".
        If not supplied, defaults to an empty string.
    :type name: str, optional
    :param workorder: Internal work order number or code associated with the project.
        If not supplied, defaults to None.
    :type workorder: str, optional
    :param created_at: Timestamp when the project was created.
        If not supplied, defaults to None.
    :type created_at: datetime or str, optional
    :param modified_at: Timestamp when the project was last modified.
        If not supplied, defaults to None.
    :type modified_at: datetime or str, optional
    :param status: Current status of the project, matching the Notion Status options
        (e.g. "Not Started", "In Progress", "On Hold", "Completed").
    :type status: str, optional
    :param priority: Project priority level, matching the Notion Priority options
        (e.g. "Low", "Medium", "High", "Critical").
    :type priority: str, optional
    :param owner: List of owners of the project.
        If not supplied, defaults to None.
    :type owner: list[str], optional
    :param notion_page_id: The internal Notion page UUID for this project record.
        If not supplied, defaults to None.
    :type notion_page_id: str, optional
    :raises TypeError: If the fully-formed project ID `id` is malformed.
    """

    def __init__(
        self,
        year: int = THIS_YEAR,
        user_id: str = None,
        suffix: str = None,
        id: str = None,
        p_uuid: str = None,
        name: str = "",
        workorder: str = None,
        created_at = None,
        modified_at = None,
        status: str = None,
        priority: str = None,
        owner: list = None,
        tasks: list = None,
        notion_page_id: str = None
    ) -> None:
        """Constructor method"""
        logger.debug("Creating Project instance")
        self.year = year
        self.user_id = user_id
        self.workorder = workorder
        self.name = name
        self.created_at = created_at
        self.modified_at = modified_at
        self.status = status
        self.priority = priority
        self.owner = owner
        self.tasks = tasks
        self.notion_page_id = notion_page_id
        if suffix is not None:
            self.suffix = suffix
        else:
            self.generate_suffix()
        if id is not None and check_project_id(id):
            self.id = id
            self.year = int(id[1:5])
            self.user_id = id.split("-")[1]
            self.suffix = id.split("-")[2]
        elif (
            isinstance(year, int)
            and check_user_id(user_id)
            and check_suffix(self.suffix)
        ):
            self.id = f"P{self.year}-{self.user_id}-{self.suffix}"
        else:
            raise TypeError(
                f"ID '{id}' is incorrectly formed, must similar to P2024-ABC-DEFG or P2024-AB1-DEFG"
            )
        if p_uuid is not None and check_uuid(p_uuid):
            self.p_uuid = p_uuid
        elif p_uuid is not None and not check_uuid(p_uuid):
            self.p_uuid = str(uuid.uuid4())
            warnings.warn(
                "UUID provided is not valid UUID version 4, generating one instead..."
            )
        else:
            self.p_uuid = str(uuid.uuid4())
        logger.info(f"Project '{self.id}' instance created")

    def __str__(self) -> str:
        """Machine-readable representation of class..

        :return: basic Project() attrs.
        :rtype: str
        """
        logger.debug("Calling Project.__str__ method")
        return (
            f"Project(\n"
            f"    id = {self.id},\n"
            f"    name = {self.name},\n"
            f"    year = {self.year},\n"
            f"    user_id = {self.user_id},\n"
            f"    priority = {self.priority}\n"
            f"    status = {self.status}\n"
            f"    owner = {self.owner}\n"
            f"    notion_page_id = {self.notion_page_id}\n"
            f")"
        )

    def generate_suffix(self) -> str:
        """Generates a 4-character, uppercase, alphabetical suffix for a project, and
        sets the suffix.

        :return: Project suffix.
        :rtype: str
        """
        logger.debug("Calling Project.generate_suffix method")
        letters = string.ascii_uppercase
        suffix = "".join(random.choice(letters) for i in range(4))
        self.suffix = suffix
        return self.suffix

    def id_is_valid(self) -> bool:
        """Checks whether a project ID is valid, i.e. correctly-formed.

        :return: True/False for whether the project ID is valid.
        :rtype: bool
        """
        logger.debug("Calling Project.id_is_valid method")
        return check_project_id(self.id)
