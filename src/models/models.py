"""
models/ - Definición de los modelos de datos
"""
from src.config.database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """Modelo de usuario/cliente"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    password_hash = db.Column(db.String(200))
    rol = db.Column(db.String(20), default='cliente')  # cliente | admin
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    solicitudes = db.relationship('SolicitudServicio', backref='cliente', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'rol': self.rol,
            'creado_en': self.creado_en.strftime('%d de %B de %Y')
        }


class Servicio(db.Model):
    """Modelo de tipos de servicios disponibles"""
    __tablename__ = 'servicios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(50))  # emoji o clase de icono
    precio_base = db.Column(db.Float, default=0.0)
    disponible = db.Column(db.Boolean, default=True)
    
    solicitudes = db.relationship('SolicitudServicio', backref='servicio', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'icono': self.icono,
            'precio_base': self.precio_base,
            'disponible': self.disponible
        }


class SolicitudServicio(db.Model):
    """Modelo de solicitud de servicio"""
    __tablename__ = 'solicitudes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    descripcion = db.Column(db.Text)
    direccion = db.Column(db.String(200), nullable=False)
    estado = db.Column(db.String(30), default='Pendiente')  # Pendiente | En Proceso | Completado | Cancelado
    fecha_solicitud = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_servicio = db.Column(db.DateTime)
    notas_admin = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente': self.cliente.nombre if self.cliente else 'N/A',
            'telefono': self.cliente.telefono if self.cliente else '',
            'servicio': self.servicio.nombre if self.servicio else 'N/A',
            'descripcion': self.descripcion,
            'direccion': self.direccion,
            'estado': self.estado,
            'fecha': self.fecha_solicitud.strftime('%d de %B de %Y, %H:%M'),
            'notas_admin': self.notas_admin
        }


class Admin(db.Model):
    """Modelo de administrador del sistema"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    nombre = db.Column(db.String(100))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
