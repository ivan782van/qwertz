"""
Client Webex léger (synchronisé) pour envoyer un markdown vers Webex Teams.
Utilise requests avec retry + backoff exponentiel.
"""
import logging
import time
from typing import Optional, Dict

import requests

LOG = logging.getLogger(__name__)

DEFAULT_API_URL = "https://webexapis.com/v1/messages"


def _do_post(api_url: str, json_body: Dict, headers: Dict, verify: bool, proxies: Optional[dict], timeout: int):
    """Une seule tentative de POST. Lève une exception requests en cas d'erreur."""
    resp = requests.post(api_url, json=json_body, headers=headers, verify=verify, proxies=proxies, timeout=timeout)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return {"status_code": resp.status_code, "text": resp.text}


def send_markdown_to_webex(
    markdown: str,
    token: str,
    room_id: str,
    api_url: str = DEFAULT_API_URL,
    verify_ssl: bool = True,
    proxies: Optional[dict] = None,
    timeout: int = 10,
    retries: int = 3,
    backoff_factor: float = 0.5,
) -> dict:
    """
    Envoie un message markdown vers Webex avec retry + backoff.
    Lève ValueError si token/room_id manquants.
    Retourne le JSON de la réponse ou lève après échecs.
    """
    if not token or not room_id:
        raise ValueError("Webex token and room_id are required")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"roomId": room_id, "markdown": markdown}

    attempt = 0
    while True:
        try:
            return _do_post(api_url, body, headers, verify_ssl, proxies, timeout)
        except Exception as e:
            attempt += 1
            LOG.warning("Tentative d'envoi Webex %d/%d échouée: %s", attempt, retries, e)
            if attempt >= retries:
                LOG.exception("Toutes les tentatives d'envoi Webex ont échoué")
                raise
            sleep_time = backoff_factor * (2 ** (attempt - 1))
            time.sleep(sleep_time)
