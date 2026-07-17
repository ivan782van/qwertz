import logging
from app.services.notification import send_deploy_notification

logger = logging.getLogger(__name__)

class Deployer:

    def deploy(self, instance, declaration):
        try:
            # --- logique réelle de déploiement ---
            # placeholder: exécuter le déploiement ici
            # ...

            # Si tout OK -> notifier succès
            try:
                send_deploy_notification(True, instance=instance, filename=declaration, message="Déploiement réussi")
            except Exception:
                logger.exception("Erreur lors de l'envoi de la notification de succès")
        except Exception as e:
            # Sur erreur : notifier l'échec puis propager (ou gérer selon besoin)
            try:
                send_deploy_notification(False, instance=instance, filename=declaration, message="Échec du déploiement", error=e)
            except Exception:
                logger.exception("Erreur lors de l'envoi de la notification d'erreur")
            raise
