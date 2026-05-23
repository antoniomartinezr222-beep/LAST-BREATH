"""
controllers/web_controller.py - Rutas web del cliente (versión segura)
Añade: logging de login de usuarios, validación básica.
"""
from flask import render_template, redirect, url_for, session, request, flash
from src.config.database import get_db
from src.services.solicitud_service import SolicitudService, UserService
from src.config.logger import log_login_attempt


def index():
    conn = get_db()
    servicios = [dict(r) for r in conn.execute(
        "SELECT * FROM servicios WHERE disponible=1"
    ).fetchall()]
    conn.close()
    return render_template('index.html', servicios=servicios)


def servicios():
    conn = get_db()
    svc = [dict(r) for r in conn.execute(
        "SELECT * FROM servicios WHERE disponible=1"
    ).fetchall()]
    conn.close()
    return render_template('servicios.html', servicios=svc)


def solicitar_servicio():
    if not session.get('user_id'):
        flash('Debes iniciar sesión para solicitar un servicio', 'warning')
        return redirect(url_for('web.login'))

    conn = get_db()
    svc = [dict(r) for r in conn.execute(
        "SELECT * FROM servicios WHERE disponible=1"
    ).fetchall()]
    conn.close()
    servicio_id = request.args.get('servicio_id')

    if request.method == 'POST':
        servicio_id = request.form.get('servicio_id')
        direccion   = request.form.get('direccion', '').strip()
        descripcion = request.form.get('descripcion', '').strip()

        if not servicio_id:
            flash('Por favor selecciona un servicio', 'danger')
        elif not direccion:
            flash('La dirección es requerida', 'danger')
        else:
            _, error = SolicitudService.crear_solicitud(
                session['user_id'], servicio_id, direccion, descripcion
            )
            if error:
                flash(error, 'danger')
            else:
                flash('¡Solicitud enviada exitosamente! Te contactaremos pronto.', 'success')
                return redirect(url_for('web.mis_solicitudes'))

    return render_template('solicitar.html', servicios=svc, servicio_seleccionado=servicio_id)


def mis_solicitudes():
    if not session.get('user_id'):
        return redirect(url_for('web.login'))

    conn = get_db()
    rows = conn.execute("""
        SELECT s.*, sv.nombre as servicio_nombre, sv.icono as servicio_icono
        FROM solicitudes s
        JOIN servicios sv ON s.servicio_id = sv.id
        WHERE s.user_id=?
        ORDER BY s.id DESC
    """, (session['user_id'],)).fetchall()
    conn.close()
    solicitudes = [dict(r) for r in rows]
    return render_template('mis_solicitudes.html', solicitudes=solicitudes)


def login():
    if session.get('user_id'):
        return redirect(url_for('web.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        ip       = request.remote_addr or 'unknown'
        ua       = request.headers.get('User-Agent', '')

        # Validación básica
        if not email or not password:
            flash('Email y contraseña son requeridos', 'danger')
            return render_template('login.html')

        user, error = UserService.autenticar_usuario(email, password)
        if error:
            log_login_attempt(email, False, ip, ua)
            flash(error, 'danger')
        else:
            log_login_attempt(email, True, ip, ua)
            session['user_id']     = user['id']
            session['user_nombre'] = user['nombre']
            flash(f"Bienvenido, {user['nombre']}!", 'success')
            return redirect(url_for('web.index'))

    return render_template('login.html')


def registro():
    if request.method == 'POST':
        nombre    = request.form.get('nombre', '').strip()
        email     = request.form.get('email', '').strip()
        telefono  = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        password  = request.form.get('password', '')

        # Validación
        errors = []
        if len(nombre) < 2:
            errors.append('El nombre debe tener al menos 2 caracteres')
        import re
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors.append('Email inválido')
        if len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('registro.html')

        user, error = UserService.registrar_usuario(nombre, email, telefono, direccion, password)
        if error:
            flash(error, 'danger')
        else:
            session['user_id']     = user['id']
            session['user_nombre'] = user['nombre']
            flash('¡Cuenta creada exitosamente!', 'success')
            return redirect(url_for('web.index'))

    return render_template('registro.html')


def logout():
    session.pop('user_id', None)
    session.pop('user_nombre', None)
    return redirect(url_for('web.index'))
