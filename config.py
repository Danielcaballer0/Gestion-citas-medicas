import os

class Config:
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")
    # Usar ruta absoluta para el archivo de base de datos
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30,
        "pool_size": 10,
        "max_overflow": 20
    }
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = 'apikey'
    MAIL_PASSWORD = os.environ.get('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@appointmentmanager.com')
    
    # SendGrid configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    
    # PayPal configuration
    PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
    PAYPAL_PRODUCTION = os.environ.get('PAYPAL_PRODUCTION', 'false').lower() in ['true', 'on', '1']
    
    PAYMENT_GATEWAY = os.environ.get('PAYMENT_GATEWAY', 'paypal')  # Solo se permite PayPal como pasarela de pago
    
    # Google Calendar API
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Application settings
    APPOINTMENTS_PER_PAGE = 10
    PROFESSIONALS_PER_PAGE = 12
    DEFAULT_APPOINTMENT_DURATION = 60  # minutes
    ENABLE_PAYMENT = True  # Enable payment functionality
    APPOINTMENT_COST = 50  # Default cost in currency units
