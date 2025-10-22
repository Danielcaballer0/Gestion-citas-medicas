from app import app, db
from models import User

# Script para crear un usuario administrador
with app.app_context():
    # Verificar si ya existe un administrador
    admin = User.query.filter_by(role='admin').first()
    
    if admin:
        print(f'Ya existe un administrador: {admin.email}')
    else:
        # Crear nuevo administrador
        new_admin = User(
            username='admin',
            email='admin@sistema.com',
            first_name='Administrador',
            last_name='Sistema',
            phone='123456789',
            role='admin'
        )
        
        # Establecer contraseña
        new_admin.set_password('Admin123!')
        
        # Guardar en la base de datos
        db.session.add(new_admin)
        db.session.commit()
        
        print(f'Administrador creado con éxito:')
        print(f'Email: admin@sistema.com')
        print(f'Contraseña: Admin123!')