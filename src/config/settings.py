"""
config/settings.py - Configuración del proyecto (con seguridad mejorada)
"""
import os
from datetime import timedelta

class Config:
    # SECRET_KEY debe definirse en variable de entorno en producción
    SECRET_KEY = os.environ.get('SECRET_KEY', 'last-breath-secret-2025')

    # JWT
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-last-breath-secret-2025')
    JWT_EXPIRES_HOURS = int(os.environ.get('JWT_EXPIRES_HOURS', 24))

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///last_breath.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # CORS: orígenes permitidos (separados por coma en env)
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')

    # Rate limiting
    RATELIMIT_DEFAULT = "200 per minute"
    RATELIMIT_AUTH = "5 per 15 minutes"

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
