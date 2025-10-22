from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app import db
from models import User, Client, Professional, Appointment, Specialty
from forms import ClientProfileForm, AppointmentForm, SearchForm
from utils import get_available_slots, send_confirmation_email, get_upcoming_appointments
from paypal_utils import create_checkout_session, refund_payment
from google_calendar_utils import get_auth_url, add_appointment_to_calendar, get_credentials
import os

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
    
    # Process refund if payment was made
    if appointment.payment_status == 'paid' and appointment.payment_id:
        if refund_payment(appointment.id):
            flash('El pago ha sido reembolsado correctamente', 'success')
        else:
            flash('No se pudo procesar el reembolso automáticamente. Contacte a soporte.', 'warning')
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    # Send cancellation email
    send_confirmation_email(appointment)
    
    flash('Cita cancelada exitosamente', 'success')
    return redirect(url_for('client.my_appointments'))

@client_bp.route('/pay_appointment/<int:appointment_id>')
@login_required
def pay_appointment(appointment_id):
    """Process payment for an appointment"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    if appointment.client_id != client.id:
        flash('No tienes permiso para pagar esta cita', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    # Check if appointment is already paid
    if appointment.payment_status == 'paid':
        flash('Esta cita ya ha sido pagada', 'info')
        return redirect(url_for('client.my_appointments'))
    
    # Check if appointment is cancelled
    if appointment.status == 'cancelled':
        flash('No se puede pagar una cita cancelada', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    # Create Stripe checkout session
    checkout_url = create_checkout_session(appointment.id)
    
    if checkout_url:
        return redirect(checkout_url)
    else:
        flash('Error al procesar el pago. Por favor intente nuevamente.', 'danger')
        return redirect(url_for('client.my_appointments'))

@client_bp.route('/payment/success/<int:appointment_id>')
@login_required
def payment_success(appointment_id):
    """Handle successful payment"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    if appointment.client_id != client.id:
        flash('No tienes permiso para ver esta información', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    # Update appointment status (this is normally done via webhook but serves as a fallback)
    if appointment.payment_status != 'paid':
        appointment.payment_status = 'paid'
        appointment.payment_timestamp = datetime.utcnow()
        # If appointment was pending, set it to confirmed upon payment
        if appointment.status == 'pending':
            appointment.status = 'confirmed'
        db.session.commit()
    
    flash('Pago procesado correctamente. Gracias por tu reserva.', 'success')
    return redirect(url_for('client.my_appointments'))

@client_bp.route('/payment/cancel/<int:appointment_id>')
@login_required
def payment_cancel(appointment_id):
    """Handle cancelled payment"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    flash('El proceso de pago ha sido cancelado. Puedes intentarlo nuevamente más tarde.', 'info')
    return redirect(url_for('client.my_appointments'))

@client_bp.route('/google/authorize')
@login_required
def authorize():
    """Authorize Google Calendar access"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    # Get the authorization URL
    auth_url = get_auth_url()
    
    if not auth_url:
        flash('Error al conectar con Google Calendar. Por favor intente nuevamente.', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    return redirect(auth_url)

@client_bp.route('/google/oauth2callback')
@login_required
def oauth2callback():
    """Callback from Google OAuth2"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    # Verificar que el estado exista en la sesión
    if 'state' not in session:
        flash('Error de autenticación: sesión inválida', 'danger')
        return redirect(url_for('client.my_appointments'))
        
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']
    
    try:
        # Verificar que el archivo de credenciales exista
        client_secrets_file = 'client_secret_678559980772-kftgco67hmaflpdvhetp9ji96s1bcjqe.apps.googleusercontent.com.json'
        if not os.path.exists(client_secrets_file):
            flash('Error: Archivo de credenciales de Google no encontrado', 'danger')
            return redirect(url_for('client.my_appointments'))
            
        # Crear el flujo de autorización
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=['https://www.googleapis.com/auth/calendar'],
            state=state)
            
        # Usamos la URL exacta configurada en el archivo de credenciales para evitar el error redirect_uri_mismatch
        flow.redirect_uri = 'http://localhost:5000/client/google/oauth2callback'
        
        # Obtener la URL completa de la solicitud actual
        authorization_response = request.url
        print(f"URL de respuesta de autorización: {authorization_response}")
        
        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        flow.fetch_token(authorization_response=authorization_response)
        
        # Store credentials in the session.
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        flash('Conectado exitosamente a Google Calendar!', 'success')
        return redirect(url_for('client.my_appointments'))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error detallado: {error_details}")
        flash(f'Error al conectar con Google Calendar: {str(e)}', 'danger')
        return redirect(url_for('client.my_appointments'))

@client_bp.route('/google/sync_appointment/<int:appointment_id>')
@login_required
def sync_appointment(appointment_id):
    """Sync an appointment with Google Calendar"""
    if not current_user.is_client():
        flash('No tienes permisos para acceder a esta página', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if user has Google Calendar connected
    if not get_credentials():
        flash('Necesitas conectar tu cuenta de Google Calendar primero', 'warning')
        return redirect(url_for('client.authorize'))
    
    # Get the appointment
    appointment = Appointment.query.get_or_404(appointment_id)
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    if appointment.client_id != client.id:
        flash('No tienes permiso para sincronizar esta cita', 'danger')
        return redirect(url_for('client.my_appointments'))
    
    # Add the appointment to Google Calendar
    event = add_appointment_to_calendar(appointment.id)
    
    if event:
        flash('Cita sincronizada exitosamente con Google Calendar', 'success')
    else:
        flash('Error al sincronizar la cita con Google Calendar', 'danger')
    
    return redirect(url_for('client.my_appointments'))
