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
