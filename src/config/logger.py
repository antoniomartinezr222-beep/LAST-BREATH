"""
config/logger.py - Sistema de logging centralizado (espejo de tccpdss/logger.js)
Usa Python logging estándar con handlers de archivo y consola.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from src.config.settings import Config

LOG_DIR = Config.LOG_DIR
os.makedirs(LOG_DIR, exist_ok=True)

# Formato JSON-like para los archivos (igual que winston en tccpdss)
LOG_FORMAT = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "last-breath", "message": %(message)s}'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def _make_handler(filename, level=logging.DEBUG, max_bytes=5_242_880, backup_count=5):
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, filename),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def get_logger(name: str = 'last_breath') -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # ya configurado

    logger.setLevel(logging.DEBUG)

    # error.log — solo errores
    logger.addHandler(_make_handler('error.log', level=logging.ERROR))
    # combined.log — info en adelante
    logger.addHandler(_make_handler('combined.log', level=logging.INFO))
    # access.log — todos los niveles (HTTP incluido)
    logger.addHandler(_make_handler('access.log', level=logging.DEBUG))

    # Consola en desarrollo
    if os.environ.get('FLASK_ENV', 'development') != 'production':
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s', datefmt=DATE_FORMAT
        ))
        logger.addHandler(console)

    return logger


# Instancia global
logger = get_logger()


def log_request(method: str, url: str, status: int, duration_ms: float, ip: str, user_agent: str):
    """Registra cada request HTTP (equivalente al middleware HTTP de tccpdss)."""
    import json
    logger.debug(json.dumps({
        "type": "http",
        "method": method,
        "url": url,
        "status": status,
        "duration": f"{duration_ms:.1f}ms",
        "ip": ip,
        "user_agent": user_agent
    }))


def log_login_attempt(username: str, success: bool, ip: str, user_agent: str = ''):
    """Registra intentos de login (exitoso o fallido)."""
    import json
    level = logging.INFO if success else logging.WARNING
    logger.log(level, json.dumps({
        "type": "authentication",
        "event": "login_success" if success else "login_failed",
        "username": username,
        "ip": ip,
        "user_agent": user_agent
    }))


def log_access_denied(username: str, resource: str, ip: str):
    """Registra denegaciones de acceso (403)."""
    import json
    logger.warning(json.dumps({
        "type": "security",
        "event": "access_denied",
        "username": username,
        "resource": resource,
        "ip": ip
    }))


def log_security(event: str, details: dict):
    """Evento de seguridad genérico."""
    import json
    logger.warning(json.dumps({"type": "security", "event": event, **details}))
