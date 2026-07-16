import json

from app.bigip import BigIP


def deploy_file(host, username, password, filename):

    with open(filename) as f:

        declaration = json.load(f)

    bigip = BigIP(host, username, password)

    return bigip.deploy(declaration)

