from fastapi import FastAPI
from app.api.webhook import router as webhook_router
from app.logger import logger
from app.models.schemas import HealthResponse

app = FastAPI(
    title="BIG-IP Deployment Service",
    version="1.0.0",
    description="Automated BIG-IP AS3 deployment triggered by Bitbucket webhooks"
)

# Inclure les routers
app.include_router(webhook_router, prefix="/api", tags=["Webhooks"])


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Healthcheck endpoint pour vérifier l'état du service.
    """
    return HealthResponse(
        status="UP",
        version=app.version
    )


@app.on_event("startup")
def startup():
    """Événement de démarrage du service"""
    logger.info(
        f"BIG-IP Deployment Service started - v{app.version}",
        extra={"context": {"service": app.title}}
    )


@app.on_event("shutdown")
def shutdown():
    """Événement d'arrêt du service"""
    logger.info("BIG-IP Deployment Service stopped")
