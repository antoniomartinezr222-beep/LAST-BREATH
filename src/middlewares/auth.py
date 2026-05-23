"""
middlewares/auth.py - Autenticación y autorización (versión segura)
Equivalente a tccpdss: Auth.js + authorization.js

Combina:
  - Sesiones Flask (admin_required / login_required) — como antes
  - Log de acceso denegado — nuevo
  - validate_request_data — como antes
"""
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from src.config.logger import log_access_denied


# ---------------------------------------------------------------------------
# Autenticación de administrador
# ---------------------------------------------------------------------------

def admin_required(f):
    """Middleware: requiere sesión de administrador activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged'):
            # Registrar acceso denegado
            log_access_denied(
                username=session.get('admin_username', 'anonymous'),
                resource=f"{request.method} {request.path}",
                ip=request.remote_addr or 'unknown'
            )
            if request.is_json:
                return jsonify({'success': False, 'error': 'No autorizado'}), 401
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Autenticación de usuario cliente
# ---------------------------------------------------------------------------

def login_required(f):
    """Middleware: requiere sesión de usuario cliente activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            log_access_denied(
                username='anonymous',
                resource=f"{request.method} {request.path}",
                ip=request.remote_addr or 'unknown'
            )
            if request.is_json:
                return jsonify({'success': False, 'error': 'Debes iniciar sesión'}), 401
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Validación de campos JSON requeridos (igual que antes)
# ---------------------------------------------------------------------------

def validate_request_data(required_fields):
    """Middleware factory: valida campos requeridos en JSON."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'Datos requeridos'}), 400
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                return jsonify({
                    'success': False,
                    'error': f'Campos faltantes: {", ".join(missing)}'
                }), 400
            return f(*args, **kwargs)
        return decorated
    return decorator
