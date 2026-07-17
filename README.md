# laforge-foundry

Foundry, la création des pieces de la forge. 

Application Python pour le déploiement et la gestion d'inventaire (squelette).  
Ce dépôt contient une petite application (FastAPI) et des services utilitaires (clients, services, logger, config). Le but est de fournir un outil modulable pour automatiser des déploiements et envoyer des notifications (optionnelles).

> Remarque : ce README décrit le fonctionnement actuel du dépôt. Avant d'exécuter, vérifiez les fichiers `app/config.py` et `.env.example` pour connaître les variables d'environnement prises en charge.

## Table des matières
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Installation rapide](#installation-rapide)
- [Configuration (.env)](#configuration-env)
- [Lancer l'application](#lancer-lapplication)
- [Fonctionnalités principales](#fonctionnalités-principales)
- [Notifications (optionnelles)](#notifications-optionnelles)
- [Tests](#tests)
- [Debug / dépannage](#debug--dépannage)
- [Contribuer](#contribuer)

---

## Structure du projet
Arborescence essentielle (extrait) :

- app/
  - main.py         -> point d'entrée FastAPI (routes minimales comme `/health`)
  - config.py       -> lecture des variables d'environnement et constantes
  - logger.py       -> configuration du logger (format JSON)
  - clients/        -> clients externes (BigIP, Bitbucket, Webex, ...)
  - services/       -> logique métier (deployer, inventory, planner, notification, ...)
  - models/         -> modèles / schémas si nécessaires
- requirements.txt  -> dépendances Python
- .env.example      -> exemples de variables d'environnement (NE PAS committer .env réel)

Cette structure vise à séparer :
- les clients externes (HTTP / API),
- la logique métier (services),
- la configuration et le logging.

---

## Prérequis
- Python 3.9+ recommandé
- pip
- (optionnel) Docker si vous voulez containeriser

---

## Installation rapide

1. Cloner le dépôt :
```bash
git clone https://github.com/ivan782van/qwertz.git
cd qwertz
```

2. Créer et activer un environnement virtuel :
```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows
```

3. Installer les dépendances :
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Préparer le fichier d'environnement local (ne pas committer) :
```bash
cp .env.example .env
# Editer .env et renseigner les variables nécessaires (voir section suivante)
```

---

## Configuration (.env)
Toutes les variables d'environnement attendues sont documentées dans `.env.example`. Les variables souvent utilisées incluent (liste non exhaustive — vérifiez `app/config.py`) :

- Variables générales
  - `LOG_LEVEL` — niveau de log (INFO, DEBUG, ...)
- Intégrations externes (exemples)
  - `WEBEX_ENABLED` — activer les notifications Webex (true/false)
  - `WEBEX_BOT_TOKEN` — token du bot Webex (si activé)
  - `WEBEX_ROOM_ID` — id de la room Webex (si activé)
  - `WEBEX_API_URL` — URL API (par défaut https://webexapis.com/v1/messages)
  - `WEBEX_VERIFY_SSL` — vérifier TLS (true/false)

- Autres intégrations (Bitbucket/BigIP, etc.)  
  Consultez `app/config.py` pour la liste complète des variables requises par les différents clients.

Important :
- NE COMMETTEZ JAMAIS `.env` contenant des secrets dans le repo.
- Utilisez `.env.example` pour documenter les variables.

---

## Lancer l'application (développement)

L'application expose un objet FastAPI dans `app/main.py`. Pour lancer le serveur de développement :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Endpoint de santé :
  - `GET /health` — retourne un JSON minimal (vérifier `app/main.py`).

---

## Fonctionnalités principales

- `app/services/deployer.py`  
  Composant principal pour exécuter des déploiements. Il expose une classe `Deployer` et la méthode `deploy(instance, declaration)` (stub actuel). Vous pouvez appeler cette méthode depuis vos scripts ou l'exposer via une route API si besoin.

- `app/services/inventory.py`, `planner.py`  
  Services utilitaires pour gérer l'inventaire et la planification des tâches.

- `app/logger.py`  
  Formatage et configuration du logger (JSON-friendly). Vérifiez que l'application utilise ce logger pour centraliser les messages.

---

## Notifications (optionnelles)

Le dépôt contient une implémentation de notification via Webex (client + service). Comportement recommandé :

- Activation via variable d'environnement `WEBEX_ENABLED=true`.
- Configuration des secrets via `WEBEX_BOT_TOKEN` et `WEBEX_ROOM_ID`.
- Les notifications doivent être déclenchées depuis les points métier (par exemple `Deployer.deploy`) — la fonction de notification est non bloquante : un échec d'envoi ne doit pas arrêter le déploiement.

Exemple d'envoi manuel (local, ne pas committer) :

```python
# test_webex.py (local)
from app.services.notification import send_deploy_notification
send_deploy_notification(True, instance="staging", filename="playbook.yml", message="Test notification")
```

Si vous n'utilisez pas les notifications, laissez `WEBEX_ENABLED=false`.

---

## Tests

- Framework recommandé : pytest
- Exemple d'exécution locale :
```bash
pip install pytest
pytest -q
```

- Il est recommandé de mocker les appels réseau (ex: `requests`) pour les tests unitaires du service `notification`.

---

## Debug / dépannage

- Vérifier les logs :
  - Contrôler `LOG_LEVEL` et la sortie du logger (format JSON).
- Problèmes de dépendances :
  - Exécuter `pip install -r requirements.txt`.
  - Comparer `pip freeze` à `requirements.txt` si besoin.
- Erreurs d'API externes (Webex, Bitbucket, BigIP) :
  - Vérifier les variables d'environnement et la connectivité réseau.
  - En cas d'erreur TLS proxifiée, ajuster `*_VERIFY_SSL` si nécessaire (mais attention aux risques de sécurité).

---

## Contribuer

- Créez une branche feature/issue-description pour vos modifications.
- Soumettez une PR ciblée vers `main`.
- Évitez de committer des secrets ou des fichiers de configuration contenant des tokens.
- Ajoutez des tests pour toute logique métier ajoutée.

---

## Notes finales

- Ce dépôt contient une base modulaire pensée pour être complétée et adaptée selon vos besoins d'automatisation et d'orchestration.
- Avant toute mise en production, vérifiez et testez les intégrations externes (tokens, permissions, limites d'API).

Questions / modifications demandées ? Ouvrez un ticket ou demandez-moi de préciser une section (ex : doc pour un client spécifique, ajout d'exemples CLI, génération d'image Docker, etc.).e
