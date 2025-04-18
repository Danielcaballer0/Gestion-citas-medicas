import os
import logging
from app import app
from routes.auth import auth_bp
from routes.client import client_bp
from routes.professional import professional_bp
from routes.admin import admin_bp
from routes.main import main_bp

# Configure logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
