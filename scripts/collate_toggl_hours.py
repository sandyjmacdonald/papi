import argparse
import pendulum
from papi.wrappers import TogglTrackWrapper
from papi import config

def main():
    """Main function of collate-toggl-hours script"""

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

    # Set up Toggl Track API wrapper
    #
    # NOTE: you must have added Toggl Track API key and password, with
    # variable names below to .env file in this directory
    toggl_api_key = config["TOGGL_TRACK_API_KEY"]
    toggl_api_password = config["TOGGL_TRACK_PASSWORD"]
    toggl = TogglTrackWrapper(toggl_api_key, toggl_api_password)

    # Tell wrapper which workspace to set as default
    toggl_workspace = config["TOGGL_TRACK_WORKSPACE"]
    toggl.set_default_workspace(toggl_workspace)
    toggl.set_me()

    # Get tracked hours and tracked project IDs/names
    tracked_hours = toggl.get_user_hours(start_time=start_time, end_time=end_time)
    projects = {p["id"]: p["name"] for p in toggl.get_user_projects() if p["id"] in tracked_hours}

    output = args.output

    if output:
        # If output filename provided, write to file
        with open(output, "w") as out:
            for t in tracked_hours:
                out.write(f"{projects[t]}\t{tracked_hours[t]}\n")
    else:
        # Otherwise, print out project names and tracked hours to stdout
        for t in tracked_hours:
            print(f"{projects[t]}\t{tracked_hours[t]}")

if __name__ == "__main__":
    main()