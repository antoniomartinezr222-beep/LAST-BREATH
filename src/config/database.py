"""
config/database.py - Conexión a la base de datos con sqlite3
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'last_breath.db')

def get_db():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Crear todas las tablas"""
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefono TEXT,
            direccion TEXT,
            password_hash TEXT,
            rol TEXT DEFAULT 'cliente',
            activo INTEGER DEFAULT 1,
            creado_en TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            icono TEXT,
            precio_base REAL DEFAULT 0,
            disponible INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS solicitudes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            servicio_id INTEGER NOT NULL,
            descripcion TEXT,
            direccion TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            fecha_solicitud TEXT DEFAULT (datetime('now')),
            notas_admin TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (servicio_id) REFERENCES servicios(id)
        );
    """)
    conn.commit()
    conn.close()
