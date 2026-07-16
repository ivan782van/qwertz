from fastapi import FastAPI
<<<<<<< HEAD

from app.webhook import router as webhook_router
=======
from app.api.webhook import router as webhook_router
from app.logger import logger
>>>>>>> 6eea538 ( new project bigip-deployer)

app = FastAPI(
    title="BIG-IP Deployment Service",
    version="1.0"
)

app.include_router(webhook_router)

<<<<<<< HEAD

=======
>>>>>>> 6eea538 ( new project bigip-deployer)
@app.get("/health")
def health():

    return {
        "status": "UP"
    }
<<<<<<< HEAD
=======

@app.on_event("startup")
def startup():
    logger.info("BIG-IP Deployer started")
>>>>>>> 6eea538 ( new project bigip-deployer)
