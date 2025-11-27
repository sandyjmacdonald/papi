import sys
import json
from papi.wrappers import NotionWrapper
from papi import config, setup_logger

def main():
    """Main function of create-notion-task script."""
    required = ["NOTION_API_SECRET", "NOTION_PROJECTS_DB", "NOTION_WORKORDERS_DB"]
    if any(r not in config for r in required):
        logger.warning("Set NOTION_API_SECRET, NOTION_PROJECTS_DB, NOTION_WORKORDERS_DB in your .env")
        return

    notion = NotionWrapper(config["NOTION_API_SECRET"])
    projects_db_id = config["NOTION_PROJECTS_DB"]
    workorders_db_id = config["NOTION_WORKORDERS_DB"]
    trac_costs_db_id = config["NOTION_TRAC_COSTS_DB"]

    projects = ["P2025-DL1-DDZH", "P2025-NMH-XUHO"]
    for p in projects:
        project = notion.get_project(projects_db_id=projects_db_id, project_id=p, workorders_db_id=workorders_db_id)
        print(project)

        workorder = notion.get_workorder(workorders_db_id=workorders_db_id, workorder_id=project.workorder)
        print(workorder)
        print(workorder.is_complete())

#    notion.get_trac_costs(trac_costs_db_id=trac_costs_db_id, key="Internal Charity")

if __name__ == "__main__":
    main()
