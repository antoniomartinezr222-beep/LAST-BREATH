"""
app.py — Configuración principal de la aplicación Flask

SEGURIDAD IMPLEMENTADA (original + nuevas adiciones):
  1. Security Headers (helmet equivalente)   — via security_headers.py
  2. CORS configurado con orígenes            — via flask-cors
  3. Rate Limiting anti fuerza bruta         — via flask-limiter
  4. Sesiones Flask (admin/usuario)          — via auth.py
  5. Autorización por roles                  — via auth.py (admin_required / login_required)
  6. Validación de entrada                   — via validator.py
  7. Logging centralizado JSON               — via logger.py
  8. Error handlers globales                 — 404, 429, 500
  ── NUEVAS ──────────────────────────────────────────────────────────────────
  9. JWT para la API REST                    — via jwt_auth.py  ← NUEVO
 10. Protección CSRF en formularios HTML     — via csrf_protection.py  ← NUEVO
"""
import time
from flask import Flask, jsonify, request
from flask_cors import CORS


def create_app():
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # ── Configuración ────────────────────────────────────────────────────────
    from src.config.settings import Config
    app.config.from_object(Config)

    # ── 1. Security Headers (equivalente a helmet) ────────────────────────────
    from src.middlewares.security_headers import apply_security_headers
    apply_security_headers(app)

    # ── 10. CSRF: registra csrf_token() en Jinja2 y el handler 403 ───────────────────
    # SEGURIDAD NUEVA: protege formularios HTML contra CSRF
    # Los templates deben incluir: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    from src.middlewares.csrf_protection import init_csrf
    init_csrf(app)

    # ── 2. CORS ───────────────────────────────────────────────────────────────
    allowed_origins = app.config.get('ALLOWED_ORIGINS', '*')
    origins = allowed_origins.split(',') if allowed_origins != '*' else '*'
    CORS(app, origins=origins, supports_credentials=True)

    # ── 3. Rate Limiting ──────────────────────────────────────────────────────
    from src.middlewares.rate_limiter import limiter
    limiter.init_app(app)

    # ── 7. Logging de requests HTTP ───────────────────────────────────────────
    from src.config.logger import log_request
    @app.before_request
    def _start_timer():
        request._start_time = time.time()

    @app.after_request
    def _log_request(response):
        duration = (time.time() - getattr(request, '_start_time', time.time())) * 1000
        log_request(
            method=request.method,
            url=request.path,
            status=response.status_code,
            duration_ms=duration,
            ip=request.remote_addr or 'unknown',
            user_agent=request.headers.get('User-Agent', '')
        )
        return response

    # ── Base de datos ─────────────────────────────────────────────────────────
    from src.config.database import init_db
    init_db()

    from src.seeds.initial_data import seed_data
    seed_data()

    # ── Rutas ─────────────────────────────────────────────────────────────────
    from src.routes.web_routes import web_bp
    from src.routes.api_routes import api_bp
    from src.routes.admin_routes import admin_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # ── 8. Manejadores de error globales ──────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Ruta no encontrada'}), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            'success': False,
            'message': 'Demasiadas solicitudes. Intente nuevamente en un momento'
        }), 429

    @app.errorhandler(500)
    def internal_error(e):
        from src.config.logger import logger
        import json
        logger.error(json.dumps({
            "event": "internal_server_error",
            "error": str(e),
            "path": request.path,
            "method": request.method,
            "ip": request.remote_addr
        }))
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route('/api/health')
    def health():
        from datetime import datetime
        return jsonify({
            'success': True,
            'message': 'Servidor funcionando correctamente',
            'timestamp': datetime.utcnow().isoformat()
        })

    return app
