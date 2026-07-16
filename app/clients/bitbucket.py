import os
import json
import requests
from pathlib import Path
from app.logger import logger
from app.config import (
    BITBUCKET_URL,
    BITBUCKET_TOKEN,
    BITBUCKET_VERIFY_SSL,
    BITBUCKET_CA_BUNDLE
)


class BitbucketClient:

    def __init__(self):
        self.base_url = BITBUCKET_URL
        self.headers = {
            "Authorization": f"Bearer {BITBUCKET_TOKEN}"
        }
        
        # Configurer la vérification SSL
        if BITBUCKET_VERIFY_SSL:
            # Vérifier si le fichier CA existe
            if Path(BITBUCKET_CA_BUNDLE).exists():
                self.verify = BITBUCKET_CA_BUNDLE
                logger.debug(f"Using CA bundle: {BITBUCKET_CA_BUNDLE}")
            else:
                logger.warning(
                    f"CA bundle not found at {BITBUCKET_CA_BUNDLE}, "
                    "using system certificates"
                )
                self.verify = True
        else:
            logger.warning("SSL verification disabled for Bitbucket")
            self.verify = False

    def get_changes(self, project, repository, pr_id):
        url = (
            f"{self.base_url}"
            f"/rest/api/latest/projects/{project}"
            f"/repos/{repository}"
            f"/pull-requests/{pr_id}/changes"
        )
        logger.debug(f"Fetching changes for PR {pr_id}")
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
        
        logger.debug(f"Downloading file: {task.path}")
        
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
