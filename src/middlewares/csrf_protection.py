"""
middlewares/csrf_protection.py — Protección contra CSRF (Cross-Site Request Forgery)

SEGURIDAD NUEVA: Previene que sitios externos envíen peticiones en nombre
del usuario sin que él lo sepa.

Problema que resuelve:
  Un atacante crea una página evil.com con un formulario oculto que hace
  POST /solicitar al servidor. Si el usuario tiene sesión abierta, el
  navegador incluye automáticamente las cookies de sesión → solicitud válida.

Solución (Double Submit Cookie / Synchronizer Token Pattern):
  1. Al cargar cualquier formulario se genera un token aleatorio de 32 bytes
  2. El token se guarda en la sesión del servidor (csrf_token)
  3. El template lo incluye como campo oculto <input name="csrf_token">
  4. Al recibir el POST, se compara el valor del formulario con el de la sesión
  5. evil.com no puede leer la sesión del usuario → no puede replicar el token

NOTA: Las rutas JSON (API) con JWT no necesitan CSRF porque no usan cookies.
      CSRF solo aplica a formularios HTML con sesiones basadas en cookies.
"""

import secrets
import hmac
from functools import wraps
from flask import session, request, abort, jsonify
from src.config.logger import log_security


# ---------------------------------------------------------------------------
# Generación del token CSRF
# ---------------------------------------------------------------------------

def get_csrf_token() -> str:
    """
    Obtiene el token CSRF de la sesión actual o crea uno nuevo.

    SEGURIDAD:
      - secrets.token_hex(32) = 64 caracteres hexadecimales (256 bits de entropía)
      - El token es único por sesión de usuario
      - Se regenera al hacer login para evitar fixation attacks

    Returns:
        Token CSRF como string hexadecimal; persiste durante toda la sesión.
    """
    if 'csrf_token' not in session:
        # SEGURIDAD: secrets.token_hex es criptográficamente seguro (no usar random)
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def regenerate_csrf_token() -> str:
    """
    Fuerza la creación de un nuevo token CSRF.
    Llamar después de login para invalidar tokens pre-autenticación.

    SEGURIDAD: Previene CSRF session fixation (un atacante que obtenga el token
    antes del login no puede usarlo después de que el usuario inicia sesión).
    """
    session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


# ---------------------------------------------------------------------------
# Verificación del token CSRF
# ---------------------------------------------------------------------------

def _verify_csrf_token(submitted_token: str) -> bool:
    """
    Compara en tiempo constante el token enviado con el de la sesión.

    SEGURIDAD:
      - hmac.compare_digest evita timing attacks (comparación bit a bit
        en tiempo constante, no se detiene en el primer byte diferente)
      - Un atacante no puede inferir cuántos bytes acertó midiendo el tiempo
    """
    expected = session.get('csrf_token', '')
    if not expected or not submitted_token:
        return False
    # SEGURIDAD: comparación en tiempo constante
    return hmac.compare_digest(expected, submitted_token)


# ---------------------------------------------------------------------------
# Decorador: @csrf_protect
# ---------------------------------------------------------------------------

def csrf_protect(f):
    """
    Decorador que verifica el token CSRF en peticiones POST/PUT/DELETE/PATCH.

    SEGURIDAD:
      - GET, HEAD, OPTIONS son idempotentes → no modifican datos → no necesitan CSRF
      - Busca el token en el formulario (campo 'csrf_token') o en el header
        X-CSRFToken (para peticiones AJAX)
      - Registra intentos de CSRF fallidos en el log de seguridad

    Uso en rutas Flask:
        @web_bp.route('/solicitar', methods=['GET', 'POST'])
        @csrf_protect
        def solicitar():
            ...

    En el template HTML (OBLIGATORIO agregar en cada <form>):
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Solo verificar en métodos que modifican estado
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # Buscar token en form-data o en header AJAX
            submitted = (
                request.form.get('csrf_token') or
                request.headers.get('X-CSRFToken')
            )

            if not _verify_csrf_token(submitted or ''):
                # SEGURIDAD: registrar el intento fallido con IP
                log_security('csrf_validation_failed', {
                    'ip': request.remote_addr,
                    'path': request.path,
                    'method': request.method,
                    'user_id': session.get('user_id', 'anonymous')
                })
                # 403 Forbidden — no 400, para indicar claramente que es un problema de autorización
                abort(403)

        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Helper para Jinja2: exponer csrf_token() en templates
# ---------------------------------------------------------------------------

def init_csrf(app):
    """
    Registra la función csrf_token() como global de Jinja2.

    Llamar en create_app() después de crear la app Flask:
        from src.middlewares.csrf_protection import init_csrf
        init_csrf(app)

    Luego en cualquier template:
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    """
    # SEGURIDAD: disponible en TODOS los templates automáticamente
    app.jinja_env.globals['csrf_token'] = get_csrf_token

    # Manejador global del error 403 por CSRF
    @app.errorhandler(403)
    def csrf_error(e):
        if request.is_json:
            return jsonify({'success': False, 'error': 'Token CSRF inválido o ausente'}), 403
        return '<h1>403 - Acceso Denegado</h1><p>Token de seguridad inválido. Recarga la página e intenta de nuevo.</p>', 403
