# Seguridad implementada — Last Breath

Basada en el modelo de seguridad de **tccpdss (Clínica Bella Vista)** con Node.js/Express.
Cada capa se traduce 1:1 al stack Python/Flask.

---

## Capas de seguridad

### 1. Security Headers — `src/middlewares/security_headers.py`
**Equivalente a:** `helmet()` en tccpdss (`app.js`)

Añade headers HTTP de seguridad en cada respuesta:

| Header | Valor | Propósito |
|---|---|---|
| Content-Security-Policy | `default-src 'self'; style-src ...` | Previene XSS y carga de recursos no autorizados |
| X-Frame-Options | `SAMEORIGIN` | Anti-clickjacking |
| X-Content-Type-Options | `nosniff` | Previene MIME sniffing |
| Referrer-Policy | `strict-origin-when-cross-origin` | Controla info de referencia |
| Permissions-Policy | `geolocation=(), ...` | Deshabilita APIs del navegador no usadas |
| Strict-Transport-Security | (solo producción) | Fuerza HTTPS |

---

### 2. CORS configurado — `src/app.py`
**Equivalente a:** `cors(corsOptions)` en tccpdss

Permite controlar los orígenes permitidos mediante la variable de entorno `ALLOWED_ORIGINS`.
```
ALLOWED_ORIGINS=https://misitioweb.com,https://admin.misitioweb.com
```

---

### 3. Rate Limiting — `src/middlewares/rate_limiter.py`
**Equivalente a:** `authLimiter` + `apiLimiter` en tccpdss (`rateLimiter.js`)

| Limitador | Rutas | Límite |
|---|---|---|
| `AUTH_LIMIT` | `/login`, `/registro`, `/admin/login` | 5 intentos / 15 minutos |
| `API_LIMIT` (default) | Todas las demás | 200 req / minuto |

Previene ataques de **fuerza bruta** en autenticación.

---

### 4. Autenticación con sesiones — `src/middlewares/auth.py`
**Equivalente a:** `Auth.js` en tccpdss

- `@admin_required` — protege rutas del panel admin
- `@login_required` — protege rutas de usuario cliente
- Cualquier intento sin sesión válida es **registrado en los logs** antes de redirigir

---

### 5. Autorización por roles — `src/middlewares/auth.py`
**Equivalente a:** `authorization.js` en tccpdss

- Administradores: acceso al panel `/admin/`
- Clientes: acceso solo a sus propias solicitudes
- Accesos denegados quedan registrados con IP, usuario y ruta

---

### 6. Validación de entrada — `src/middlewares/validator.py`
**Equivalente a:** `validator.js` (express-validator) en tccpdss

Esquemas disponibles:
- `login` — valida email/usuario y contraseña no vacíos
- `registro` — valida nombre ≥ 2 chars, email válido, contraseña ≥ 6 chars
- `solicitud` — valida servicio_id y dirección requeridos

Uso con decoradores:
```python
@validate_form('login')    # para formularios HTML
@validate_json('solicitud') # para endpoints JSON
```

---

### 7. Logging centralizado — `src/config/logger.py`
**Equivalente a:** `logger.js` (winston) en tccpdss

Genera tres archivos de log con rotación automática (5MB / 5 backups):

| Archivo | Contenido |
|---|---|
| `logs/access.log` | Todos los requests HTTP (método, URL, status, duración, IP) |
| `logs/combined.log` | Eventos de nivel INFO en adelante |
| `logs/error.log` | Solo errores (500, excepciones) |

Funciones de log especializadas:
- `log_login_attempt(username, success, ip, ua)` — intentos de login
- `log_access_denied(username, resource, ip)` — accesos denegados (403)
- `log_security(event, details)` — eventos de seguridad genéricos
- `log_request(...)` — automático via middleware en `app.py`

---

### 8. Manejo de errores global — `src/app.py`
**Equivalente a:** error handlers en tccpdss (`app.js`)

- `404` → JSON `{success: false, message: 'Ruta no encontrada'}`
- `429` → JSON con mensaje de rate limit
- `500` → JSON genérico + log del error completo (sin exponer stack en producción)

---

## Variables de entorno recomendadas

```env
SECRET_KEY=cambia_esto_en_produccion
JWT_SECRET=otro_secreto_seguro
ALLOWED_ORIGINS=https://tudominio.com
FLASK_ENV=production
LOG_LEVEL=INFO
LOG_DIR=logs
```
