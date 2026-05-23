"""
routes/api_routes.py — Rutas de la API REST

SEGURIDAD MEJORADA:
  - Se añadió el endpoint POST /api/auth/token para obtener un JWT
  - Las rutas de datos (/servicios público, /mis-solicitudes protegido)
    ahora usan @jwt_required para autenticación stateless
  - /api/solicitudes/stats ahora requiere rol admin vía @jwt_admin_required
  - /api/servicios sigue siendo pública (catálogo visible sin login)

Antes: ninguna ruta de API tenía autenticación → cualquiera podía consultar
       estadísticas y datos sin estar logueado.
Ahora: endpoints sensibles requieren token JWT válido en header Authorization.
"""

from flask import Blueprint, jsonify, request
from src.config.database import get_db
from src.services.solicitud_service import SolicitudService, UserService

# ── SEGURIDAD NUEVA: importar middlewares JWT ─────────────────────────────
from src.middlewares.jwt_auth import (
    generate_jwt,
    jwt_required,
    jwt_admin_required
)
from src.middlewares.rate_limiter import limiter, AUTH_LIMIT

api_bp = Blueprint('api', __name__)


# ---------------------------------------------------------------------------
# SEGURIDAD NUEVA: Endpoint de autenticación JWT
# POST /api/auth/token
# Body JSON: {"email": "...", "password": "..."}
# ---------------------------------------------------------------------------

@api_bp.route('/auth/token', methods=['POST'])
@limiter.limit(AUTH_LIMIT)   # SEGURIDAD: rate limit anti fuerza bruta (5/15min)
def obtener_token():
    """
    Genera un token JWT para uso en la API REST.

    SEGURIDAD:
      - Rate limited para prevenir fuerza bruta
      - El token incluye user_id, email y rol → no hay estado en el servidor
      - Mensaje de error genérico: no revela si el email existe o no
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email y contraseña requeridos'}), 400

    user, error = UserService.autenticar_usuario(email, password)
    if error:
        # SEGURIDAD: mismo mensaje para email inexistente y contraseña incorrecta
        return jsonify({'success': False, 'error': 'Credenciales incorrectas'}), 401

    token = generate_jwt(
        user_id=user['id'],
        email=user['email'],
        rol=user.get('rol', 'cliente')
    )

    return jsonify({
        'success': True,
        'token': token,
        'expires_in': 86400,    # segundos (24 horas)
        'token_type': 'Bearer'
    }), 200


# ---------------------------------------------------------------------------
# Ruta pública: catálogo de servicios (no requiere autenticación)
# ---------------------------------------------------------------------------

@api_bp.route('/servicios')
def get_servicios():
    """Lista servicios disponibles. Pública — el catálogo es información pública."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM servicios WHERE disponible=1").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# SEGURIDAD NUEVA: estadísticas solo para admins con JWT
# GET /api/solicitudes/stats
# Header: Authorization: Bearer <token_admin>
# ---------------------------------------------------------------------------

@api_bp.route('/solicitudes/stats')
@jwt_admin_required   # SEGURIDAD: antes era pública, ahora solo admins con JWT
def get_stats():
    """
    SEGURIDAD:
      - Verifica firma y expiración del token
      - Verifica que rol == 'admin' en el payload
      - Un cliente con token válido recibe 403 Forbidden
    """
    return jsonify(SolicitudService.obtener_estadisticas())


# ---------------------------------------------------------------------------
# SEGURIDAD NUEVA: solicitudes propias del usuario autenticado
# GET /api/mis-solicitudes
# Header: Authorization: Bearer <token>
# ---------------------------------------------------------------------------

@api_bp.route('/mis-solicitudes')
@jwt_required   # SEGURIDAD: cualquier usuario autenticado
def get_mis_solicitudes():
    """
    SEGURIDAD IDOR: el user_id viene del TOKEN firmado, no de un parámetro
    de la URL. Un usuario no puede ver solicitudes ajenas aunque conozca el ID.
    """
    user_id = request.jwt_payload['sub']   # extraído del JWT, no del request

    conn = get_db()
    rows = conn.execute("""
        SELECT s.*, sv.nombre as servicio_nombre
        FROM solicitudes s
        JOIN servicios sv ON s.servicio_id = sv.id
        WHERE s.user_id = ?
        ORDER BY s.id DESC
    """, (user_id,)).fetchall()
    conn.close()

    return jsonify({'success': True, 'solicitudes': [dict(r) for r in rows]})
