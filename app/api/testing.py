"""
Endpoints de test - Uniquement disponibles en développement (LOG_LEVEL=DEBUG)
Permet de tester les webhooks sans avoir Bitbucket
"""

import json
import hmac
import hashlib
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.logger import logger
from app.config import LOG_LEVEL

router = APIRouter()

# Vérifier si on est en mode développement
IS_DEBUG = LOG_LEVEL.upper() == "DEBUG"


class WebhookTestPayload(BaseModel):
    """Payload de test pour simuler un webhook Bitbucket"""
    eventKey: str = Field(default="pr:merged", description="Type d'événement")
    project_key: str = Field(default="PROJ", description="Clé du projet Bitbucket")
    repo_slug: str = Field(default="repo", description="Slug du repo")
    pr_id: int = Field(default=1, description="ID du PR")
    merge_commit: str = Field(default="abc123def456", description="Hash du commit de fusion")


class WebhookTestRequest(BaseModel):
    """Requête de test de webhook"""
    payload: WebhookTestPayload
    use_signature: bool = Field(default=True, description="Ajouter une signature HMAC valide")
    invalid_signature: bool = Field(default=False, description="Forcer une signature invalide")


@router.post("/test/webhook/generate-payload")
async def generate_test_payload(payload: WebhookTestPayload) -> Dict[str, Any]:
    """
    🧪 **TEST ONLY** - Génère un payload de webhook Bitbucket pour les tests
    
    **Non disponible en production** (nécessite LOG_LEVEL=DEBUG)
    
    Returns:
        - `payload`: Le payload JSON
        - `signature`: La signature HMAC-SHA256 (si secret configuré)
        - `curl_command`: Commande curl prête à exécuter
    """
    
    if not IS_DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Test endpoints only available in DEBUG mode"
        )
    
    # Construire le payload complet Bitbucket
    full_payload = {
        "eventKey": payload.eventKey,
        "pullRequest": {
            "id": payload.pr_id,
            "toRef": {
                "repository": {
                    "project": {"key": payload.project_key},
                    "slug": payload.repo_slug
                }
            },
            "properties": {
                "mergeCommit": {"id": payload.merge_commit}
            }
        }
    }
    
    payload_json = json.dumps(full_payload, separators=(',', ':'))
    payload_bytes = payload_json.encode()
    
    # Générer la signature
    secret = os.getenv("BITBUCKET_WEBHOOK_SECRET", "").strip()
    signature = None
    
    if secret:
        signature = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
    
    # Générer la commande curl
    curl_cmd = f"""curl -X POST http://localhost:8000/api/webhook \\
  -H "Content-Type: application/json" \\
  -H "x-hub-signature: sha256={signature}" \\
  -d '{payload_json}'
"""
    
    if not signature:
        curl_cmd = f"""curl -X POST http://localhost:8000/api/webhook \\
  -H "Content-Type: application/json" \\
  -d '{payload_json}'
"""
    
    return {
        "payload": full_payload,
        "payload_json": payload_json,
        "signature": signature,
        "curl_command": curl_cmd.strip(),
        "note": "Copie/colle le curl_command dans un terminal pour tester"
    }


@router.post("/test/webhook/send")
async def send_test_webhook(request: WebhookTestRequest) -> Dict[str, Any]:
    """
    🧪 **TEST ONLY** - Envoie un webhook de test à ton propre endpoint
    
    **Non disponible en production** (nécessite LOG_LEVEL=DEBUG)
    
    Args:
        payload: Configuration du webhook de test
        use_signature: Ajouter une signature HMAC valide
        invalid_signature: Forcer une signature invalide (pour tester la validation)
    
    Returns:
        Résultat de l'appel au webhook
    """
    
    if not IS_DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Test endpoints only available in DEBUG mode"
        )
    
    import requests
    
    # Construire le payload
    full_payload = {
        "eventKey": request.payload.eventKey,
        "pullRequest": {
            "id": request.payload.pr_id,
            "toRef": {
                "repository": {
                    "project": {"key": request.payload.project_key},
                    "slug": request.payload.repo_slug
                }
            },
            "properties": {
                "mergeCommit": {"id": request.payload.merge_commit}
            }
        }
    }
    
    payload_json = json.dumps(full_payload)
    payload_bytes = payload_json.encode()
    
    # Préparer les headers
    headers = {"Content-Type": "application/json"}
    
    # Générer la signature
    if request.use_signature:
        secret = os.getenv("BITBUCKET_WEBHOOK_SECRET", "").strip()
        if secret:
            if request.invalid_signature:
                # Forcer une signature invalide pour le test
                signature = "sha256=0000000000000000000000000000000000000000000000000000000000000000"
            else:
                signature = "sha256=" + hmac.new(
                    secret.encode(),
                    payload_bytes,
                    hashlib.sha256
                ).hexdigest()
            headers["x-hub-signature"] = signature
    
    # Envoyer
    try:
        response = requests.post(
            "http://localhost:8000/api/webhook",
            data=payload_json,
            headers=headers,
            timeout=10
        )
        
        logger.info(
            f"Test webhook sent - Status: {response.status_code}",
            extra={"context": {
                "pr_id": request.payload.pr_id,
                "status_code": response.status_code
            }}
        )
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.headers.get("content-type") == "application/json" else response.text,
            "success": 200 <= response.status_code < 300
        }
        
    except Exception as e:
        logger.error(f"Error sending test webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending test webhook: {str(e)}"
        )
