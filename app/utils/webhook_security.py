import hmac
import hashlib
from fastapi import HTTPException
from typing import Optional
from app.logger import logger
import os


BITBUCKET_WEBHOOK_SECRET = os.getenv("BITBUCKET_WEBHOOK_SECRET", "").strip()


def verify_bitbucket_webhook_signature_raw(
    payload_bytes: bytes,
    x_hub_signature: Optional[str] = None
) -> bool:
    """
    Vérifie la signature HMAC-SHA256 du webhook Bitbucket.
    
    Cette fonction accepte directement les bytes du payload et la signature,
    ce qui la rend compatible avec Swagger et les tests.
    
    Documentation: https://bitbucket.org/product/features/webhooks
    
    Args:
        payload_bytes: Le corps brut de la requête (encoded en UTF-8)
        x_hub_signature: Signature HMAC du header 'x-hub-signature'
                        Format: "sha256=hex_digest" ou None
    
    Returns:
        True si la signature est valide ou pas de secret configuré
    
    Raises:
        HTTPException 401: Signature invalide ou manquante (en prod)
        HTTPException 400: Format de signature invalide
    """
    
    # Si pas de secret configuré, accepter tous les webhooks (mode développement)
    if not BITBUCKET_WEBHOOK_SECRET:
        logger.debug(
            "⚠️  BITBUCKET_WEBHOOK_SECRET not configured - signature verification DISABLED",
            extra={"context": {"security_mode": "disabled"}}
        )
        return True
    
    # En production (secret configuré), vérifier la signature
    if not x_hub_signature:
        logger.error(
            "🚨 Missing x-hub-signature - webhook rejected",
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
                "🚨 Webhook signature mismatch - tampering detected",
                extra={"context": {
                    "received": received_signature[:16] + "..." if len(received_signature) > 16 else "***",
                    "expected": expected_signature[:16] + "..." if len(expected_signature) > 16 else "***"
                }}
            )
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Invalid webhook signature"
            )
        
        logger.info("✅ Webhook signature verified")
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating signature: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signature format: {str(e)}"
        )
