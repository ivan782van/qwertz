from dataclasses import dataclass


@dataclass
class DeploymentTask:
    instance: str
    module: str
    path: str
    filename: str
    merge_commit: str
    project: str
    repository: str
