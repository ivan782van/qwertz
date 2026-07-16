from app.models import DeploymentTask

class DeploymentPlanner:
    def create_tasks(self, hook, configs):
        tasks = []
        for cfg in configs:
            tasks.append(
                DeploymentTask(
                    instance=cfg.instance,
                    module=cfg.module,
                    filename=cfg.filename,
                    path=cfg.path,
                    merge_commit=hook.merge_commit,
                    project=hook.project,
                    repository=hook.repository
                )
            )
        return tasks
