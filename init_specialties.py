"""Script para inicializar las especialidades en la base de datos

Este script crea las especialidades básicas en la base de datos si no existen.
Ejecútalo una vez para asegurar que las especialidades estén disponibles en el formulario de registro.
"""
from app import app, db
from models import Specialty

def init_specialties():
    """Inicializa las especialidades básicas en la base de datos"""
    # Lista de especialidades a crear
    specialties_data = [
        {'name': 'Medicina General', 'description': 'Atención médica general y preventiva'},
        {'name': 'Psicología', 'description': 'Atención psicológica y salud mental'},
        {'name': 'Nutrición', 'description': 'Asesoramiento nutricional y dietético'},
        {'name': 'Fisioterapia', 'description': 'Rehabilitación física y tratamiento de lesiones'},
        {'name': 'Odontología', 'description': 'Salud dental y tratamientos bucales'},
        {'name': 'Pediatría', 'description': 'Atención médica para niños y adolescentes'},
        {'name': 'Ginecología', 'description': 'Salud femenina y reproductiva'},
        {'name': 'Dermatología', 'description': 'Tratamiento de afecciones de la piel'},
        {'name': 'Cardiología', 'description': 'Diagnóstico y tratamiento de enfermedades del corazón'},
        {'name': 'Oftalmología', 'description': 'Salud visual y tratamiento de enfermedades oculares'}
    ]
    
    # Verificar especialidades existentes
    existing_specialties = {s.name: s for s in Specialty.query.all()}
    print(f"Especialidades existentes: {len(existing_specialties)}")
    
    # Crear especialidades que no existan
    created_count = 0
    for specialty_data in specialties_data:
        if specialty_data['name'] not in existing_specialties:
            specialty = Specialty(
                name=specialty_data['name'],
                description=specialty_data['description']
            )
            db.session.add(specialty)
            created_count += 1
            print(f"Creada especialidad: {specialty_data['name']}")
    
    # Guardar cambios si se crearon especialidades
    if created_count > 0:
        db.session.commit()
        print(f"Se crearon {created_count} especialidades nuevas.")
    else:
        print("No se crearon especialidades nuevas.")
    
    # Mostrar todas las especialidades
    all_specialties = Specialty.query.order_by(Specialty.name).all()
    print("\nLista de todas las especialidades:")
    for specialty in all_specialties:
        print(f"- {specialty.name}")

if __name__ == "__main__":
    with app.app_context():
        print("="*80)
        print("INICIALIZACIÓN DE ESPECIALIDADES".center(80))
        print("="*80)
        init_specialties()
        print("\n" + "="*80)
        print("PROCESO COMPLETADO".center(80))
        print("="*80)