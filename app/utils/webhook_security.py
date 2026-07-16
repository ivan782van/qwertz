import hmac
import hashlib
import json
from fastapi import HTTPException, Header
from typing import Optional
from app.logger import logger
import os


BITBUCKET_WEBHOOK_SECRET = os.getenv("BITBUCKET_WEBHOOK_SECRET", "").strip()


def verify_bitbucket_webhook_signature(
    payload_bytes: bytes,
    x_hub_signature: Optional[str] = Header(None)
) -> bool:
    """
    Vérifie la signature HMAC-SHA256 du webhook Bitbucket.
    
    Documentation: https://bitbucket.org/product/features/webhooks
    
    Args:
        payload_bytes: Le corps brut de la requête POST
        x_hub_signature: Header 'x-hub-signature' de la requête
                        Format: "sha256=hex_digest"
    
    Returns:
        True si la signature est valide, sinon lève HTTPException
    
    Raises:
        HTTPException 401: Signature invalide ou manquante
        HTTPException 400: Format de signature invalide
    """
    
    # Si pas de secret configuré, accepter tous les webhooks (mode développement)
    if not BITBUCKET_WEBHOOK_SECRET:
        logger.warning(
            "⚠️  BITBUCKET_WEBHOOK_SECRET not configured - webhook signature verification DISABLED",
            extra={"context": {"security_mode": "disabled"}}
        )
        return True
    
    # Vérifier que le header est présent
    if not x_hub_signature:
        logger.error(
            "🚨 Missing x-hub-signature header - possible attack attempt",
            extra={"context": {"header": "x-hub-signature"}}
        )
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing webhook signature"
        )
    
    try:
        # Parser le header : "sha256=abcd1234..."
        if "=" not in x_hub_signature:
            logger.error(f"Invalid signature format: missing '='")
            raise ValueError("Signature format invalid")
        
        algorithm, received_signature = x_hub_signature.split("=", 1)
        
        if algorithm.lower() != "sha256":
            logger.warning(f"Unexpected signature algorithm: {algorithm}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid signature algorithm: expected sha256, got {algorithm}"
            )
        
        # Calculer la signature attendue
        expected_signature = hmac.new(
            BITBUCKET_WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Comparer de façon sécurisée (timing-safe comparison)
        if not hmac.compare_digest(expected_signature, received_signature):
            logger.error(
                "🚨 Webhook signature mismatch - possible tampering detected",
                extra={"context": {
                    "received_signature": received_signature[:16] + "..." if len(received_signature) > 16 else "***",
                    "expected_signature": expected_signature[:16] + "..." if len(expected_signature) > 16 else "***"
                }}
            )
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Invalid webhook signature"
            )
        
        logger.debug("✅ Webhook signature verified successfully")
        return True
        
    except HTTPException:
        # Re-lever les exceptions HTTP
        raise
    except Exception as e:
        logger.error(f"Error validating signature: {e}", extra={"context": {"error": str(e)}})
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signature format: {str(e)}"
        )


async def get_raw_body(request) -> bytes:
    """
    Récup��re le corps brut d'une requête FastAPI.
    Utilisé pour la validation de signature HMAC.
    """
    return await request.body()
