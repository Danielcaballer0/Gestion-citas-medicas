# Sistema de Gestión de Citas Médicas

Este es un sistema web desarrollado con Flask que permite la gestión de citas médicas entre profesionales de la salud y pacientes.

## Características Principales

- Sistema de autenticación para pacientes y profesionales
- Panel de administración para gestionar especialidades y usuarios
- Búsqueda de profesionales por especialidad
- Agendamiento de citas con calendario integrado
- Integración con Google Calendar
- Sistema de pagos a través de PayPal
- Envío de notificaciones por correo electrónico (SendGrid)

## Requisitos Técnicos

- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Login
- Google Calendar API
- PayPal SDK
- SendGrid

## Configuración del Proyecto

1. Clonar el repositorio:
```bash
git clone https://github.com/Danielcaballer0/Gestion-citas-medicas.git
cd Gestion-citas-medicas
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta
DATABASE_URL=sqlite:///instance/database.db
GOOGLE_CALENDAR_CREDENTIALS=path/to/credentials.json
PAYPAL_CLIENT_ID=tu_client_id_paypal
PAYPAL_CLIENT_SECRET=tu_client_secret_paypal
SENDGRID_API_KEY=tu_api_key_sendgrid
```

4. Inicializar la base de datos:
```bash
flask db upgrade
python init_specialties.py
python create_admin.py
```

## Estructura del Proyecto

```
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuraciones
├── models.py             # Modelos de base de datos
├── forms.py              # Formularios WTForms
├── routes/               # Rutas de la aplicación
│   ├── admin.py         # Rutas de administración
│   ├── auth.py          # Rutas de autenticación
│   ├── client.py        # Rutas para clientes
│   └── professional.py   # Rutas para profesionales
├── templates/            # Plantillas HTML
├── static/              # Archivos estáticos
└── utils/               # Utilidades y helpers
```

## Despliegue

Este proyecto está configurado para ser desplegado en Vercel. Para desplegar:

1. Asegúrate de tener la CLI de Vercel instalada:
```bash
npm i -g vercel
```

2. Ejecuta el comando de despliegue:
```bash
vercel
```

3. Sigue las instrucciones en pantalla para completar el despliegue.

## Desarrollo Local

Para ejecutar el proyecto localmente:

```bash
flask run
```

La aplicación estará disponible en `http://localhost:5000`

## Tests

Para ejecutar los tests:

```bash
python -m pytest
```

## Integración con Servicios Externos

### Google Calendar
La documentación para la integración con Google Calendar se encuentra en `docs/google_calendar_integration.md`

### PayPal
La documentación para la integración con PayPal se encuentra en `docs/paypal_integration.md`

## Licencia

MIT License

## Autor

[Danielcaballer0](https://github.com/Danielcaballer0)
