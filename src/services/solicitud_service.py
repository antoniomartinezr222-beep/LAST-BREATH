"""
services/solicitud_service.py - Lógica de negocio para solicitudes
"""
from src.config.database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

class SolicitudService:
    
    @staticmethod
    def crear_solicitud(user_id, servicio_id, direccion, descripcion=''):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO solicitudes (user_id, servicio_id, direccion, descripcion, estado)
            VALUES (?,?,?,?,'Pendiente')
        """, (user_id, servicio_id, direccion, descripcion))
        conn.commit()
        sol_id = cur.lastrowid
        conn.close()
        return sol_id, None
    
    @staticmethod
    def actualizar_estado(solicitud_id, nuevo_estado, notas=''):
        conn = get_db()
        cur = conn.cursor()
        sol = cur.execute("SELECT id FROM solicitudes WHERE id=?", (solicitud_id,)).fetchone()
        if not sol:
            conn.close()
            return None, 'Solicitud no encontrada'
        cur.execute("UPDATE solicitudes SET estado=?, notas_admin=? WHERE id=?",
                    (nuevo_estado, notas, solicitud_id))
        conn.commit()
        conn.close()
        return solicitud_id, None
    
    @staticmethod
    def obtener_estadisticas():
        conn = get_db()
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM solicitudes").fetchone()[0]
        pendientes = cur.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Pendiente'").fetchone()[0]
        en_proceso = cur.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='En Proceso'").fetchone()[0]
        completados = cur.execute("SELECT COUNT(*) FROM solicitudes WHERE estado='Completado'").fetchone()[0]
        clientes = cur.execute("SELECT COUNT(*) FROM users WHERE rol='cliente'").fetchone()[0]
        conn.close()
        return {'total': total, 'pendientes': pendientes, 'en_proceso': en_proceso,
                'completados': completados, 'clientes': clientes}
    
    @staticmethod
    def obtener_solicitudes_filtradas(estado=None):
        conn = get_db()
        cur = conn.cursor()
        if estado and estado != 'todos':
            rows = cur.execute("""
                SELECT s.*, u.nombre as cliente_nombre, u.telefono as cliente_tel,
                       sv.nombre as servicio_nombre, sv.icono as servicio_icono
                FROM solicitudes s
                JOIN users u ON s.user_id = u.id
                JOIN servicios sv ON s.servicio_id = sv.id
                WHERE s.estado=?
                ORDER BY s.id DESC
            """, (estado,)).fetchall()
        else:
            rows = cur.execute("""
                SELECT s.*, u.nombre as cliente_nombre, u.telefono as cliente_tel,
                       sv.nombre as servicio_nombre, sv.icono as servicio_icono
                FROM solicitudes s
                JOIN users u ON s.user_id = u.id
                JOIN servicios sv ON s.servicio_id = sv.id
                ORDER BY s.id DESC
            """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    @staticmethod
    def obtener_solicitud(solicitud_id):
        conn = get_db()
        cur = conn.cursor()
        row = cur.execute("""
            SELECT s.*, u.nombre as cliente_nombre, u.telefono as cliente_tel,
                   u.email as cliente_email,
                   sv.nombre as servicio_nombre, sv.icono as servicio_icono
            FROM solicitudes s
            JOIN users u ON s.user_id = u.id
            JOIN servicios sv ON s.servicio_id = sv.id
            WHERE s.id=?
        """, (solicitud_id,)).fetchone()
        conn.close()
        return dict(row) if row else None


class UserService:
    
    @staticmethod
    def registrar_usuario(nombre, email, telefono, direccion, password):
        conn = get_db()
        cur = conn.cursor()
        existing = cur.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            conn.close()
            return None, 'El email ya está registrado'
        cur.execute("""
            INSERT INTO users (nombre, email, telefono, direccion, password_hash, rol)
            VALUES (?,?,?,?,?,'cliente')
        """, (nombre, email, telefono, direccion, generate_password_hash(password)))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return {'id': user_id, 'nombre': nombre, 'email': email}, None
    
    @staticmethod
    def autenticar_usuario(email, password):
        conn = get_db()
        cur = conn.cursor()
        row = cur.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            return dict(row), None
        return None, 'Credenciales incorrectas'
