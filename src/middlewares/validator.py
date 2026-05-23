"""
middlewares/validator.py - Validación de entrada (espejo de tccpdss/validator.js)
Usa marshmallow para validar y sanitizar los datos de los formularios/JSON.
"""
import re
from functools import wraps
from flask import request, jsonify


# ---------------------------------------------------------------------------
# Helpers de validación
# ---------------------------------------------------------------------------

def _is_valid_email(value: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value))


def _sanitize_str(value, max_len: int = 200) -> str:
    """Elimina espacios extremos y trunca."""
    return str(value).strip()[:max_len]


# ---------------------------------------------------------------------------
# Esquemas de validación (dict con reglas mínimas)
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors  # list[str]
        super().__init__(str(errors))


def _validate_login(data: dict):
    errors = []
    if not data.get('email') and not data.get('usuario'):
        errors.append('El usuario/email es requerido')
    if not data.get('password'):
        errors.append('La contraseña es requerida')
    if errors:
        raise ValidationError(errors)


def _validate_registro(data: dict):
    errors = []
    nombre = data.get('nombre', '').strip()
    email  = data.get('email', '').strip()
    password = data.get('password', '')

    if len(nombre) < 2:
        errors.append('El nombre debe tener al menos 2 caracteres')
    if not _is_valid_email(email):
        errors.append('Email inválido')
    if len(password) < 6:
        errors.append('La contraseña debe tener al menos 6 caracteres')
    if errors:
        raise ValidationError(errors)


def _validate_solicitud(data: dict):
    errors = []
    if not data.get('servicio_id'):
        errors.append('El servicio es requerido')
    if not data.get('direccion', '').strip():
        errors.append('La dirección es requerida')
    if errors:
        raise ValidationError(errors)


# Mapa de nombre → función validadora
_VALIDATORS = {
    'login':     _validate_login,
    'registro':  _validate_registro,
    'solicitud': _validate_solicitud,
}


# ---------------------------------------------------------------------------
# Decoradores listos para usar en rutas
# ---------------------------------------------------------------------------

def validate_form(schema_name: str):
    """
    Decorador para rutas de formularios (request.form).
    Uso:  @validate_form('login')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            validator = _VALIDATORS.get(schema_name)
            if validator is None:
                raise ValueError(f"Esquema '{schema_name}' no existe")
            try:
                validator(request.form.to_dict())
            except ValidationError as e:
                from flask import flash, redirect, url_for
                for msg in e.errors:
                    flash(msg, 'danger')
                return redirect(request.referrer or '/')
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_json(schema_name: str):
    """
    Decorador para rutas JSON (request.get_json()).
    Uso:  @validate_json('solicitud')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            validator = _VALIDATORS.get(schema_name)
            if validator is None:
                raise ValueError(f"Esquema '{schema_name}' no existe")
            data = request.get_json() or {}
            try:
                validator(data)
            except ValidationError as e:
                return jsonify({'success': False, 'errors': e.errors}), 400
            return f(*args, **kwargs)
        return decorated
    return decorator
