import logging
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import ValidationError
from typing import Optional

from app.logger import logger
from app.models.schemas import WebhookPayload, DeploymentResponse
from app.models import BitbucketWebhook, ConfigurationFile
from app.clients.bitbucket import BitbucketClient
from app.clients.bigip import BigIPClient
from app.services.planner import DeploymentPlanner
from app.services.inventory import BigIPInventory
from app.utils.webhook_security import verify_bitbucket_webhook_signature

router = APIRouter()


class ContextFilter(logging.Filter):
    """Filter personnalisé pour ajouter du contexte aux logs"""
    def __init__(self, **context):
        super().__init__()
        self.context = context
    
    def filter(self, record):
        record.context = self.context
        return True


@router.post("/webhook", response_model=DeploymentResponse)
async def webhook(
    request: Request,
    x_hub_signature: Optional[str] = Header(None)
) -> DeploymentResponse:
    """
    Reçoit les webhooks Bitbucket et déclenche les déploiements.
    
    **Sécurisé par signature HMAC-SHA256** (si BITBUCKET_WEBHOOK_SECRET configuré)
    
    - Filtre les événements (seulement PR merged)
    - Récupère les fichiers JSON modifiés
    - Déploie sur les instances BIG-IP correspondantes
    
    **Headers de sécurité**:
    - `x-hub-signature`: Signature HMAC-SHA256 du webhook (format: sha256=...)
    
    **Exemple de test** (voir Tests Webhook ci-dessous):
    ```bash
    # Générer le secret:
    SECRET="mon_secret_teste"
    
    # Créer le payload:
    PAYLOAD='{"eventKey":"pr:merged","pullRequest":{...}}'
    
    # Générer la signature:
    SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | cut -d' ' -f2)
    
    # Envoyer:
    curl -X POST http://localhost:8000/api/webhook \\
      -H "x-hub-signature: sha256=$SIGNATURE" \\
      -H "Content-Type: application/json" \\
      -d "$PAYLOAD"
    ```
    """
    
    try:
        # ✅ Lire le corps brut pour validation de la signature
        payload_bytes = await request.body()
        payload = await request.json()
        
        # ✅ Vérifier la signature du webhook (lève 401 si invalide)
        verify_bitbucket_webhook_signature(payload_bytes, x_hub_signature)
        
        # ✅ Validation du payload Pydantic
        try:
            validated_payload = WebhookPayload(**payload)
        except ValidationError as e:
            logger.warning(
                f"Invalid webhook payload: {e.error_count()} validation error(s)",
                extra={"context": {"payload_keys": list(payload.keys())}}
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
                extra={"context": {"error_type": type(e).__name__}}
            )
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse webhook: {str(e)}"
            )
        
        # ✅ Ignorer les événements non-PR merged
        if not hook.is_pr_merged:
            logger.info(
                f"Webhook ignored - event type: {hook.event}",
                extra={"context": {"reason": "not pr:merged"}}
            )
            return DeploymentResponse(
                status="ignored",
                details={"event_type": hook.event}
            )
        
        # ✅ Logger les infos du webhook
        logger.info(
            "Webhook received for merged PR",
            extra={"context": {
                "project": hook.project,
                "repository": hook.repository,
                "pr_id": hook.pr_id,
                "merge_commit": hook.merge_commit[:7],
            }}
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
                extra={"context": {"files_count": len(files)}}
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch changed files from Bitbucket: {e}",
                extra={"context": {"error_type": type(e).__name__}}
            )
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch files from Bitbucket: {str(e)}"
            )
        
        # ✅ Pas de fichiers à déployer
        if not files:
            logger.info(
                "No JSON configuration files found",
                extra={"context": {"pr_id": hook.pr_id}}
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
            extra={"context": {"tasks_count": len(tasks)}}
        )
        
        # ✅ Charger l'inventaire UNE SEULE FOIS
        try:
            inventory = BigIPInventory()
        except Exception as e:
            logger.error(
                f"Failed to load BigIP inventory: {e}",
                extra={"context": {"error_type": type(e).__name__}}
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
                    extra={"context": {
                        "instance": task.instance,
                        "module": task.module,
                        "config_file": task.filename,
                    }}
                )
                
                # Récupérer les credentials
                target = inventory.get(task.instance)
                
                # S'authentifier et déployer
                bigip = BigIPClient(target)
                token = bigip.authenticate()
                logger.debug(
                    f"Authenticated to BIG-IP {task.instance}",
                    extra={"context": {"instance": task.instance}}
                )
                
                # Récupérer le fichier de configuration
                declaration = client.get_json_file(task)
                
                # Déployer
                result = bigip.deploy_as3(declaration)
                logger.info(
                    f"Deployment successful",
                    extra={"context": {
                        "instance": task.instance,
                        "config_file": task.filename,
                        "status": result.get("status", "unknown")
                    }}
                )
                deployment_results.append({
                    "instance": task.instance,
                    "config_file": task.filename,
                    "status": "success",
                    "result": result
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Deployment failed: {e}",
                    extra={"context": {
                        "instance": task.instance,
                        "config_file": task.filename,
                        "error_type": type(e).__name__,
                    }},
                    exc_info=False
                )
                deployment_results.append({
                    "instance": task.instance,
                    "config_file": task.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        # ✅ Résumé final
        logger.info(
            f"Deployment completed",
            extra={"context": {
                "total_tasks": len(tasks),
                "successful": len(tasks) - failed_count,
                "failed": failed_count,
                "pr_id": hook.pr_id
            }}
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
            extra={"context": {"error_type": type(e).__name__}},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
