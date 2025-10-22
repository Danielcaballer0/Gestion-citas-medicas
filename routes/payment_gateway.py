from flask import Blueprint, request, jsonify, current_app, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from models import Appointment, Client, db
from datetime import datetime
import logging

# Importar utilidades de pasarela de pago
import paypal_utils

# Configure logging
logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/process/<int:appointment_id>')
@login_required
def process_payment(appointment_id):
    """
    Procesar pago para una cita usando la pasarela configurada
    """
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
    
    # Usar PayPal como única pasarela de pago
    checkout_url = paypal_utils.create_checkout_session(appointment.id)
    
    if checkout_url:
        return redirect(checkout_url)
    else:
        flash('Error al procesar el pago. Por favor intente nuevamente.', 'danger')
        return redirect(url_for('client.my_appointments'))

@payment_bp.route('/refund/<int:appointment_id>', methods=['POST'])
@login_required
def refund_payment(appointment_id):
    """
    Reembolsar un pago usando la pasarela configurada
    """
    if not current_user.is_client() and not current_user.is_admin():
        flash('No tienes permisos para acceder a esta función', 'danger')
        return redirect(url_for('main.index'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Verificar permisos
    if current_user.is_client():
        client = Client.query.filter_by(user_id=current_user.id).first()
        if appointment.client_id != client.id:
            flash('No tienes permiso para reembolsar esta cita', 'danger')
            return redirect(url_for('client.my_appointments'))
    
    # Verificar que el pago existe
    if appointment.payment_status != 'paid' or not appointment.payment_id:
        flash('No hay pago para reembolsar', 'warning')
        return redirect(url_for('client.my_appointments'))
    
    # Usar PayPal como única pasarela de pago
    success = paypal_utils.refund_payment(appointment.id)
    
    if success:
        flash('El pago ha sido reembolsado correctamente', 'success')
    else:
        flash('Error al procesar el reembolso. Por favor intente nuevamente.', 'danger')
    
    # Redirigir según el tipo de usuario
    if current_user.is_client():
        return redirect(url_for('client.my_appointments'))
    else:
        return redirect(url_for('admin.appointments'))

# Se eliminaron las rutas de simulación de Wompi ya que solo se usa PayPal