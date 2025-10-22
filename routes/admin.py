from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import User, Professional, Client, Appointment, Specialty
from forms import SpecialtyForm
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorador para verificar si el usuario es administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('No tienes permisos para acceder a esta sección', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.before_request
def check_admin():
    """Check if user is admin before each request"""
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('No tienes permisos para acceder a esta sección', 'danger')
        return redirect(url_for('main.index'))
        
# Ruta directa para acceso de administrador
@admin_bp.route('/acceso')
@admin_required
def admin_access():
    """Ruta directa para acceso de administrador"""
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard with statistics"""
    # User statistics
    total_users = User.query.count()
    total_professionals = Professional.query.count()
    total_clients = Client.query.count()
    
    # Appointment statistics
    total_appointments = Appointment.query.count()
    pending_appointments = Appointment.query.filter_by(status='pending').count()
    confirmed_appointments = Appointment.query.filter_by(status='confirmed').count()
    cancelled_appointments = Appointment.query.filter_by(status='cancelled').count()
    completed_appointments = Appointment.query.filter_by(status='completed').count()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Recent appointments
    from sqlalchemy.orm import aliased
    
    # Crear alias para User para diferenciar entre profesional y cliente
    ProfessionalUser = aliased(User)
    ClientUser = aliased(User)
    
    recent_appointments = db.session.query(
        Appointment, ProfessionalUser, ClientUser
    ).join(
        Professional, Appointment.professional_id == Professional.id
    ).join(
        ProfessionalUser, Professional.user_id == ProfessionalUser.id
    ).join(
        Client, Appointment.client_id == Client.id
    ).join(
        ClientUser, Client.user_id == ClientUser.id
    ).order_by(
        Appointment.created_at.desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          total_professionals=total_professionals,
                          total_clients=total_clients,
                          total_appointments=total_appointments,
                          pending_appointments=pending_appointments,
                          confirmed_appointments=confirmed_appointments,
                          cancelled_appointments=cancelled_appointments,
                          completed_appointments=completed_appointments,
                          recent_users=recent_users,
                          recent_appointments=recent_appointments)

@admin_bp.route('/users')
@login_required
def users():
    """Manage users"""
    role_filter = request.args.get('role', 'all')
    
    # Base query
    query = User.query
    
    # Apply role filter
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    
    # Get users with pagination
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    users = pagination.items
    
    return render_template('admin/users.html',
                          users=users,
                          pagination=pagination,
                          role_filter=role_filter,
                          current_user=current_user)

@admin_bp.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    """Activate or deactivate a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating own account
    if user.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    action = "activada" if user.is_active else "desactivada"
    flash(f'Cuenta {action} correctamente', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting own account
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta', 'danger')
        return redirect(url_for('admin.users'))
    
    # Check if user is a professional with appointments
    if user.is_professional():
        professional = Professional.query.filter_by(user_id=user.id).first()
        if professional and Appointment.query.filter_by(professional_id=professional.id).count() > 0:
            flash('No se puede eliminar este profesional porque tiene citas asociadas', 'danger')
            return redirect(url_for('admin.users'))
    
    # Check if user is a client with appointments
    if user.is_client():
        client = Client.query.filter_by(user_id=user.id).first()
        if client and Appointment.query.filter_by(client_id=client.id).count() > 0:
            flash('No se puede eliminar este cliente porque tiene citas asociadas', 'danger')
            return redirect(url_for('admin.users'))
    
    # Delete associated profiles
    if user.is_professional():
        professional = Professional.query.filter_by(user_id=user.id).first()
        if professional:
            db.session.delete(professional)
    
    if user.is_client():
        client = Client.query.filter_by(user_id=user.id).first()
        if client:
            db.session.delete(client)
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuario eliminado correctamente', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/specialties', methods=['GET', 'POST'])
@login_required
def specialties():
    """Manage specialties"""
    form = SpecialtyForm()
    
    if form.validate_on_submit():
        # Check if specialty already exists
        existing = Specialty.query.filter_by(name=form.name.data).first()
        if existing:
            flash('Esta especialidad ya existe', 'warning')
        else:
            specialty = Specialty(
                name=form.name.data,
                description=form.description.data
            )
            db.session.add(specialty)
            db.session.commit()
            flash('Especialidad agregada correctamente', 'success')
        
        return redirect(url_for('admin.specialties'))
    
    # Get all specialties with pagination
    page = request.args.get('page', 1, type=int)
    pagination = Specialty.query.order_by(Specialty.name).paginate(
        page=page, per_page=10, error_out=False)
    specialties = pagination.items
    
    return render_template('admin/specialties.html',
                          form=form,
                          specialties=specialties,
                          pagination=pagination)

@admin_bp.route('/edit_specialty/<int:specialty_id>', methods=['GET', 'POST'])
@login_required
def edit_specialty(specialty_id):
    """Edit a specialty"""
    specialty = Specialty.query.get_or_404(specialty_id)
    form = SpecialtyForm()
    
    if form.validate_on_submit():
        # Check if new name conflicts with existing specialties
        existing = Specialty.query.filter(
            Specialty.name == form.name.data,
            Specialty.id != specialty_id
        ).first()
        
        if existing:
            flash('Ya existe otra especialidad con este nombre', 'warning')
        else:
            specialty.name = form.name.data
            specialty.description = form.description.data
            db.session.commit()
            flash('Especialidad actualizada correctamente', 'success')
            return redirect(url_for('admin.specialties'))
    
    elif request.method == 'GET':
        form.name.data = specialty.name
        form.description.data = specialty.description
    
    return render_template('admin/edit_specialty.html',
                          form=form,
                          specialty=specialty)

@admin_bp.route('/delete_specialty/<int:specialty_id>', methods=['POST'])
@login_required
def delete_specialty(specialty_id):
    """Delete a specialty"""
    specialty = Specialty.query.get_or_404(specialty_id)
    
    # Check if specialty is used by any professional
    if specialty.professionals:
        flash('No se puede eliminar esta especialidad porque está siendo utilizada por profesionales', 'danger')
        return redirect(url_for('admin.specialties'))
    
    db.session.delete(specialty)
    db.session.commit()
    
    flash('Especialidad eliminada correctamente', 'success')
    return redirect(url_for('admin.specialties'))
