"""
Service de notification pour événements de déploiement AS3.
Format Markdown : date UTC, instance, fichier/tâche, status (success/error).
En cas d'erreur, inclut le détail (stack trace ou message), tronqué si trop long.
"""
import os
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import logging

LAUSANNE_TZ = ZoneInfo("Europe/Zurich")  


from app.clients import webex_client

LOG = logging.getLogger(__name__)
_TRUNCATE_LIMIT = 6000  # caractères max pour le détail d'erreur


def _maybe_truncate(text: Optional[str], limit: int = _TRUNCATE_LIMIT) -> Optional[str]:
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n...[truncated]"


def _format_markdown(status: str, instance: str, filename: Optional[str] = None, message: Optional[str] = None, error: Optional[str] = None) -> str:
    now = datetime.now(LAUSANNE_TZ).replace(microsecond=0).isoformat()
    lines = [
        f"**Alerte de déploiement - {status.upper()}**",
        "",
        f"- **Date**: {now}",
        f"- **Instance**: {instance}",
    ]

    if filename:
        lines.append(f"- **Fichier / tâche**: `{filename}`")
    lines.append(f"- **Status**: **{status}**")
    if message:
        lines.append("")
        lines.append(f"**Message**: {message}")
    if error:
        lines.append("")
        lines.append("**Détails d'erreur**:")
        lines.append("```")
        lines.append(_maybe_truncate(error))
        lines.append("```")
    return "\n".join(lines)


def _read_config():
    enabled = os.getenv("WEBEX_ENABLED", "false").lower() in ("1", "true", "yes")
    token = os.getenv("WEBEX_BOT_TOKEN")
    room = os.getenv("WEBEX_ROOM_ID")
    api_url = os.getenv("WEBEX_API_URL", "https://webexapis.com/v1/messages")
    verify = os.getenv("WEBEX_VERIFY_SSL", "true").lower() in ("1", "true", "yes")
    # Proxies via standard env vars
    proxies = {}
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if http_proxy:
        proxies["http"] = http_proxy
    if https_proxy:
        proxies["https"] = https_proxy
    if not proxies:
        proxies = None
    return enabled, token, room, api_url, verify, proxies


def send_deploy_notification(success: bool, instance: str, filename: Optional[str] = None, message: Optional[str] = None, error: Optional[Exception] = None) -> dict:
    """
    Envoie la notification de déploiement vers Webex si activé.
    Retourne le dict réponse du client, ou {"skipped": True} si désactivé,
    ou {"failed_to_send": True, "error": "..."} en cas d'échec d'envoi.
    """
    enabled, token, room, api_url, verify, proxies = _read_config()
    if not enabled:
        LOG.debug("Webex notifications disabled by WEBEX_ENABLED")
        return {"skipped": True}

    # Préparer le texte d'erreur (string) si fourni
    error_text = None
    if error is not None:
        if isinstance(error, Exception):
            error_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        else:
            error_text = str(error)

    md = _format_markdown("success" if success else "error", instance, filename, message, error_text)

    try:
        resp = webex_client.send_markdown_to_webex(md, token=token, room_id=room, api_url=api_url, verify_ssl=verify, proxies=proxies)
        LOG.info("Notification Webex envoyée: %s", resp if isinstance(resp, dict) else str(resp))
        return resp
    except Exception as exc:
        LOG.exception("Echec envoi notification Webex: %s", exc)
        # Ne pas faire échouer le déploiement pour une notification
        return {"failed_to_send": True, "error": str(exc)}
