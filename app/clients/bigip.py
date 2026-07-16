import requests
from pathlib import Path
from app.logger import logger
from app.config import (
    BIGIP_VERIFY_SSL,
    BIGIP_CA_BUNDLE
)


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
        response.raise_for_status()

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
