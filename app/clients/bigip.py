import requests

from app.config import CONFIG

class BigIPClient:

    def __init__(self, inventory):
        self.inventory = inventory
        self.session = requests.Session()
        if CONFIG["bigip"].get("verify_ssl", True):
            self.session.verify = CONFIG["bigip"]["ca_bundle"]
        else:
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

class BigIP:

    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def deploy(self, declaration):
        url = f"https://{self.host}/mgmt/shared/appsvcs/declare"
        response = requests.post(
            url,
            json=declaration,
            auth=(self.username, self.password),
            verify=False
        )

        return response.json()
