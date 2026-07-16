from fastapi import APIRouter, HTTPException

from app.models.bitbucket import BitbucketWebhook
from app.models import BitbucketWebhook, ConfigurationFile
from app.clients.bitbucket import BitbucketClient
from app.services.planner import DeploymentPlanner
from app.models import DeploymentTask
from app.services.inventory import BigIPInventory
from app.clients.bigip import BigIPClient

router = APIRouter()


@router.post("/webhook")
async def webhook(payload: dict):

    if "eventKey" not in payload:
        raise HTTPException(
            status_code=400,
            detail="Invalid Bitbucket webhook payload"
        )

    # Création de l'objet
    hook = BitbucketWebhook(payload)

    # On ne traite que les PR mergées
    if not hook.is_pr_merged:
        return {
            "status": "ignored"
        }

    print(f"Projet     : {hook.project}")
    print(f"Repository : {hook.repository}")
    print(f"PR         : {hook.pr_id}")
    print(f"Merge      : {hook.merge_commit}")

    client = BitbucketClient()

    files = client.get_changed_json_files(
        hook.project,
        hook.repository,
        hook.pr_id
    )

    configs = [
        ConfigurationFile(f)
        for f in files
    ]

    planner = DeploymentPlanner()
    tasks = planner.create_tasks(
        hook,
        configs
    )

    inventory = BigIPInventory()

    for task in tasks:
        inventory = BigIPInventory()
        target = inventory.get(task.instance)
        bigip = BigIPClient(target)
        token = bigip.authenticate()
        declaration = client.get_json_file(task)
        result = bigip.deploy_as3(declaration)
        print(result)

    return {
        "status": "accepted"
    }
