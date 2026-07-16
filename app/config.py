import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Charger le fichier .env depuis la racine du projet
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

# ==========================================
# CHEMINS
# ==========================================

config_path = os.getenv(
    "CONFIG_PATH",
    str(Path(__file__).parent.parent / "config" / "config.yaml")
)

try:
    with open(config_path, "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    raise RuntimeError(f"Configuration file not found: {config_path}")


# ==========================================
# BITBUCKET
# ==========================================

BITBUCKET_URL = os.getenv("BITBUCKET_URL", "https://bitbucket.company.net")
BITBUCKET_TOKEN = os.getenv("BITBUCKET_TOKEN")
BITBUCKET_VERIFY_SSL = os.getenv("BITBUCKET_VERIFY_SSL", "true").lower() == "true"
BITBUCKET_CA_BUNDLE = os.getenv(
    "BITBUCKET_CA_BUNDLE",
    "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"
)

# Validation
if not BITBUCKET_TOKEN:
    raise ValueError("❌ BITBUCKET_TOKEN non défini dans .env")


# ==========================================
# BIG-IP
# ==========================================

BIGIP_USERNAME = os.getenv("BIGIP_USERNAME")
BIGIP_PASSWORD = os.getenv("BIGIP_PASSWORD")
BIGIP_VERIFY_SSL = os.getenv("BIGIP_VERIFY_SSL", "true").lower() == "true"
BIGIP_CA_BUNDLE = os.getenv(
    "BIGIP_CA_BUNDLE",
    "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"
)

# Validation
if not BIGIP_USERNAME or not BIGIP_PASSWORD:
    raise ValueError("❌ BIGIP_USERNAME et BIGIP_PASSWORD requis dans .env")


# ==========================================
# APPLICATION
# ==========================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
