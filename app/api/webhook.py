import logging
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.logger import logger
from app.models.schemas import WebhookPayload, DeploymentResponse
from app.models import BitbucketWebhook, ConfigurationFile
from app.clients.bitbucket import BitbucketClient
from app.clients.bigip import BigIPClient
from app.services.planner import DeploymentPlanner
from app.services.inventory import BigIPInventory

router = APIRouter()


def add_log_context(record, **kwargs):
    """Helper pour ajouter du contexte aux logs"""
    record.extra_fields = kwargs
    return record


@router.post("/webhook", response_model=DeploymentResponse)
async def webhook(payload: dict) -> DeploymentResponse:
    """
    Reçoit les webhooks Bitbucket et déclenche les déploiements.
    
    - Filtre les événements (seulement PR merged)
    - Récupère les fichiers JSON modifiés
    - Déploie sur les instances BIG-IP correspondantes
    """
    
    try:
        # ✅ Validation du payload
        try:
            validated_payload = WebhookPayload(**payload)
        except ValidationError as e:
            logger.warning(
                "Invalid webhook payload",
                extra={"error": str(e), "payload_keys": list(payload.keys())}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid webhook payload: {e.error_count()} validation error(s)"
            )
        
        # ✅ Parser le webhook
        try:
            hook = BitbucketWebhook(payload)
        except (KeyError, TypeError) as e:
            logger.error(
                f"Failed to parse BitbucketWebhook: {e}",
                extra={"error_type": type(e).__name__}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse webhook: {str(e)}"
            )
        
        # ✅ Ignorer les événements non-PR merged
        if not hook.is_pr_merged:
            logger.info(
                "Webhook ignored",
                extra={"event_type": hook.event, "reason": "not pr:merged"}
            )
            return DeploymentResponse(
                status="ignored",
                details={"event_type": hook.event}
            )
        
        # ✅ Logger les infos du webhook
        logger.info(
            "Webhook received for merged PR",
            extra={
                "project": hook.project,
                "repository": hook.repository,
                "pr_id": hook.pr_id,
                "merge_commit": hook.merge_commit[:7],
            }
        )
        
        # ✅ Récupérer les fichiers modifiés
        try:
            client = BitbucketClient()
            files = client.get_changed_json_files(
                hook.project,
                hook.repository,
                hook.pr_id
            )
            logger.info(
                f"Found {len(files)} JSON configuration file(s)",
                extra={"files": files[:5]}  # Log max 5 fichiers
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch changed files from Bitbucket: {e}",
                extra={"error_type": type(e).__name__}
            )
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch files from Bitbucket: {str(e)}"
            )
        
        # ✅ Pas de fichiers à déployer
        if not files:
            logger.info(
                "No JSON configuration files found",
                extra={"pr_id": hook.pr_id}
            )
            return DeploymentResponse(
                status="ignored",
                details={"reason": "no_json_files"}
            )
        
        # ✅ Créer les tâches de déploiement
        configs = [ConfigurationFile(f) for f in files]
        planner = DeploymentPlanner()
        tasks = planner.create_tasks(hook, configs)
        logger.info(
            f"Created {len(tasks)} deployment task(s)",
            extra={"tasks_count": len(tasks)}
        )
        
        # ✅ Charger l'inventaire UNE SEULE FOIS
        try:
            inventory = BigIPInventory()
        except Exception as e:
            logger.error(
                f"Failed to load BigIP inventory: {e}",
                extra={"error_type": type(e).__name__}
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load BIG-IP inventory: {str(e)}"
            )
        
        # ✅ Exécuter les déploiements
        deployment_results = []
        failed_count = 0
        
        for idx, task in enumerate(tasks, 1):
            try:
                logger.info(
                    f"Deploying task {idx}/{len(tasks)}",
                    extra={
                        "instance": task.instance,
                        "module": task.module,
                        "filename": task.filename,
                    }
                )
                
                # Récupérer les credentials
                target = inventory.get(task.instance)
                
                # S'authentifier et déployer
                bigip = BigIPClient(target)
                token = bigip.authenticate()
                logger.debug(
                    f"Authenticated to BIG-IP",
                    extra={"instance": task.instance}
                )
                
                # Récupérer le fichier de configuration
                declaration = client.get_json_file(task)
                
                # Déployer
                result = bigip.deploy_as3(declaration)
                logger.info(
                    f"Deployment successful",
                    extra={
                        "instance": task.instance,
                        "filename": task.filename,
                        "status": result.get("status", "unknown")
                    }
                )
                deployment_results.append({
                    "instance": task.instance,
                    "filename": task.filename,
                    "status": "success",
                    "result": result
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Deployment failed for {task.instance}/{task.filename}: {e}",
                    extra={
                        "instance": task.instance,
                        "filename": task.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                deployment_results.append({
                    "instance": task.instance,
                    "filename": task.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        # ✅ Résumé final
        logger.info(
            f"Deployment completed",
            extra={
                "total": len(tasks),
                "successful": len(tasks) - failed_count,
                "failed": failed_count,
                "pr_id": hook.pr_id
            }
        )
        
        return DeploymentResponse(
            status="accepted" if failed_count == 0 else "partial",
            details={
                "total_tasks": len(tasks),
                "successful": len(tasks) - failed_count,
                "failed": failed_count,
                "results": deployment_results
            }
        )
        
    except HTTPException:
        # Re-lever les exceptions HTTP
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in webhook handler: {e}",
            extra={"error_type": type(e).__name__},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
