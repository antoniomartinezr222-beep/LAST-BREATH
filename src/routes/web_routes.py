"""
routes/web_routes.py — Rutas del sitio web público

SEGURIDAD MEJORADA:
  - Rate limiting en login/registro (anti fuerza bruta) — ya existía
  - CSRF protection en login, registro y solicitar  ← NUEVO
    (cada formulario POST debe incluir el campo oculto csrf_token)
"""
from flask import Blueprint
from src.controllers import web_controller
from src.middlewares.rate_limiter import limiter, AUTH_LIMIT
# SEGURIDAD NUEVA: importar decorador CSRF
from src.middlewares.csrf_protection import csrf_protect

web_bp = Blueprint('web', __name__)

web_bp.route('/')(web_controller.index)
web_bp.route('/servicios')(web_controller.servicios)
web_bp.route('/mis-solicitudes')(web_controller.mis_solicitudes)
web_bp.route('/logout')(web_controller.logout)

# SEGURIDAD: Login con rate limit + CSRF
# rate limit: max 5 intentos de login por IP en 15 minutos
# csrf_protect: verifica que el POST venga del propio formulario del sitio
@web_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(AUTH_LIMIT)
@csrf_protect   # SEGURIDAD NUEVA: previene que sitios externos hagan POST al login
def login():
    return web_controller.login()

# SEGURIDAD: Registro con rate limit + CSRF
@web_bp.route('/registro', methods=['GET', 'POST'])
@limiter.limit(AUTH_LIMIT)
@csrf_protect   # SEGURIDAD NUEVA: previene registro masivo desde sitios externos
def registro():
    return web_controller.registro()

# SEGURIDAD: Solicitar servicio con CSRF (ya requiere sesión en el controller)
@web_bp.route('/solicitar', methods=['GET', 'POST'])
@csrf_protect   # SEGURIDAD NUEVA: previene que el usuario sea engañado para crear solicitudes
def solicitar():
    return web_controller.solicitar_servicio()
