"""
seeds/initial_data.py - Datos iniciales del proyecto
"""
from src.config.database import get_db
from werkzeug.security import generate_password_hash

def seed_data():
    """Insertar datos iniciales si no existen"""
    conn = get_db()
    cur = conn.cursor()

    # Admin por defecto
    existing = cur.execute("SELECT id FROM admins WHERE username='admin'").fetchone()
    if not existing:
        cur.execute("INSERT INTO admins (username, password_hash, nombre) VALUES (?,?,?)",
                    ('admin', generate_password_hash('admin123'), 'Administrador'))

    # Servicios base
    count = cur.execute("SELECT COUNT(*) FROM servicios").fetchone()[0]
    if count == 0:
        servicios = [
            ('Plomería y Grifería', 'Reparación de tuberías, instalación de grifos, destape de desagüés y mantenimiento de sistemas hidráulicos.', '🔧', 80000),
            ('Limpieza Especializada', 'Limpieza profunda de hogares, oficinas, post-construcción y desinfección de espacios.', '🧹', 120000),
            ('Electricidad', 'Instalaciones eléctricas, reparación de cortocircuitos, cambio de tomacorrientes y cableado.', '⚡', 90000),
            ('Pintura', 'Pintura interior y exterior de paredes, cielos rasos, fachadas y acabados decorativos.', '🎨', 150000),
            ('Carpintería', 'Instalación y reparación de puertas, ventanas, muebles y estructuras de madera.', '🪚', 100000),
            ('Fumigación', 'Control de plagas, fumigación de cucarachas, ratas, hormigas y desinfección total.', '🦟', 70000),
            # Nuevos servicios
            ('Aires Acondicionados', 'Instalación, mantenimiento y reparación de aires acondicionados split, tipo ventana y sistemas centrales.', '❄️', 110000),
            ('Cerrajería', 'Apertura de cerraduras, cambio de bombines, instalación de chapas de seguridad y duplicado de llaves.', '🔑', 65000),
            ('Impermeabilización', 'Sellado de filtraciones, impermeabilización de terrazas, losas, baños y sótanos con materiales de alta durabilidad.', '💧', 180000),
            ('Instalación de Redes', 'Instalación y configuración de redes de internet, puntos de acceso WiFi, cámaras de seguridad IP y sistemas de cableado estructurado.', '📡', 95000),
            ('Jardinería y Paisajismo', 'Diseño, mantenimiento y recuperación de jardines, poda de árboles, siembra de césped y ornamentales.', '🌿', 85000),
            ('Remodelación de Baños y Cocinas', 'Renovación integral de baños y cocinas: enchapes, grifería, mesones, gabinetes y acabados modernos.', '🏠', 350000),
        ]
        for s in servicios:
            cur.execute("INSERT INTO servicios (nombre, descripcion, icono, precio_base) VALUES (?,?,?,?)", s)

    conn.commit()
    conn.close()
