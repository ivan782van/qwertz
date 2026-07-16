import os
import json
import requests
from app.config import CONFIG
from app.logger import logger

class BitbucketClient:

    def __init__(self):
        self.base_url = CONFIG["bitbucket"]["url"]
        self.headers = {
            "Authorization": f"Bearer {os.getenv('BITBUCKET_TOKEN')}"
        }
        if CONFIG["bitbucket"].get("verify_ssl", True):
            self.verify = CONFIG["bitbucket"]["ca_bundle"]
        else:
            self.verify = False

    def get_changes(self, project, repository, pr_id):
        url = (
            f"{self.base_url}"
            f"/rest/api/latest/projects/{project}"
            f"/repos/{repository}"
            f"/pull-requests/{pr_id}/changes"
        )
        logger.debug(f"Fetching changes for PR {pr_id}")  # Sans l'URL !
        response = requests.get(
            url,
            headers=self.headers,
            verify=self.verify,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_changed_files(self, project, repository, pr_id):
        changes = self.get_changes(project, repository, pr_id)
        files = [change["path"]["toString"] for change in changes.get("values", [])]
        return files

    def get_changed_json_files(self, project, repository, pr_id):
        files = self.get_changed_files(project, repository, pr_id)
        return [
            f for f in files
            if f.startswith("LTM/configurations/") and f.endswith(".json")
        ]

    def download_file(self, task):
        url = (
            f"{self.base_url}"
            f"/rest/api/latest/projects/{task.project}"
            f"/repos/{task.repository}"
            f"/raw/{task.path}"
            f"?at={task.merge_commit}"
        )
        
        logger.debug(f"Downloading file: {task.path}")  # Plus secure
        
        response = requests.get(
            url,
            headers=self.headers,
            verify=self.verify,
            timeout=30
        )
        response.raise_for_status()
        return response.text

    def get_json_file(self, task):
        content = self.download_file(task)
        return json.loads(content)
