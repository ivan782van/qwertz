import logging
<<<<<<< HEAD

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
=======
import os

log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
>>>>>>> 6eea538 ( new project bigip-deployer)
)

logger = logging.getLogger("bigip-deployer")
