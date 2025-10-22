"""
Google Calendar integration utilities for syncing appointments
"""
import os
import logging
from datetime import datetime, timedelta
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app, url_for, session, redirect, request
from models import Appointment

# Configure logging
logger = logging.getLogger(__name__)

# This variable specifies the name of a file that contains the OAuth 2.0 information
# for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = 'client_secret_678559980772-kftgco67hmaflpdvhetp9ji96s1bcjqe.apps.googleusercontent.com.json'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/calendar']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v3'

# Configuración de depuración para OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Solo para desarrollo local
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'  # Permite flexibilidad en los scopes

def get_credentials():
    """Get valid user credentials from storage.
    
    If nothing has been stored, or if the stored credentials are invalid,
    return None.
    
    Returns:
        Credentials, the obtained credential.
    """
    if 'credentials' not in session:
        return None
    
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])
    
    return credentials

def create_client_secrets_file():
    """Verifica que el archivo de credenciales de Google exista"""
    # Verificamos que el archivo de credenciales exista
    if os.path.exists(CLIENT_SECRETS_FILE):
        logger.info(f"Archivo de credenciales {CLIENT_SECRETS_FILE} encontrado")
        return True
    else:
        logger.error(f"Archivo de credenciales {CLIENT_SECRETS_FILE} no encontrado")
        return False

def get_auth_url():
    """Get the authorization URL to redirect the user to."""
    # Create the client_secrets file if it doesn't exist
    if not os.path.exists(CLIENT_SECRETS_FILE):
        if not create_client_secrets_file():
            logger.error("No se pudo crear o encontrar el archivo de credenciales")
            return None
    
    try:
        # Verificar que el archivo de credenciales tenga el formato correcto
        with open(CLIENT_SECRETS_FILE, 'r') as f:
            client_info = json.load(f)
            logger.info(f"Usando credenciales para el proyecto: {client_info['web']['project_id']}")
            logger.info(f"URI de redirección configurada: {client_info['web']['redirect_uris']}")
        
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)

        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console.
        # Usamos la URL exacta configurada en el archivo de credenciales para evitar el error redirect_uri_mismatch
        flow.redirect_uri = 'http://localhost:5000/client/google/oauth2callback'

        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission.
            access_type='offline',
            # Enable incremental authorization.
            include_granted_scopes='true',
            # Force the approval prompt to get a new refresh token
            prompt='consent'
        )

        # Store the state so the callback can verify the auth server response.
        session['state'] = state
        
        logger.info(f"URL de autorización generada: {authorization_url}")
        return authorization_url
    except Exception as e:
        logger.error(f"Error al generar URL de autorización: {str(e)}")
        return None

def add_appointment_to_calendar(appointment_id):
    """Add an appointment to the user's Google Calendar
    
    Args:
        appointment_id (int): ID of the appointment to add
    
    Returns:
        dict: Calendar event data if successful, None otherwise
    """
    credentials = get_credentials()
    if not credentials:
        logger.error("No valid credentials for Google Calendar")
        return None
    
    # Build the Google Calendar API service
    service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    
    # Get appointment details
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        logger.error(f"Appointment {appointment_id} not found")
        return None
    
    # Get professional and client details
    professional_name = appointment.professional.user.get_full_name()
    client_name = appointment.client.user.get_full_name()
    
    # Format date and time
    date_str = appointment.date.strftime('%Y-%m-%d')
    start_time_str = appointment.start_time.strftime('%H:%M:%S')
    end_time_str = appointment.end_time.strftime('%H:%M:%S')
    
    start_datetime = f"{date_str}T{start_time_str}"
    end_datetime = f"{date_str}T{end_time_str}"
    
    # Create calendar event
    event = {
        'summary': f'Cita con {professional_name}',
        'location': appointment.professional.address or 'No especificada',
        'description': f'''
            Cita médica con {professional_name}
            
            Fecha: {appointment.date.strftime('%d/%m/%Y')}
            Hora: {appointment.start_time.strftime('%H:%M')} - {appointment.end_time.strftime('%H:%M')}
            Estado: {get_status_display(appointment.status)}
            
            Notas: {appointment.notes or 'No hay notas adicionales'}
        ''',
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'Europe/Madrid',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'Europe/Madrid',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 60},
            ],
        },
    }
    
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        logger.info(f"Event created: {event.get('htmlLink')}")
        return event
    except HttpError as error:
        logger.error(f'An error occurred: {error}')
        return None

def get_status_display(status):
    """Convert status code to display text"""
    status_map = {
        'pending': 'Pendiente',
        'confirmed': 'Confirmada',
        'cancelled': 'Cancelada',
        'completed': 'Completada'
    }
    return status_map.get(status, status)