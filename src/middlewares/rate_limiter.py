"""
middlewares/rate_limiter.py - Rate limiting (espejo de tccpdss/rateLimiter.js)
Requiere: pip install flask-limiter

Implementa dos limitadores:
  - auth_limiter  : 5 intentos / 15 min  (rutas de login)
  - api_limiter   : 200 req  / 1 min     (API general)
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.config.logger import log_security

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",          # en producción: "redis://localhost:6379"
)

# Límites individuales que se aplican decorando rutas
AUTH_LIMIT  = "5 per 15 minutes"   # para /login
API_LIMIT   = "200 per minute"      # para API general


def on_rate_limit_exceeded(e):
    """Callback cuando se supera el límite — registra el evento de seguridad."""
    from flask import request
    log_security("rate_limit_exceeded", {
        "ip": request.remote_addr,
        "path": request.path,
        "method": request.method,
    })
    # Deja que flask-limiter devuelva su respuesta estándar 429
    raise e
