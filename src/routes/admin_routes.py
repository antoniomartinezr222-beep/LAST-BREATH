"""
routes/admin_routes.py - Rutas del panel de administración (versión segura)
Añade rate limiting en login para prevenir fuerza bruta.
"""
from flask import Blueprint
from src.controllers import admin_controller
from src.middlewares.auth import admin_required
from src.middlewares.rate_limiter import limiter, AUTH_LIMIT

admin_bp = Blueprint('admin', __name__)

# Login con rate limit de autenticación (5 intentos / 15 min)
@admin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(AUTH_LIMIT)
def login():
    return admin_controller.login()

admin_bp.route('/logout')(admin_controller.logout)
admin_bp.route('/')(admin_required(admin_controller.dashboard))
admin_bp.route('/solicitudes/<int:solicitud_id>')(admin_required(admin_controller.ver_solicitud))
admin_bp.route('/solicitudes/<int:solicitud_id>/editar',
               methods=['GET', 'POST'])(admin_required(admin_controller.editar_solicitud))
admin_bp.route('/clientes')(admin_required(admin_controller.clientes))
