import argparse
import pendulum
import warnings
from papi.wrappers import TogglTrackWrapper, NotionWrapper
from papi import config
from papi.project import get_project_ids, check_project_id

from decimal import Decimal, ROUND_UP

def initialise_toggl(toggl_api_key, toggl_workspace):
    """Initialises the TogglTrackWrapper.

    :param toggl_api_key: A user's Toggl Track API key.
    :type toggl_api_key: str
    :param toggl_workspace: The name of the Toggl Track workspace.
    :type toggl_workspace: str
    :return: An initialised TogglTrackWrapper.
    :rtype: TogglTrackWrapper
    """
    toggl_api_password = config["TOGGL_TRACK_PASSWORD"]
    toggl = TogglTrackWrapper(toggl_api_key, toggl_api_password)
    toggl.set_default_workspace(toggl_workspace)
    toggl.set_me()
    return toggl

def calculate_cost(hours: float, hourly_rate: float) -> float:
    """Calculates a properly-rounded cost given hours and an hourly rate.

    :param hours: A number of hours, e.g. 1.5 for one and a half hours.
    :type hours: float
    :param hourly_rate: An hourly rate to charge.
    :type hourly_rate: float
    :return: A properly-rounded (note: rounded up) cost to charge.
    :rtype: float
    """
    cost = Decimal(hours * hourly_rate)
    cost_rounded = cost.quantize(Decimal("0.01"), rounding=ROUND_UP)
    return cost_rounded

def get_toggl_hours(start_time, end_time, toggl):
    """Get the tracked hours between a start time and end time from an
    initialised TogglTrackWrapper instance.

    :param start_time: A start time, e.g. 2025-11-01
    :type start_time: str
    :param end_time: An end time, e.g. 2025-11-31
    :type end_time: str
    :param toggl: An initialised TogglTrackWrapper instance.
    :type toggl: TogglTrackWrapper
    :return: A dicitonary of projects and tracked hours.
    :rtype: dict
    """
    tracked_hours = toggl.get_user_hours(start_time=start_time, end_time=end_time)
    projects = {p["id"]: p["name"] for p in toggl.get_user_projects() if p["id"] in tracked_hours}
    hours_per_project = [(projects[t], tracked_hours[t]) for t in tracked_hours]
    hours_dict = {}
    for i, p in enumerate(hours_per_project):
        project_id = get_project_ids([p[0]])
        if len(project_id):
            project_id = project_id[0]
            hours_dict[project_id] = hours_per_project[i][1]
        else:
            hours_dict[p[0]] = hours_per_project[i][1]
    return hours_dict

def main():
    """Main function of generate-timesheet script"""

    # Set up argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--start", type=str, help="start date in YYYY-MM-DD format", required=True
    )
    parser.add_argument(
        "-e", "--end", type=str, help="end date in YYYY-MM-DD format, if none supplied then end date is now", default=False
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="output TSV filename, omit to write to stdout",
        default=False,
    )
    args = parser.parse_args()

    # Set up start/end date
    start_date = args.start
    start_time = pendulum.parse(start_date).to_rfc3339_string()
    end_date = args.end
    if not end_date:
        end_time = pendulum.now().to_rfc3339_string()
    else:
        end_time = pendulum.parse(end_date).to_rfc3339_string()

    # Check that start time is not more than 3 months ago
    if pendulum.now() < pendulum.parse(start_date).add(months=3):
        toggl_api_key = config["TOGGL_TRACK_API_KEY"]
        toggl_workspace = config["TOGGL_TRACK_WORKSPACE"]
        toggl = initialise_toggl(toggl_api_key, toggl_workspace)

        hours_dict = get_toggl_hours(start_time, end_time, toggl)

        notion_api_secret = config["NOTION_API_SECRET"]
        notion_clients_db = config["NOTION_CLIENTS_DB"]
        notion_projects_db = config["NOTION_PROJECTS_DB"]
        notion_workorders_db = config["NOTION_WORKORDERS_DB"]
        notion = NotionWrapper(notion_api_secret)

        project_ids = hours_dict.keys()
        for project_id in project_ids:
            if check_project_id(project_id):
                project = notion.get_project(notion_projects_db, project_id, workorders_db_id=notion_workorders_db)
                workorder_id = project.workorder
                if workorder_id is not None:
                    workorder = notion.get_workorder(workorders_db_id=notion_workorders_db, workorder_id=workorder_id)
                    if workorder.is_complete():
                        hours = float(hours_dict[project_id])
                        print(
                            f"{workorder.id}\t"
                            f"{project_id}\t"
                            f"{workorder.payment_type}\t"
                            f"{workorder.costing_rate}\t"
                            f"{workorder.hourly_rate}\t"
                            f"{hours}\t"
                            f"{calculate_cost(hours, workorder.hourly_rate)}\t"
                            f"{project.name}\t"
                            f"{project.id}: {project.name}"
                        )
    else:
        warnings.warn("Start time must not be more than 3 months ago!")

if __name__ == "__main__":
    main()
