<<<<<<< HEAD
import yaml

CONFIG_FILE = "config/instances.yaml"


def load_config():

    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)
=======
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

config_path = os.getenv(
    "CONFIG_PATH",
    Path(__file__).parent / "config" / "config.yaml"
)

try:
    with open(config_path, "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    raise RuntimeError(f"Configuration file not found: {config_path}")
>>>>>>> 6eea538 ( new project bigip-deployer)
