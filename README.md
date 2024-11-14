PAPI is an API for managing projects.

<img src="https://imgur.com/lprJ3mP.jpg" alt="HAHA BUSINESS meme" height="250">

It has functionality for creating User and Project instances, storing users in a TinyDB database, and generating project IDs in the format we use in the Data Science group (at the Bioscience Technology Facility at the University of York). It also has wrappers for Asana and Notion, and Toggl Track, tools we use for project management and time tracking, respectively.

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

# Notion config
NOTION_API_SECRET = "YOURAPISECRET"
NOTION_CLIENTS_DB = "notionclientsdbid"
NOTION_PROJECTS_DB = "notionprojectsdbid"
```

The `ASANA_PASSWORD` and `TOGGL_TRACK_PASSWORD` values can be left as above, the remaining ones should be replaced with the correct values from your Notion, Asana, and Toggl Track accounts.

This .env file can either be put in your working directory or in the top-level papi module folder wherever it is installed.

Alternatively, these values can be hard-coded in your scripts, but this is not advised and will not work with the CLI scripts provided.

## CLI scripts

Convenience CLI scripts are provided for some common tasks. They are:

### create-toggl-project

This script creates a project ID if necessary, and adds the project to your Toggl Track:

```
usage: create-toggl-project [-h] [-u USER_ID] [-g GRANT_CODE] [-n NAME] [-p PROJECT_ID] [--enable-logging] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                            [--log-file LOG_FILE]

options:
  -h, --help            show this help message and exit
  -u USER_ID, --user_id USER_ID
                        three-letter user ID, e.g. JAS
  -g GRANT_CODE, --grant_code GRANT_CODE
                        grant code, e.g. R12345
  -n NAME, --name NAME  short project name, e.g. 'RNA-seq analysis'
  -p PROJECT_ID, --project_id PROJECT_ID
                        full project ID, e.g. P2024-JAS-ABCD, if already generated
  --enable-logging      enable logging output for the papi library
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set the logging level (default: INFO)
  --log-file LOG_FILE   path to a file where logs should be written
```

Ideally, a three-character user ID, grant code, and short project name will be provided, and PAPI will generate the project ID, e.g.

```
create-toggl-project -u JAS -g R12345 -n 'Such project. Wow.'
```

If a project ID has already been created, then it can be provided via the `-p` argument and the user ID is not necessary, e.g.

```
create-toggl-project -p P2024-JAS-ABCD -g R12345 -n 'Such project. Wow.'
```

The grant code (`-g`) and name (`-n`) are not required, but either a project ID (`-p`) or user ID (`-u`) _is_ necessary.

Logging can also be enabled at various levels of detail, and logs can be saved to a file.

### collate-toggl-hours

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

### create-notion-project

This script creates a project ID if necessary, and adds the project to the Notion projects database:

```
usage: create-notion-project [-h] [-u USER_ID] [-v USER_NAME] [-n NAME] [-p PROJECT_ID] [--enable-logging] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                             [--log-file LOG_FILE]

options:
  -h, --help            show this help message and exit
  -u USER_ID, --user_id USER_ID
                        three-letter user (client) ID, e.g. JAS
  -v USER_NAME, --user_name USER_NAME
                        user (client) name, e.g. John Andrew Smith
  -n NAME, --name NAME  short project name, e.g. 'RNA-seq analysis', project ID will be auto-generated
  -p PROJECT_ID, --project_id PROJECT_ID
                        full project ID, e.g. P2024-JAS-ABCD, if already generated
  --enable-logging      enable logging output for the papi library
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set the logging level (default: INFO)
  --log-file LOG_FILE   path to a file where logs should be written
```

Similar to the `create-toggl-project` script, you can simply provide a three-character user ID and a short project name, and PAPI will generate the project ID, e.g.

```
create-notion-project -u JAS -n 'Such project. Wow.'
```

If a project ID has already been created, then it can be provided via the `-p` argument and the user ID is not necessary, e.g.

```
create-notion-project -p P2024-JAS-ABCD -n 'Such project. Wow.'
```

Logging can also be enabled at various levels of detail, and logs can be saved to a file.

### create-project

This script can create a project on Toggl Track or Notion, or both:

```
usage: create-project [-h] [-u USER_ID] [-v USER_NAME] [-n NAME] [-p PROJECT_ID] [--enable-toggl] [--enable-notion] [--enable-logging]
                      [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--log-file LOG_FILE]

