"""
middlewares/jwt_auth.py — Autenticación mediante JWT (JSON Web Tokens)

SEGURIDAD NUEVA: Este archivo añade protección por token JWT para la API REST.
Antes, las rutas /api/* no requerían ninguna autenticación. Ahora cualquier
endpoint de la API necesita un token válido en el header Authorization.

Flujo:
  1. El cliente hace POST /api/auth/token con email+password
  2. Si las credenciales son correctas, recibe un token JWT firmado
  3. Para llamar a /api/* protegidas, envía: Authorization: Bearer <token>
  4. El decorador @jwt_required verifica la firma y la expiración del token

Ventajas sobre solo-sesiones:
  - Los tokens son stateless (no hay sesión en servidor)
  - Cada token lleva embebido el user_id y rol → no hay consulta a BD
  - Expiran automáticamente (por defecto 24 h, configurable en settings.py)
  - Si el SECRET_KEY rota, todos los tokens anteriores quedan inválidos
"""

import jwt                          # PyJWT — pip install PyJWT
import json
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app
from src.config.logger import log_security


# ---------------------------------------------------------------------------
# Generación de token JWT
# ---------------------------------------------------------------------------

def generate_jwt(user_id: int, email: str, rol: str = 'cliente') -> str:
    """
    Crea y firma un token JWT con los datos del usuario.

    SEGURIDAD:
      - 'exp': el token expira automáticamente (evita tokens eternos)
      - 'iat': fecha de emisión para auditoría
      - Firmado con JWT_SECRET de settings.py (HS256 simétrico)

    Args:
        user_id: ID del usuario en la BD
        email:   email del usuario
        rol:     'cliente' o 'admin'

    Returns:
        Token JWT como string (enviar en header Authorization: Bearer <token>)
    """
    secret = current_app.config['JWT_SECRET']
    expires_hours = current_app.config.get('JWT_EXPIRES_HOURS', 24)

    payload = {
        'sub': user_id,                                      # subject (ID del usuario)
        'email': email,                                      # dato embebido — sin consulta a BD
        'rol': rol,                                          # para control de acceso por rol
        'iat': datetime.now(timezone.utc),                   # issued at
        'exp': datetime.now(timezone.utc) + timedelta(hours=expires_hours)  # expiry
    }
    # HS256 = HMAC-SHA256 — algoritmo simétrico, suficiente para APIs internas
    return jwt.encode(payload, secret, algorithm='HS256')


# ---------------------------------------------------------------------------
# Decodificación / verificación de token
# ---------------------------------------------------------------------------

def decode_jwt(token: str) -> dict | None:
    """
    Verifica la firma y la expiración del token.

    SEGURIDAD:
      - jwt.decode() lanza ExpiredSignatureError si el token ya expiró
      - Lanza InvalidTokenError si la firma no coincide (token alterado)
      - Nunca se confía en el payload sin verificar primero la firma

    Returns:
        payload dict si el token es válido, None si no lo es
    """
    secret = current_app.config['JWT_SECRET']
    try:
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        # Token expirado: el usuario debe obtener uno nuevo
        return None
    except jwt.InvalidTokenError:
        # Firma inválida o token mal formado: posible ataque
        return None


# ---------------------------------------------------------------------------
# Decorador: @jwt_required
# ---------------------------------------------------------------------------

def jwt_required(f):
    """
    Decorador que protege rutas de la API con autenticación JWT.

    SEGURIDAD:
      - Rechaza peticiones sin header Authorization (401)
      - Rechaza tokens con firma inválida o expirados (401)
      - Registra intentos de acceso con token inválido (log de seguridad)
      - Inyecta `jwt_payload` en kwargs para que la ruta acceda a user_id/rol

    Uso:
        @api_bp.route('/mis-solicitudes')
        @jwt_required
        def mis_solicitudes_api():
            uid = request.jwt_payload['sub']
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        # SEGURIDAD: el header debe tener el esquema "Bearer <token>"
        if not auth_header.startswith('Bearer '):
            log_security('jwt_missing_token', {
                'ip': request.remote_addr,
                'path': request.path
            })
            return jsonify({'success': False, 'error': 'Token de autorización requerido'}), 401

        token = auth_header[7:]  # Eliminar el prefijo "Bearer "
        payload = decode_jwt(token)

        if payload is None:
            # SEGURIDAD: no revelar si el token expiró o si la firma es inválida
            log_security('jwt_invalid_token', {
                'ip': request.remote_addr,
                'path': request.path,
                'token_prefix': token[:10] + '...'   # solo prefijo para logs (no el token completo)
            })
            return jsonify({'success': False, 'error': 'Token inválido o expirado'}), 401

        # Adjuntar el payload al contexto de la petición para uso en la ruta
        request.jwt_payload = payload
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# Decorador: @jwt_admin_required
# ---------------------------------------------------------------------------

def jwt_admin_required(f):
    """
    Extiende jwt_required: además verifica que el rol en el token sea 'admin'.

    SEGURIDAD:
      - Un token de usuario cliente no puede acceder a rutas de admin
      - El rol está embebido y firmado en el token → no se puede falsificar
    """
    @wraps(f)
    @jwt_required                      # primero verificar que el token sea válido
    def decorated(*args, **kwargs):
        payload = request.jwt_payload
        if payload.get('rol') != 'admin':
            log_security('jwt_unauthorized_role', {
                'user_id': payload.get('sub'),
                'rol': payload.get('rol'),
                'path': request.path,
                'ip': request.remote_addr
            })
            return jsonify({'success': False, 'error': 'Acceso denegado: se requiere rol admin'}), 403
        return f(*args, **kwargs)

    return decorated
