import warnings
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

@runtime_checkable
class Workorder(Protocol):
    """This class represents a workorder and all of its associated metadata.

    :param id: The Workorder ID e.g. R123456.
        Often starts with R, M, or A depending on the workorder type.
    :type id: str, required
    :param user_id: The ID of the user to which the workorder belongs,
        defaults to None.
    :type user_id: str, optional
    :param funder: The funding source, e.g. Internal or BBSRC, defaults to None.
    :type funder: str, optional
    :param trac_type: TRAC type, e.g. Internal FEC, defaults to None.
    :type trac_type: str, optional
    :param project_location: e.g. Internal or External, defaults to None.
    :type project_location: str, optional
    :param costing_rate: Charity or FEC, defaults to None.
    :type costing_rate: str, optional
    :param payment_type: DI or DA, defaults to None.
    :type payment_type: str, optional
    :param hourly_rate: The hourly rate to charge, defaults to None.
    :type hourly_rate: float, optional
    :param notion_page_id: The internal Notion page UUID for this workorder.
    :type notion_page_id: str, optional
    """

    def __init__(
        self,
        id: str = None,
        user_id: str = None,
        funder: str = None,
        trac_type: str = None,
        project_location: str = None,
        costing_rate: str = None,
        payment_type: str = None,
        hourly_rate: float = None,
        notion_page_id: str = None
    ) -> None:
        """Constructor method"""
        logger.debug("Creating Workorder instance")
        self.id = id
        self.user_id = user_id
        self.funder = funder
        if trac_type is not None:
            self.trac_type = trac_type
            self.project_location, self.costing_rate = trac_type.split()
        else:
            self.project_location = project_location
            self.costing_rate = costing_rate
            self.trac_type = f"{project_location} {costing_rate}"
        self.payment_type = payment_type
        self.hourly_rate = hourly_rate
        self.notion_page_id = notion_page_id
        self.required_fields = [
            "id",
            "project_location",
            "costing_rate",
            "trac_type",
            "payment_type",
            "hourly_rate",
        ]

        logger.info(f"Workorder: '{self.id}' instance created")

    def __str__(self) -> str:
        """Machine-readable representation of class..

        :return: basic Workorder() attrs.
        :rtype: str
        """
        logger.debug("Calling Workorder.__str__ method")
        return (
            f"Workorder(\n"
            f"    id = {self.id},\n"
            f"    user_id = {self.user_id},\n"
            f"    funder = {self.funder},\n"
            f"    trac_type = {self.trac_type},\n"
            f"    project_location = {self.project_location},\n"
            f"    costing_rate = {self.costing_rate},\n"
            f"    payment_type = {self.payment_type},\n"
            f"    hourly_rate = {self.hourly_rate},\n"
            f"    notion_page_id = {self.notion_page_id}\n"
            f")"
        )

    def is_complete(self) -> bool:
        """Checks whether the workorder details are complete.

        :return: True/False as appropriate
        :rtype: bool
        """
        logger.debug("Calling Workorder.is_complete method")

        return all(getattr(self, field) is not None for field in self.required_fields)
