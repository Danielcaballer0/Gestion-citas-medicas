import os
import sys

# Configurar variables de entorno necesarias
os.environ['DATABASE_URL'] = 'sqlite:///app.db'
os.environ['SESSION_SECRET'] = 'dev-secret-key'

# Importar la aplicación después de configurar las variables de entorno
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

if __name__ == '__main__':
    print('Iniciando la aplicación en http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)