import requests


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
