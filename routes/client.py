from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import User, Client, Professional, Appointment, Specialty
from forms import ClientProfileForm, AppointmentForm, SearchForm
from utils import get_available_slots, send_confirmation_email, get_upcoming_appointments

client_bp = Blueprint('client', __name__)

@client_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Client profile page"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    # Get client profile or create if not exists
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        client = Client(user_id=current_user.id)
        db.session.add(client)
        db.session.commit()
    
    form = ClientProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        client.address = form.address.data
        client.insurance_info = form.insurance_info.data
        
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('client.profile'))
    
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.address.data = client.address
        form.insurance_info.data = client.insurance_info
    
    return render_template('profile.html', form=form, user=current_user)

@client_bp.route('/my_appointments')
@login_required
def my_appointments():
    """View client's appointments"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        flash('Perfil de cliente no encontrado', 'warning')
        return redirect(url_for('client.profile'))
    
    # Get appointments grouped by status
    upcoming = Appointment.query.filter(
        Appointment.client_id == client.id,
        Appointment.date >= datetime.now().date(),
        Appointment.status.in_(['confirmed', 'pending'])
    ).order_by(Appointment.date, Appointment.start_time).all()
    
    past = Appointment.query.filter(
        Appointment.client_id == client.id,
        (Appointment.date < datetime.now().date()) | 
        (Appointment.status == 'cancelled') |
        (Appointment.status == 'completed')
    ).order_by(Appointment.date.desc(), Appointment.start_time).all()
    
    return render_template('my_appointments.html', upcoming=upcoming, past=past)

@client_bp.route('/book_appointment/<int:professional_id>', methods=['GET', 'POST'])
@login_required
def book_appointment(professional_id):
    """Book an appointment with a professional"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    professional = Professional.query.get_or_404(professional_id)
    professional_user = User.query.get(professional.user_id)
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    if not client:
        flash('Perfil de cliente no encontrado', 'warning')
        return redirect(url_for('client.profile'))
    
    form = AppointmentForm()
    
    if form.validate_on_submit():
        # Check if selected time is available
        selected_date = form.date.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        
        # Check if date is in the past
        if selected_date < datetime.now().date():
            flash('No se puede agendar citas para fechas pasadas', 'danger')
            return redirect(url_for('client.book_appointment', professional_id=professional_id))
        
        # Create new appointment
        appointment = Appointment(
            professional_id=professional.id,
            client_id=client.id,
            date=selected_date,
            start_time=start_time,
            end_time=end_time,
            notes=form.notes.data,
            status='pending'
        )
        
        # Validate appointment against schedule and conflicts
        if not appointment.is_valid_time():
            flash('El horario seleccionado está fuera del horario de atención del profesional', 'danger')
        elif appointment.has_conflict():
            flash('El horario seleccionado ya está reservado', 'danger')
        else:
            db.session.add(appointment)
            db.session.commit()
            
            # Send confirmation email
            send_confirmation_email(appointment)
            
            flash('Cita reservada exitosamente. Pendiente de confirmación por el profesional.', 'success')
            return redirect(url_for('client.my_appointments'))
    
    # Get available slots for the next 7 days
    today = datetime.now().date()
    available_days = []
    
    for i in range(14):  # Check next 14 days
        check_date = today + timedelta(days=i)
        slots = get_available_slots(professional.id, check_date)
        if slots:
            available_days.append({
                'date': check_date,
                'slots': slots
            })
    
    return render_template('booking.html', 
                          form=form, 
                          professional=professional,
                          professional_user=professional_user,
                          available_days=available_days)

@client_bp.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    if appointment.client_id != client.id:
        flash('No tienes permiso para cancelar esta cita', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    # Check if appointment is in the future and can be cancelled
    if appointment.date < datetime.now().date():
        flash('No se pueden cancelar citas pasadas', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Send cancellation email
    send_confirmation_email(appointment)
    
    flash('Cita cancelada exitosamente', 'success')
    return redirect(url_for('client.my_appointments'))
