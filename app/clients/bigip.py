import requests
from pathlib import Path
from app.logger import logger
from app.services.notification import send_deploy_notification
from app.config import (
    BIGIP_VERIFY_SSL,
    BIGIP_CA_BUNDLE
)


class BigIPClient:

    def __init__(self, inventory):
        self.inventory = inventory
        self.session = requests.Session()

        # Configuration de la vérification SSL
        if BIGIP_VERIFY_SSL:
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

    def _notify(self, success, declaration, message):
        """Envoie la notification de déploiement sans jamais faire planter l'appelant."""
        try:
            instance = self.inventory.get("name", self.inventory.get("host"))
            filename = declaration.get("file_name") if isinstance(declaration, dict) else None
            send_deploy_notification(success, instance=instance, filename=filename, message=message)
        except Exception:
            logger.exception("Erreur lors de l'envoi de la notification de déploiement")

    def deploy_as3(self, declaration):
        partition = self.inventory["partition"]
        url = (
            f"https://{self.inventory['host']}"
            f"/mgmt/shared/appsvcs/declare/"
            f"{partition}/applications"
        )
        try:
            response = self.session.post(url, json=declaration, timeout=300)
            logger.debug(f"AS3 response status: {response.status_code}")
            logger.debug(f"AS3 response body: {response.text}")
            response.raise_for_status()

            self._notify(True, declaration, "AS3 declaration applied")
            return response.json()

        except requests.RequestException as e:
            # e.response peut être absent (timeout, DNS, connexion refusée...)
            as3_body = e.response.text if e.response is not None else str(e)
            logger.debug(f"AS3 error response: {as3_body}")

            self._notify(False, declaration, f"AS3 declaration failed: {as3_body}")
            raise

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
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        token = response.json()["token"]["token"]
        self.session.headers["X-F5-Auth-Token"] = token
        return token