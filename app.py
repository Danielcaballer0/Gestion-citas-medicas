import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy base
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()

# Create the app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

# Configure login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Import models
with app.app_context():
    # Import models here to avoid circular imports
    from models import User, Professional, Client, Appointment, Specialty, Schedule
    
    # Create all tables
    db.create_all()

# Register blueprints
from routes.auth import auth_bp
from routes.client import client_bp
from routes.professional import professional_bp
from routes.admin import admin_bp
from routes.main import main_bp

app.register_blueprint(auth_bp)
app.register_blueprint(client_bp, url_prefix='/client')
app.register_blueprint(professional_bp, url_prefix='/professional')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(main_bp)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, 
                          error_message="Página no encontrada"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, 
                          error_message="Error interno del servidor"), 500

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    from sqlalchemy.exc import PendingRollbackError
    try:
        return User.query.get(int(user_id))
    except PendingRollbackError:
        # Si hay una transacción pendiente, hacemos rollback y reintentamos
        db.session.rollback()
        return User.query.get(int(user_id))
