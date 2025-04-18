from datetime import datetime, timedelta
from flask import flash
from flask_mail import Message
from app import mail, db
from models import Appointment, Schedule

def send_confirmation_email(appointment):
    """Send appointment confirmation email to client"""
    client_email = appointment.client.user.email
    professional_name = appointment.professional.user.get_full_name()
    appointment_date = appointment.date.strftime('%d/%m/%Y')
    appointment_time = appointment.start_time.strftime('%H:%M')
    
    msg = Message(
        subject=f'Confirmación de Cita con {professional_name}',
        recipients=[client_email]
    )
    
    msg.html = f'''
    <h2>Confirmación de Cita</h2>
    <p>Hola {appointment.client.user.first_name},</p>
    <p>Tu cita ha sido <strong>{get_status_display(appointment.status)}</strong>.</p>
    <p><strong>Profesional:</strong> {professional_name}</p>
    <p><strong>Fecha:</strong> {appointment_date}</p>
    <p><strong>Hora:</strong> {appointment_time}</p>
    <p><strong>Estado:</strong> {get_status_display(appointment.status)}</p>
    
    <p>Si necesitas realizar algún cambio, por favor contacta con el profesional o ingresa a tu cuenta.</p>
    <p>Gracias por usar nuestro servicio.</p>
    '''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        flash(f"Error al enviar email: {str(e)}", "danger")
        return False

def send_reminder_email(appointment):
    """Send appointment reminder email to client"""
    client_email = appointment.client.user.email
    professional_name = appointment.professional.user.get_full_name()
    appointment_date = appointment.date.strftime('%d/%m/%Y')
    appointment_time = appointment.start_time.strftime('%H:%M')
    
    msg = Message(
        subject=f'Recordatorio de Cita con {professional_name}',
        recipients=[client_email]
    )
    
    msg.html = f'''
    <h2>Recordatorio de Cita</h2>
    <p>Hola {appointment.client.user.first_name},</p>
    <p>Te recordamos que tienes una cita programada para mañana.</p>
    <p><strong>Profesional:</strong> {professional_name}</p>
    <p><strong>Fecha:</strong> {appointment_date}</p>
    <p><strong>Hora:</strong> {appointment_time}</p>
    
    <p>Si necesitas cancelar o reprogramar, por favor hazlo con al menos 24 horas de anticipación.</p>
    <p>Gracias por usar nuestro servicio.</p>
    '''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        flash(f"Error al enviar recordatorio: {str(e)}", "danger")
        return False

def get_available_slots(professional_id, date):
    """Get available appointment slots for a professional on a specific date"""
    day_of_week = date.weekday()
    
    # Get the professional's schedule for this day
    schedules = Schedule.query.filter_by(
        professional_id=professional_id,
        day_of_week=day_of_week
    ).all()
    
    if not schedules:
        return []
    
    # Get all appointments for this professional on this date
    appointments = Appointment.query.filter(
        Appointment.professional_id == professional_id,
        Appointment.date == date,
        Appointment.status != 'cancelled'
    ).all()
    
    # Create time slots (default 1 hour)
    slots = []
    for schedule in schedules:
        current_time = schedule.start_time
        end_time = schedule.end_time
        
        while current_time < end_time:
            slot_end = (datetime.combine(date, current_time) + timedelta(hours=1)).time()
            
            if slot_end > end_time:
                slot_end = end_time
                
            # Check if slot is available (not booked)
            is_available = True
            for appointment in appointments:
                # If there is any overlap with existing appointment, slot is not available
                if (current_time < appointment.end_time and 
                    slot_end > appointment.start_time):
                    is_available = False
                    break
            
            if is_available:
                slots.append({
                    'start': current_time,
                    'end': slot_end
                })
                
            # Move to next slot
            current_time = slot_end
    
    return slots

def get_status_display(status):
    """Convert status code to display text"""
    status_map = {
        'pending': 'Pendiente',
        'confirmed': 'Confirmada',
        'cancelled': 'Cancelada',
        'completed': 'Completada'
    }
    return status_map.get(status, status)

def get_upcoming_appointments(user_id, is_professional=False):
    """Get upcoming appointments for a user"""
    today = datetime.now().date()
    
    if is_professional:
        return Appointment.query.join(Appointment.professional).filter(
            Appointment.professional.has(user_id=user_id),
            Appointment.date >= today,
            Appointment.status.in_(['pending', 'confirmed'])
        ).order_by(Appointment.date, Appointment.start_time).all()
    else:
        return Appointment.query.join(Appointment.client).filter(
            Appointment.client.has(user_id=user_id),
            Appointment.date >= today,
            Appointment.status.in_(['pending', 'confirmed'])
        ).order_by(Appointment.date, Appointment.start_time).all()

def send_daily_reminders():
    """Send reminders for appointments scheduled for tomorrow"""
    tomorrow = datetime.now().date() + timedelta(days=1)
    appointments = Appointment.query.filter(
        Appointment.date == tomorrow,
        Appointment.status == 'confirmed'
    ).all()
    
    for appointment in appointments:
        send_reminder_email(appointment)
