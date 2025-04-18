from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import User, Professional, Specialty, Schedule, Appointment
from forms import ProfessionalProfileForm, ScheduleForm, AppointmentStatusForm
from utils import send_confirmation_email, get_upcoming_appointments

professional_bp = Blueprint('professional', __name__)

@professional_bp.route('/dashboard')
@login_required
def dashboard():
    """Professional dashboard"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional:
        flash('Perfil de profesional no encontrado', 'warning')
        return redirect(url_for('professional.profile'))
    
    # Get upcoming appointments
    today = datetime.now().date()
    upcoming_appointments = Appointment.query.filter(
        Appointment.professional_id == professional.id,
        Appointment.date >= today,
        Appointment.status.in_(['confirmed', 'pending'])
    ).order_by(Appointment.date, Appointment.start_time).limit(5).all()
    
    # Get appointment statistics
    total_appointments = Appointment.query.filter_by(professional_id=professional.id).count()
    pending_appointments = Appointment.query.filter_by(
        professional_id=professional.id, status='pending').count()
    confirmed_appointments = Appointment.query.filter_by(
        professional_id=professional.id, status='confirmed').count()
    
    # Get today's appointments
    today_appointments = Appointment.query.filter(
        Appointment.professional_id == professional.id,
        Appointment.date == today,
        Appointment.status.in_(['confirmed', 'pending'])
    ).order_by(Appointment.start_time).all()
    
    return render_template('professional/dashboard.html',
                          professional=professional,
                          upcoming_appointments=upcoming_appointments,
                          today_appointments=today_appointments,
                          total_appointments=total_appointments,
                          pending_appointments=pending_appointments,
                          confirmed_appointments=confirmed_appointments)

@professional_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Professional profile page"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    # Get professional profile or create if not exists
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional:
        professional = Professional(user_id=current_user.id)
        db.session.add(professional)
        db.session.commit()
    
    # Get all specialties for the form
    all_specialties = Specialty.query.order_by(Specialty.name).all()
    
    form = ProfessionalProfileForm()
    form.specialties.choices = [(s.id, s.name) for s in all_specialties]
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        professional.address = form.address.data
        professional.bio = form.bio.data
        professional.years_experience = form.years_experience.data
        professional.accepts_insurance = form.accepts_insurance.data
        
        # Update specialties
        professional.specialties = [Specialty.query.get(spec_id) for spec_id in form.specialties.data]
        
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('professional.profile'))
    
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.address.data = professional.address
        form.bio.data = professional.bio
        form.years_experience.data = professional.years_experience
        form.accepts_insurance.data = professional.accepts_insurance
        form.specialties.data = [s.id for s in professional.specialties]
    
    return render_template('profile.html', 
                          form=form, 
                          user=current_user, 
                          professional=professional, 
                          is_professional=True)

@professional_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    """Manage professional's schedule"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional:
        flash('Perfil de profesional no encontrado', 'warning')
        return redirect(url_for('professional.profile'))
    
    form = ScheduleForm()
    
    if form.validate_on_submit():
        # Check if schedule already exists for this day
        existing_schedule = Schedule.query.filter_by(
            professional_id=professional.id,
            day_of_week=form.day_of_week.data
        ).first()
        
        if existing_schedule:
            existing_schedule.start_time = form.start_time.data
            existing_schedule.end_time = form.end_time.data
            flash('Horario actualizado correctamente', 'success')
        else:
            new_schedule = Schedule(
                professional_id=professional.id,
                day_of_week=form.day_of_week.data,
                start_time=form.start_time.data,
                end_time=form.end_time.data
            )
            db.session.add(new_schedule)
            flash('Horario agregado correctamente', 'success')
        
        db.session.commit()
        return redirect(url_for('professional.schedule'))
    
    # Get current schedules
    schedules = Schedule.query.filter_by(professional_id=professional.id).all()
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    return render_template('professional/schedule.html', 
                          form=form, 
                          schedules=schedules,
                          days=days)

