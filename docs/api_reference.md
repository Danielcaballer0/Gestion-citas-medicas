# Guía de API y Endpoints

## Autenticación

### Registro de Usuario
```
POST /auth/register
Content-Type: application/json

{
    "email": "usuario@ejemplo.com",
    "password": "contraseña",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "role": "client"
}
```

### Inicio de Sesión
```
POST /auth/login
Content-Type: application/json

{
    "email": "usuario@ejemplo.com",
    "password": "contraseña"
}
```

## Gestión de Citas

### Buscar Profesionales
```
GET /api/professionals?specialty=id&date=YYYY-MM-DD
```

### Crear Cita
```
POST /api/appointments
Content-Type: application/json

{
    "professional_id": 123,
    "date": "2025-10-22",
    "time": "14:00",
    "notes": "Consulta general"
}
```

### Obtener Citas del Usuario
```
GET /api/appointments/my
```

### Actualizar Estado de Cita
```
PUT /api/appointments/{id}
Content-Type: application/json

{
    "status": "confirmed"
}
```

## Gestión de Calendario

### Obtener Disponibilidad
```
GET /api/professionals/{id}/availability?date=YYYY-MM-DD
```

### Actualizar Horario
```
PUT /api/professionals/{id}/schedule
Content-Type: application/json

{
    "monday": [
        {"start": "09:00", "end": "13:00"},
        {"start": "15:00", "end": "18:00"}
    ]
    // ... otros días
}
```

## Pagos

### Crear Pago
```
POST /api/payments
Content-Type: application/json

{
    "appointment_id": 456,
    "amount": 100.00,
    "payment_method": "paypal"
}
```

### Verificar Estado de Pago
```
GET /api/payments/{id}/status
```

## Administración

### Gestionar Especialidades
```
GET /api/admin/specialties
POST /api/admin/specialties
PUT /api/admin/specialties/{id}
DELETE /api/admin/specialties/{id}
```

### Gestionar Usuarios
```
GET /api/admin/users
POST /api/admin/users
PUT /api/admin/users/{id}
DELETE /api/admin/users/{id}
```

## Códigos de Respuesta

- 200: Éxito
- 201: Creado
- 400: Solicitud incorrecta
- 401: No autorizado
- 403: Prohibido
- 404: No encontrado
- 500: Error del servidor

## Headers Comunes

```
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json
```

## Paginación

Para endpoints que devuelven listas:

```
GET /api/resource?page=1&per_page=20
```

Respuesta:
```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
}
```

## Rate Limiting

- 100 solicitudes por minuto para clientes autenticados
- 30 solicitudes por minuto para clientes no autenticados

## Webhooks

### PayPal IPN
```
POST /webhooks/paypal
```

### Google Calendar
```
POST /webhooks/google-calendar
```

## Manejo de Errores

Ejemplo de respuesta de error:
```json
{
    "error": {
        "code": "INVALID_INPUT",
        "message": "El campo email es requerido",
        "details": {
            "field": "email",
            "reason": "required"
        }
    }
}
```