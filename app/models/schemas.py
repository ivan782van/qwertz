"""
Schémas Pydantic pour validation des données
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class WebhookPullRequest(BaseModel):
    """Modèle pour les informations du Pull Request"""
    id: int
    toRef: Dict[str, Any] = Field(description="Reference destination (branch)")
    properties: Dict[str, Any] = Field(description="Properties including merge commit")


class WebhookPayload(BaseModel):
    """Modèle pour valider le payload du webhook Bitbucket"""
    eventKey: str = Field(description="Type d'événement (e.g., 'pr:merged')")
    pullRequest: WebhookPullRequest


class DeploymentResponse(BaseModel):
    """Réponse du webhook après traitement"""
    status: str = Field(description="Status du traitement (accepted, ignored, failed)")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Détails supplémentaires")
    error: Optional[str] = Field(default=None, description="Message d'erreur si applicable")


class HealthResponse(BaseModel):
    """Réponse du healthcheck"""
    status: str = Field(description="État du service (UP, DOWN)")
    version: str = Field(description="Version du service")
