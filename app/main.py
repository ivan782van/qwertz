from fastapi import FastAPI

from app.api.webhook import router as webhook_router
from app.logger import logger

app = FastAPI(
    title="BIG-IP Deployment Service",
    version="1.0"
)

app.include_router(webhook_router)

@app.get("/health")
def health():

    return {
        "status": "UP"
    }

@app.on_event("startup")
def startup():
    logger.info("BIG-IP Deployer started")
