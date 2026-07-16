class BitbucketWebhook:

    def __init__(self, payload: dict):
        self.payload = payload

    @property
    def event(self):
        return self.payload["eventKey"]

    @property
    def is_pr_merged(self):
        return self.event == "pr:merged"

    @property
    def pr_id(self):
        return self.payload["pullRequest"]["id"]

    @property
    def project(self):
        return self.payload["pullRequest"]["toRef"]["repository"]["project"]["key"]

    @property
    def repository(self):
        return self.payload["pullRequest"]["toRef"]["repository"]["slug"]

    @property
    def merge_commit(self):
        return self.payload["pullRequest"]["properties"]["mergeCommit"]["id"]
