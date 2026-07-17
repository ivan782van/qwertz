import logging 
import requests
from pathlib import Path
from app.logger import logger
from app.services.notification import send_deploy_notification
from app.config import (
    BIGIP_VERIFY_SSL,
    BIGIP_CA_BUNDLE
)

LOG = logging.getLogger(__name__)


class BigIPClient:

    def __init__(self, inventory):
        self.inventory = inventory
        self.session = requests.Session()
        
        # Configurer la vérification SSL
        if BIGIP_VERIFY_SSL:
            # Vérifier si le fichier CA existe
            if Path(BIGIP_CA_BUNDLE).exists():
                self.session.verify = BIGIP_CA_BUNDLE
                logger.debug(f"Using CA bundle: {BIGIP_CA_BUNDLE}")
            else:
                logger.warning(
                    f"CA bundle not found at {BIGIP_CA_BUNDLE}, "
                    "using system certificates"
                )
                self.session.verify = True
        else:
            logger.warning("SSL verification disabled for BIG-IP")
            self.session.verify = False

    def deploy_as3(self, declaration):
        partition = self.inventory["partition"]
        url = (
            f"https://{self.inventory['host']}"
            f"/mgmt/shared/appsvcs/declare/"
            f"{partition}/applications"
        )
        response = self.session.post(
            url,
            json=declaration,
            timeout=300
        )
        try:
            response = self.session.post(url, json=declaration, timeout=300)
            response.raise_for_status()

            # Notification de succès (non bloquante)
            try:
                instance = self.inventory.get("name", self.inventory.get("host"))
                filename = declaration.get("file_name") if isinstance(declaration, dict) else None
                send_deploy_notification(True, instance=instance, filename=filename, message="AS3 declaration applied")
            except Exception:
                LOG.exception("Erreur lors de l'envoi de la notification de succès")

            return response.json()
        except requests.RequestException as e:
            # Notification d'erreur
            try:
                instance = self.inventory.get("name", self.inventory.get("host"))
                filename = declaration.get("file_name") if isinstance(declaration, dict) else None
                send_deploy_notification(False, instance=instance, filename=filename, message="AS3 declaration failed", error=e)
            except Exception:
                LOG.exception("Erreur lors de l'envoi de la notification d'erreur")
            # Ré-élever pour conserver comportement existant
            raise

        return response.json()

    def authenticate(self):
        url = (
            f"https://{self.inventory['host']}"
            "/mgmt/shared/authn/login"
        )
        payload = {
            "username": self.inventory["username"],
            "password": self.inventory["password"],
            "loginProviderName": "tmos"
        }
        response = self.session.post(
            url,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        token = response.json()["token"]["token"]
        self.session.headers["X-F5-Auth-Token"] = token
        return token
