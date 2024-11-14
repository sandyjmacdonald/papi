import argparse
import warnings
from papi.wrappers import NotionWrapper
from papi import config
from papi.user import User
from papi.project import Project

def main():
    """Main function of create-notion-project script"""

    # Set up argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user_id", type=str, help="three-letter user (client) ID, e.g. JS1", required=False
    )
    parser.add_argument(
        "-v", "--user_name", type=str, help="user (client) name, e.g. John Smith", required=False
    )
    parser.add_argument(
        "-n", "--name", type=str, help="short project name, e.g. 'RNA-seq analysis', project ID will be auto-generated", required=False
    )
    parser.add_argument(
        "-p", "--project_id", type=str, help="full project ID, e.g. P2024-JS1-DEFG, if already generated", required=False
    )
    args = parser.parse_args()

    # Set up Notion API wrapper
    #
    # NOTE: you must have added your Notion API credentials and user and projects
    # database IDs with variable names below to .env file in this directory
    if not "NOTION_API_SECRET" in config and not "NOTION_CLIENTS_DB" in config and not "NOTION_PROJECTS_DB" in config:
        warnings.warn("Please create a .env file with NOTION_API_SECRET and NOTION_CLIENTS_DB and NOTION_PROJECTS_DB set!")
        return  
    notion_api_secret = config["NOTION_API_SECRET"]
    notion_clients_db = config["NOTION_CLIENTS_DB"]
    notion_projects_db = config["NOTION_PROJECTS_DB"]
    notion = NotionWrapper(notion_api_secret)

    user_id = args.user_id
    user_name = args.user_name
    project_name = args.name
    project_id = args.project_id

    if user_id and not user_name:
        user = User(user_id=user_id)
    elif user_name and not user_id:
        user = User(user_name)
    elif user_id and user_name:
        user = User(user_name, user_id=user_id)
    else:
        warnings.warn("Please provide either a three-letter user ID and/or user name")
        return

    if project_id and not project_name:
        project = Project(id=project_id)
    elif project_name and not project_id:
        project = Project(name=project_name, user_id=user.user_id)
    elif project_id and project_name:
        project = Project(name=project_name, id=project_id)
    else:
        warnings.warn("Please provide either a valid project ID and/or project name")
        return

    # Create project on Notion
    user_page_id = notion.get_user_page_id(notion_clients_db, user)
    if user_page_id is not None:
        notion_proj_id = notion.create_project(project, user, notion_projects_db, user_page_id=user_page_id)
        print(f"Project '{notion_proj_id}' created successfully!")
    else:
        notion_proj_id = notion.create_project(project, user, notion_projects_db)
        print(f"Project '{notion_proj_id}' created successfully!")

if __name__ == "__main__":
    main()