options:
  -h, --help            show this help message and exit
  -u USER_ID, --user_id USER_ID
                        three-letter user (client) ID, e.g. JAS
  -v USER_NAME, --user_name USER_NAME
                        user (client) name, e.g. John Andrew Smith
  -n NAME, --name NAME  short project name, e.g. 'RNA-seq analysis', project ID will be auto-generated
  -p PROJECT_ID, --project_id PROJECT_ID
                        full project ID, e.g. P2024-JAS-DEFG, if already generated
  --enable-toggl        create Toggl Track project
  --enable-notion       create Notion project
  --enable-logging      enable logging output for the papi library
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set the logging level (default: INFO)
  --log-file LOG_FILE   path to a file where logs should be written
```

If no arguments are given to the script, i.e. just running `create-project`, then interactive prompts are shown to enter the necessary arguments.

## API reference

### project module

### Project class

The `Project` class is central to the whole library. A `Project` instance can be created in a few different ways.

At the most basic level, a valid `user_id` (either three letter initials or two letter initials and an integer number from 1 to 9) can be provided when instantiating the class, and the prefix and suffix will be generated.

```
from papi.project import Project

proj = Project(user_id="JAS")
```

This will generate the project ID, `id` attribute using the current year, and a random four-letter suffix.

```
print(proj.id)
print(proj.year)
print(proj.suffix)
```

```
P2024-JAS-ABCD
2024
ABCD
```

If a valid project ID has already been created, then a `Project` instance can be instantiated with the `id` attribute, and the `year`, `user_id`, and `suffix` attributes will be pulled out and set on the instance.

```
proj = Project(id="P2024-JAS-ABCD")

print(proj.year)
print(proj.user_id)
print(proj.suffix)
```

```
2024
JAS
ABCD
```

If a grant code and/or project name are available, then these can be passed in when instantiating the class.

```
proj = Project(user_id="JAS", grant_code="R12345", name="RNA-seq analysis")
```

A version 4 UUID is also generated for the project when instantiated.

```
proj = Project(user_id="JAS")

print(proj.p_uuid)
```

```
6697e457-9785-4668-b78b-72616b27aede
```

 Or if a version 4 UUID has been generated separately then it can be provided when instantiating.

 ```
 proj = Project(user_id="JAS", p_uuid="6697e457-9785-4668-b78b-72616b27aede")
 ```

### project functions

A couple of functions are provided to check the validity of a project ID, to check the validity of a suffix, and to check for a valid version 4 UUID.

You can check the validity of a project ID as follows:

```
from papi.project import check_project_id

print(check_project_id("P2024-JAS-ABCD"))
print(check_project_id("P2024-JAS-1234"))
```

```
True
False
```

You can check the validity of a project suffix as follows:

```
from papi.project import check_suffix

print(check_suffix("ABCD"))
print(check_suffix("1234"))
```

```
True
False
```

### user module

### User class

The `User` class stores attributes of a user: their name, a three-letter initial (or two-letter initial and integer number from 1 to 9), and an optional email address.

The most basic way of instantiating a `User` instance is as follows:

```
from papi.user import User

usr = User("John Andrew Smith")

print(usr.user_id)
print(usr.user_name)
```

```
JAS
John Andrew Smith
```

The first initials are converted into the `user_id` attribute.

If an email address is available, then this can be provided when instantiating:

```
from papi.user import User

usr = User("John Andrew Smith", email="jasmith@email.com")

print(usr.email)
```

```
jasmith@email.com
```

Because our user ID naming scheme enforces that a user ID must be unique, the `user_id` attribute should not really be set directly, although it can in theory:

```
usr = User("John Smith")
usr.user_id = "JS1"
```

Setting the `user_id` attribute creates the possibility of a clash in user IDs, therefore the `user` module provides a means to create a basic user database with the TinyDB library. This avoids the possibility of a clash and appends and increments integer numbers to the end of the user ID if a matching one is already in the database.
