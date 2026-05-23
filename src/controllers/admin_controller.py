"""
controllers/admin_controller.py - Panel de administración (versión segura)
Añade: logging de login, logging de acceso denegado via middleware.
"""
from flask import render_template, redirect, url_for, session, request, flash
from src.config.database import get_db
from src.services.solicitud_service import SolicitudService
from werkzeug.security import check_password_hash
from src.config.logger import log_login_attempt


def login():
    if session.get('admin_logged'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        ip = request.remote_addr or 'unknown'
        user_agent = request.headers.get('User-Agent', '')

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username=?", (username,)
        ).fetchone()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged'] = True
            session['admin_username'] = admin['username']
            # Log éxito
            log_login_attempt(username, True, ip, user_agent)
            return redirect(url_for('admin.dashboard'))
        else:
            # Log fallo — no revelar si el usuario existe o no
            log_login_attempt(username, False, ip, user_agent)
            flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('admin/login.html')


def logout():
    session.pop('admin_logged', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin.login'))


def dashboard():
    stats = SolicitudService.obtener_estadisticas()
    estado_filtro = request.args.get('estado', 'todos')
    solicitudes = SolicitudService.obtener_solicitudes_filtradas(
        None if estado_filtro == 'todos' else estado_filtro
    )
    return render_template('admin/dashboard.html',
                           stats=stats,
                           solicitudes=solicitudes,
                           estado_filtro=estado_filtro)


def ver_solicitud(solicitud_id):
    solicitud = SolicitudService.obtener_solicitud(solicitud_id)
    if not solicitud:
        flash('Solicitud no encontrada', 'danger')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/ver_solicitud.html', solicitud=solicitud)


def editar_solicitud(solicitud_id):
    solicitud = SolicitudService.obtener_solicitud(solicitud_id)
    if not solicitud:
        flash('Solicitud no encontrada', 'danger')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        nuevo_estado = request.form.get('estado')
        notas = request.form.get('notas', '')
        _, error = SolicitudService.actualizar_estado(solicitud_id, nuevo_estado, notas)
        if error:
            flash(error, 'danger')
        else:
            flash('Solicitud actualizada exitosamente', 'success')
            return redirect(url_for('admin.dashboard'))

    estados = ['Pendiente', 'En Proceso', 'Completado', 'Cancelado']
    return render_template('admin/editar_solicitud.html',
                           solicitud=solicitud, estados=estados)


def clientes():
    conn = get_db()
    users = [dict(r) for r in conn.execute(
        "SELECT * FROM users WHERE rol='cliente' ORDER BY id DESC"
    ).fetchall()]
    conn.close()
    return render_template('admin/clientes.html', clientes=users)
