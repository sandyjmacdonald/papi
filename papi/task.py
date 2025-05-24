import warnings
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

@runtime_checkable
class Task(Protocol):
    """This class represents a task and all of its associated metadata.

    :param name: A short, descriptive task name, e.g. "Sort gene annotations".
        If not supplied, defaults to None.
    :type name: str, optional
    :param project_id: The Project ID of the Project that this task belongs to.
        Should match an existing Project ID, defaults to None.
    :type project_id: str, optional
    :param status: The status of the task, matching one of your Notion Status options
        (e.g. "Not started", "In progress", "Completed"), defaults to None.
    :type status: str, optional
    :param priority: The priority level of the task, matching one of your Notion Select
        options (e.g. "Low", "Standard", "Urgent"), defaults to None.
    :type priority: str, optional
    :param assigned_to: The name of the person assigned to the task.
        Should correspond to a valid Notion user name, defaults to None.
    :type assigned_to: str, optional
    :param notion_page_id: The internal Notion page UUID for this task record.
    :type notion_page_id: str, optional
    """

    def __init__(
        self,
        name: str = None,
        project_id: str = None,
        status: str = None,
        priority: str = "Standard",
        assigned_to: str = None,
        notion_page_id: str = None
    ) -> None:
        """Constructor method"""
        logger.debug("Creating Task instance")
        self.name = name
        self.project_id = project_id
        self.status = status
        self.priority = priority
        self.assigned_to = assigned_to
        self.notion_page_id = notion_page_id

        logger.info(f"Task: '{self.name} ({self.project_id})' instance created")

    def __str__(self) -> str:
        """Machine-readable representation of class..

        :return: basic Task() attrs.
        :rtype: str
        """
        logger.debug("Calling Task.__str__ method")
        return (
            f"Task(\n"
            f"    name = {self.name},\n"
            f"    project_id = {self.project_id},\n"
            f"    status = {self.status},\n"
            f"    priority = {self.priority},\n"
            f"    assigned_to = {self.assigned_to},\n"
            f"    notion_page_id = {self.notion_page_id}\n"
            f")"
        )