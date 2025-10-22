# Guía de Seguridad

## Autenticación y Autorización

### Gestión de Sesiones
- Uso de Flask-Login para manejo de sesiones
- Sesiones encriptadas con SECRET_KEY
- Tiempo de expiración configurable
- Rotación de tokens

### Roles y Permisos
```python
ROLES = {
    'admin': ['all'],
    'professional': [
        'view_appointments',
        'update_appointments',
        'manage_schedule',
        'view_profile',
        'update_profile'
    ],
    'client': [
        'book_appointments',
        'view_appointments',
        'cancel_appointments',
        'view_profile',
        'update_profile'
    ]
}
```

### Middleware de Autorización
```python
@login_required
@requires_role(['admin', 'professional'])
def protected_route():
    pass
```

## Protección de Datos

### Contraseñas
- Hasheo con Werkzeug Security
- Salt único por usuario
- Política de contraseñas fuerte

### Datos Sensibles
- Encriptación de datos médicos
- Anonimización en logs
- Acceso restringido a información personal

## OWASP Top 10

### 1. Inyección
- Uso de SQLAlchemy ORM
- Parametrización de consultas
- Validación de entrada

### 2. Autenticación Rota
- Bloqueo después de intentos fallidos
- 2FA para administradores
- Tokens seguros

### 3. Exposición de Datos Sensibles
- HTTPS obligatorio
- Datos encriptados en reposo
- Headers de seguridad

### 4. XXE
- Parseo seguro de XML
- Desactivación de entidades externas
- Validación de tipos MIME

### 5. Control de Acceso Roto
- Verificación en cada endpoint
- Principio de menor privilegio
- Auditoría de accesos

### 6. Security Misconfigurations
- Configuraciones por ambiente
- Revisión de dependencias
- Hardening de servidor

### 7. XSS
- Escape de datos en templates
- CSP Headers
- Sanitización de entrada

### 8. Deserialización Insegura
- Validación de tipos
- Límites de tamaño
- Whitelisting de clases

### 9. Componentes Vulnerables
- Actualización regular de dependencias
- Monitoreo de CVEs
- Safety checks

### 10. Logging Insuficiente
- Logs estructurados
- Monitoreo de eventos críticos
- Retención de logs

## Headers de Seguridad

```python
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'",
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

## Protección contra Ataques

### CSRF
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

### Rate Limiting
```python
from flask_limiter import Limiter
limiter = Limiter(app)

@limiter.limit("100/minute")
def protected_route():
    pass
```

### Validación de Entrada
```python
from wtforms.validators import DataRequired, Email

class UserForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
```

## Auditoría y Logging

### Eventos Auditables
- Inicios de sesión
- Cambios en citas
- Accesos administrativos
- Modificaciones de datos

### Formato de Log
```python
{
    'timestamp': '2025-10-22T14:30:00Z',
    'event': 'appointment.create',
    'user_id': '123',
    'ip': '192.168.1.1',
    'data': {
        'appointment_id': '456',
        'action': 'create'
    }
}
```

## Backups y Recuperación

### Política de Backups
- Backup diario de base de datos
- Retención de 30 días
- Encriptación de backups
- Pruebas de restauración

### Plan de Recuperación
1. Detección de incidente
2. Evaluación de impacto
3. Activación de contingencia
4. Restauración de datos
5. Verificación
6. Documentación