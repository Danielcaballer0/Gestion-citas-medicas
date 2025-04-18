from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
from app import db
from models import User, Professional, Client, Specialty
from forms import LoginForm, RegistrationForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Email o contraseña incorrectos', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Esta cuenta ha sido desactivada. Contacte al administrador.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_professional():
                next_page = url_for('professional.dashboard')
            elif user.is_admin():
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('client.my_appointments')
        
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Obtenemos todas las especialidades para el formulario
    specialties = Specialty.query.order_by(Specialty.name).all()
    
    # Preparamos las opciones para el dropdown de especialidades
    specialty_choices = [(0, 'Seleccione una especialidad')] + [(s.id, s.name) for s in specialties]
    
    form = RegistrationForm()
    form.specialty.choices = specialty_choices
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Create professional or client profile based on role
        if user.role == 'professional':
            professional = Professional(user_id=user.id)
            
            # Si se seleccionó una especialidad (diferente de 0), asignarla al profesional
            if form.specialty.data and form.specialty.data > 0:
                specialty = Specialty.query.get(form.specialty.data)
                if specialty:
                    professional.specialties.append(specialty)
            
            db.session.add(professional)
        else:
            client = Client(user_id=user.id)
            db.session.add(client)
        
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Contraseña actual incorrecta', 'danger')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Tu contraseña ha sido actualizada', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('change_password.html', form=form)