@professional_bp.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete a schedule entry"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    
    if schedule.professional_id != professional.id:
        flash('No tienes permiso para eliminar este horario', 'danger')
        return redirect(url_for('professional.schedule'))
    
    db.session.delete(schedule)
    db.session.commit()
    
    flash('Horario eliminado correctamente', 'success')
    return redirect(url_for('professional.schedule'))

@professional_bp.route('/appointments')
@login_required
def appointments():
    """View and manage appointments"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional:
        flash('Perfil de profesional no encontrado', 'warning')
        return redirect(url_for('professional.profile'))
    
    # Filter parameters
    status = request.args.get('status', 'all')
    date_filter = request.args.get('date', 'upcoming')
    
    # Base query
    query = Appointment.query.filter_by(professional_id=professional.id)
    
    # Apply status filter
    if status != 'all':
        query = query.filter_by(status=status)
    
    # Apply date filter
    today = datetime.now().date()
    if date_filter == 'upcoming':
        query = query.filter(Appointment.date >= today)
    elif date_filter == 'past':
        query = query.filter(Appointment.date < today)
    elif date_filter == 'today':
        query = query.filter(Appointment.date == today)
    
    # Order by date and time
    if date_filter == 'past':
        appointments = query.order_by(Appointment.date.desc(), Appointment.start_time).all()
    else:
        appointments = query.order_by(Appointment.date, Appointment.start_time).all()
    
    return render_template('professional/appointments.html',
                          appointments=appointments,
                          status_filter=status,
                          date_filter=date_filter)

@professional_bp.route('/update_appointment/<int:appointment_id>', methods=['GET', 'POST'])
@login_required
def update_appointment(appointment_id):
    """Update appointment status"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    
    if appointment.professional_id != professional.id:
        flash('No tienes permiso para actualizar esta cita', 'danger')
        return redirect(url_for('professional.appointments'))
    
    form = AppointmentStatusForm()
    
    if form.validate_on_submit():
        appointment.status = form.status.data
        appointment.notes = form.notes.data
        db.session.commit()
        
        # Send confirmation email for status change
        send_confirmation_email(appointment)
        
        flash('Estado de la cita actualizado correctamente', 'success')
        return redirect(url_for('professional.appointments'))
    
    elif request.method == 'GET':
        form.status.data = appointment.status
        form.notes.data = appointment.notes
    
    return render_template('professional/update_appointment.html',
                          form=form,
                          appointment=appointment)

@professional_bp.route('/calendar')
@login_required
def calendar():
    """Calendar view of appointments"""
    if not current_user.is_professional():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional:
        flash('Perfil de profesional no encontrado', 'warning')
        return redirect(url_for('professional.profile'))
    
    return render_template('professional/calendar.html', professional=professional)

@professional_bp.route('/api/appointments')
@login_required
def api_appointments():
    """API endpoint to get appointments for calendar"""
    if not current_user.is_professional():
        return jsonify({'error': 'Unauthorized'}), 403
    
    professional = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional:
        return jsonify({'error': 'Professional profile not found'}), 404
    
    # Get date range from request
    start = request.args.get('start', datetime.now().date().isoformat())
    end = request.args.get('end', (datetime.now().date() + timedelta(days=30)).isoformat())
    
    # Get appointments in date range
    appointments = Appointment.query.filter(
        Appointment.professional_id == professional.id,
        Appointment.date >= start,
        Appointment.date <= end
    ).all()
    
    # Format appointments for FullCalendar
    events = []
    status_colors = {
        'pending': '#ffc107',  # warning
        'confirmed': '#28a745',  # success
        'cancelled': '#dc3545',  # danger
        'completed': '#17a2b8'   # info
    }
    
    for appointment in appointments:
        client_name = f"{appointment.client.user.first_name} {appointment.client.user.last_name}"
        events.append({
            'id': appointment.id,
            'title': f"Cita con {client_name}",
            'start': f"{appointment.date.isoformat()}T{appointment.start_time.isoformat()}",
            'end': f"{appointment.date.isoformat()}T{appointment.end_time.isoformat()}",
            'color': status_colors.get(appointment.status, '#6c757d'),
            'extendedProps': {
                'status': appointment.status,
                'clientName': client_name,
                'notes': appointment.notes
            }
        })
    
    return jsonify(events)
