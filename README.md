# 🔧 Last Breath - Sistema de Gestión de Servicios

Plataforma web para la gestión de solicitudes de servicios técnicos del hogar.

## 🚀 Instalación

```bash
pip install -r requirements.txt
python server.py
```

Abre: http://localhost:5000

## 🔑 Credenciales por defecto

**Admin panel** → http://localhost:5000/admin/login
- Usuario: `admin`
- Contraseña: `admin123`

## 📁 Estructura del Proyecto

```
last_breath/
├── server.py              # Punto de inicio del servidor
├── requirements.txt
└── src/
    ├── app.py             # Configuración de Flask
    ├── config/
    │   ├── settings.py    # Variables de configuración
    │   └── database.py    # Conexión a SQLite
    ├── controllers/
    │   ├── web_controller.py    # Vistas del cliente
    │   └── admin_controller.py  # Panel de admin
    ├── middlewares/
    │   └── auth.py        # Verificación de sesión
    ├── models/
    │   └── models.py      # User, Servicio, SolicitudServicio
    ├── routes/
    │   ├── web_routes.py    # Rutas públicas
    │   ├── admin_routes.py  # Rutas /admin/
    │   └── api_routes.py    # API REST /api/
    ├── seeds/
    │   └── initial_data.py  # Datos de prueba
    ├── services/
    │   └── solicitud_service.py  # Lógica de negocio
    └── utils/
        └── helpers.py     # Funciones reutilizables
```

## 🌐 Rutas principales

| Ruta | Descripción |
|------|-------------|
| `/` | Página principal |
| `/servicios` | Catálogo de servicios |
| `/solicitar` | Formulario de solicitud |
| `/mis-solicitudes` | Historial del cliente |
| `/login` | Login cliente |
| `/registro` | Registro cliente |
| `/admin/` | Dashboard admin |
| `/api/servicios` | API REST de servicios |
