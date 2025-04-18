"""
SendGrid integration utilities for managing email notifications in the appointment system.
"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, TemplateId
from flask import current_app
from app import mail
from models import Appointment

logger = logging.getLogger(__name__)

def send_email_with_sendgrid(to_email, subject, html_content=None, text_content=None, template_id=None, dynamic_template_data=None):
    """
    Send email using SendGrid API
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        html_content (str, optional): HTML content of the email
        text_content (str, optional): Plain text content of the email
        template_id (str, optional): SendGrid template ID
        dynamic_template_data (dict, optional): Dynamic data for the template
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        sg = SendGridAPIClient(current_app.config['SENDGRID_API_KEY'])
        from_email = Email(current_app.config['MAIL_DEFAULT_SENDER'])
        to_email = To(to_email)
        
        message = Mail(from_email=from_email, to_emails=to_email, subject=subject)
        
        if template_id:
            message.template_id = TemplateId(template_id)
            if dynamic_template_data:
                message.dynamic_template_data = dynamic_template_data
        elif html_content:
            message.content = Content("text/html", html_content)
        elif text_content:
            message.content = Content("text/plain", text_content)
        else:
            logger.error("No content provided for email")
            return False
        
        response = sg.send(message)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email: {response.status_code} - {response.body}")
            return False
            
    except Exception as e:
        logger.error(f"SendGrid error: {str(e)}")
        return False

def send_appointment_confirmation(appointment):
    """
    Send appointment confirmation email using SendGrid
    
    Args:
        appointment (Appointment): The appointment object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    client_email = appointment.client.user.email
    professional_name = appointment.professional.user.get_full_name()
    client_name = appointment.client.user.get_full_name()
    appointment_date = appointment.date.strftime('%d/%m/%Y')
    appointment_time = appointment.start_time.strftime('%H:%M')
    
    # Get status display text
    status_map = {
        'pending': 'Pendiente',
        'confirmed': 'Confirmada',
        'cancelled': 'Cancelada',
        'completed': 'Completada'
    }
    status_display = status_map.get(appointment.status, appointment.status)
    
    html_content = f'''
    <h2>Confirmación de Cita</h2>
    <p>Hola {appointment.client.user.first_name},</p>
    <p>Tu cita ha sido <strong>{status_display}</strong>.</p>
    <p><strong>Profesional:</strong> {professional_name}</p>
    <p><strong>Fecha:</strong> {appointment_date}</p>
    <p><strong>Hora:</strong> {appointment_time}</p>
    <p><strong>Estado:</strong> {status_display}</p>
    
    <p>Si necesitas realizar algún cambio, por favor contacta con el profesional o ingresa a tu cuenta.</p>
    <p>Gracias por usar nuestro servicio.</p>
    '''
    
    return send_email_with_sendgrid(
        to_email=client_email,
        subject=f'Confirmación de Cita con {professional_name}',
        html_content=html_content
    )

def send_appointment_reminder(appointment):
    """
    Send appointment reminder email using SendGrid
    
    Args:
        appointment (Appointment): The appointment object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    client_email = appointment.client.user.email
    professional_name = appointment.professional.user.get_full_name()
    appointment_date = appointment.date.strftime('%d/%m/%Y')
    appointment_time = appointment.start_time.strftime('%H:%M')
    
    html_content = f'''
    <h2>Recordatorio de Cita</h2>
    <p>Hola {appointment.client.user.first_name},</p>
    <p>Te recordamos que tienes una cita programada para mañana.</p>
    <p><strong>Profesional:</strong> {professional_name}</p>
    <p><strong>Fecha:</strong> {appointment_date}</p>
    <p><strong>Hora:</strong> {appointment_time}</p>
    
    <p>Si necesitas cancelar o reprogramar, por favor hazlo con al menos 24 horas de anticipación.</p>
    <p>Gracias por usar nuestro servicio.</p>
    '''
    
    return send_email_with_sendgrid(
        to_email=client_email,
        subject=f'Recordatorio de Cita con {professional_name}',
        html_content=html_content
    )

def process_daily_reminders():
    """
    Send reminders for appointments scheduled for tomorrow
    
    Returns:
        tuple: (total_reminders, success_count, failed_count)
    """
    from datetime import datetime, timedelta
    from models import Appointment
    
    tomorrow = datetime.now().date() + timedelta(days=1)
    appointments = Appointment.query.filter(
        Appointment.date == tomorrow,
        Appointment.status == 'confirmed'
    ).all()
    
    total = len(appointments)
    success = 0
    failed = 0
    
    for appointment in appointments:
        if send_appointment_reminder(appointment):
            success += 1
        else:
            failed += 1
            
    logger.info(f"Daily reminders: {success} sent successfully, {failed} failed out of {total} total")
    return (total, success, failed)