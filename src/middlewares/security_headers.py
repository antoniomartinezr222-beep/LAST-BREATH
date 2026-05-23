"""
middlewares/security_headers.py - Headers de seguridad HTTP (espejo de helmet en tccpdss)
Aplica Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, etc.
"""
from flask import Flask


def apply_security_headers(app: Flask):
    """
    Registra un after_request que añade los mismos headers que helmet() en tccpdss.
    Llama esta función en create_app() ANTES de registrar blueprints.
    """

    @app.after_request
    def set_security_headers(response):
        # Content-Security-Policy — equivalente a helmet.contentSecurityPolicy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://unpkg.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' https://unpkg.com https://cdn.jsdelivr.net"
        )
        # Evita que el sitio sea embebido en iframes (clickjacking)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Evita MIME-type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions Policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        # HSTS (solo en producción con HTTPS)
        import os
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
