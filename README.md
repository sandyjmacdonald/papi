PAPI is an API for managing projects.

<img src="https://imgur.com/lprJ3mP.jpg" alt="HAHA BUSINESS meme" height="250">

It has functionality for creating User and Project instances, storing users in a TinyDB database, and generating project IDs in the format we use in the Data Science group (at the Bioscience Technology Facility at the University of York). It also has wrappers for Asana and Toggl Track, two tools we use for project management and time tracking, respectively.

Much of the functionality is tailor-made to the way we manage projects in our group, but make of it what you will!

## Installation

The simplest way to install this is to do as follows:

```
pip install papi-projects
```

You can also install the Poetry packaging and dependency tool and then clone this repository and install with poetry, as follows:

```
pipx install poetry
git clone https://github.com/sandyjmacdonald/papi
cd papi
poetry install
```

## Environment variables

The Asana and Toggl Track wrappers expect several environment variables for API keys, etc. and the best way to do this is with a .env file that can be loaded via the Python dotenv library straight into your script. The CLI scripts provided also expect these variables to be in a .env file.

The .env file should look as follows:

```
# Asana config:
ASANA_API_KEY="YOURAPIKEY"
ASANA_PASSWORD=""
ASANA_WORKSPACE="myworkspace"
ASANA_TEAM="My Team Name"

# toggl track config:
TOGGL_TRACK_API_KEY="YOURAPIKEY"
TOGGL_TRACK_PASSWORD="api_token"
TOGGL_TRACK_WORKSPACE="My Workspace Name"
```

The `ASANA_PASSWORD` and `TOGGL_TRACK_PASSWORD` values can be left as above, the remaining ones should be replaced with the correct values from your Asana and Toggl Track accounts.

This .env file can either be put in your working directory or in the top-level papi module folder wherever it is installed.

Alternatively, these values can be hard-coded in your scripts, but this is not advised and will not work with the CLI scripts provided.

## CLI scripts

Two convenience CLI scripts are provided for common Toggl Track tasks. They are:

## create-toggl-project

This script creates a project ID if necessary, and adds the project to your Toggl Track:

```
usage: create-toggl-project [-h] [-u USER_ID] [-g GRANT_CODE] [-n NAME] [-p PROJECT_ID]

options:
  -h, --help            show this help message and exit
  -u USER_ID, --user_id USER_ID
                        three-letter user ID, e.g. CRD
  -g GRANT_CODE, --grant_code GRANT_CODE
                        grant code, e.g. R12345
  -n NAME, --name NAME  short project name, e.g. 'RNA-seq analysis'
  -p PROJECT_ID, --project_id PROJECT_ID
                        full project ID, e.g. P2024-ABC-DEFG, if already generated
```

Ideally, a three-character user ID, grant code, and short project name will be provided, and PAPI will generate the project ID, e.g.

```
create-toggl-project -u CRD -g R12345 -n 'Such project. Wow.'
```

If a project ID has already been created, then it can be provided via the `-p` argument and the user ID is not necessary, e.g.

```
create-toggl-project -p P2024-CRD-ABCD -g R12345 -n 'Such project. Wow.'
```

The grant code (`-g`) and name (`-n`) are not required, but either a project ID (`-p`) or user ID (`-u`) _is_ necessary.

## collate-toggl-hours

This script collates and returns your Toggl Track hours tracked over a specified time period:

```
usage: collate-toggl-hours [-h] -s START [-e END] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  -s START, --start START
                        start date in YYYY-MM-DD format
  -e END, --end END     end date in YYYY-MM-DD format, if none supplied then end date is now
  -o OUTPUT, --output OUTPUT
                        output TSV filename, omit to write to stdout
```

This script collates your tracked hours for any projects worked during a given time period and return the project name and decimal number of hours in tab-separated format.

If an output filename is provided, then the resulting hours are saved to that file, otherwise they are printed to stdout.

If no end date (`-e`) is provided, then the end date is the current time/date.

To collate your hours worked in August 2024:

```
collate-toggl-hours -s 2024-08-01 -e 2024-08-31 -o august-2024-hours.tsv
```