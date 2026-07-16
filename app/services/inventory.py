import os
import yaml


class BigIPInventory:

    def __init__(self):

        with open("inventory/bigip.yml") as f:
            self.data = yaml.safe_load(f)

    def get(self, instance):

        defaults = self.data["defaults"]

        current = self.data["instances"][instance]
        
        username = current.get("username")
        if username is None:
            username = os.getenv(defaults["username_env"])
        
        password = os.getenv(
            current.get(
                "password_env",
                defaults["password_env"]
            )
        )   
        
        return {

            "host": current["host"],
            "username": username,
            "password": password,
            "verify_ssl": current.get(
                "verify_ssl",
                defaults["verify_ssl"]
            ),
            "partition": current.get(
                "partition",
                defaults["partition"]
            )
        }   
