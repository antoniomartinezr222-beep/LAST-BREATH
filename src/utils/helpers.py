"""
utils/helpers.py - Funciones reutilizables
"""
from datetime import datetime

def format_price(value):
    """Formatear precio en pesos colombianos"""
    return f"${value:,.0f}"

def format_date(dt):
    """Formatear fecha en español"""
    meses = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    return f"{dt.day} de {meses[dt.month]} de {dt.year}, {dt.strftime('%H:%M')}"

def get_estado_badge(estado):
    """Retornar clase CSS según estado"""
    badges = {
        'Pendiente': 'badge-warning',
        'En Proceso': 'badge-info',
        'Completado': 'badge-success',
        'Cancelado': 'badge-danger'
    }
    return badges.get(estado, 'badge-secondary')

def allowed_file(filename, allowed_extensions):
    """Verificar extensión de archivo permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def paginate_query(query, page, per_page=10):
    """Paginar una query de SQLAlchemy"""
    return query.paginate(page=page, per_page=per_page, error_out=False)
