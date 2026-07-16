import logging
import json
import sys
from datetime import datetime
import os

from app.config import LOG_LEVEL


class JSONFormatter(logging.Formatter):
    """Formateur personnalisé pour logs JSON structurés"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Ajouter des informations contextuelles
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """Formateur simple et lisible pour stdout"""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        level_name = record.levelname
        color = self.COLORS.get(level_name, "")
        
        # Format: [HH:MM:SS] [LEVEL] logger_name: message
        timestamp = self.formatTime(record, "%H:%M:%S")
        
        base_message = (
            f"[{timestamp}] "
            f"{color}[{level_name:8s}]{self.RESET} "
            f"{record.name}: "
            f"{record.getMessage()}"
        )
        
        # Ajouter exception si présente
        if record.exc_info:
            base_message += "\n" + self.formatException(record.exc_info)
        
        # Ajouter champs supplémentaires
        if hasattr(record, "extra_fields"):
            extra = record.extra_fields
            extra_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            base_message += f" | {extra_str}"
        
        return base_message


# Créer le logger
logger = logging.getLogger("bigip-deployer")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Handler pour stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(SimpleFormatter())
logger.addHandler(stdout_handler)

# Log de démarrage
logger.debug(f"Logger initialized with level: {LOG_LEVEL}")
