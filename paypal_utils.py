"""
PayPal integration utilities for handling payments in the appointment system.
"""
import os
import logging
import json
import requests
from flask import current_app, url_for, redirect, request, flash
from models import Appointment, db
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_paypal():
    """
    Initialize PayPal with API credentials
    """
    client_id = current_app.config.get('PAYPAL_CLIENT_ID')
    client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
    return client_id is not None and client_secret is not None

def get_paypal_access_token():
    """
    Get PayPal OAuth access token
    """
    client_id = current_app.config.get('PAYPAL_CLIENT_ID')
    client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("PayPal credentials not configured")
        return None
    
    # Determine environment URL
    is_production = current_app.config.get('PAYPAL_PRODUCTION', False)
    base_url = "https://api-m.paypal.com" if is_production else "https://api-m.sandbox.paypal.com"
    
    try:
        # Get OAuth token
        auth_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            auth=(client_id, client_secret),
            headers={'Accept': 'application/json', 'Accept-Language': 'en_US'},
            data={'grant_type': 'client_credentials'}
        )
        auth_response.raise_for_status()
        return auth_response.json().get('access_token')
    except Exception as e:
        logger.error(f"Error getting PayPal access token: {str(e)}")
        return None

def create_checkout_session(appointment_id, success_url=None, cancel_url=None):
    """
    Create a PayPal Checkout Session for an appointment
    
    Args:
        appointment_id (int): ID of the appointment to pay for
        success_url (str, optional): URL to redirect to on successful payment
        cancel_url (str, optional): URL to redirect to if payment is cancelled
    
    Returns:
        str: URL to redirect the user to for checkout
    """
    if not setup_paypal():
        logger.error("PayPal API credentials not configured")
        return None
    
    # Get appointment details
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        logger.error(f"Appointment {appointment_id} not found")
        return None
    
    # Set default URLs if not provided
    if not success_url:
        success_url = url_for('client.payment_success', appointment_id=appointment_id, _external=True)
    if not cancel_url:
        cancel_url = url_for('client.payment_cancel', appointment_id=appointment_id, _external=True)
    
    # Get access token
    access_token = get_paypal_access_token()
    if not access_token:
        return None
    
    # Prepare order details
    professional_name = appointment.professional.user.get_full_name()
    appointment_date = appointment.date.strftime('%d/%m/%Y')
    appointment_time = appointment.start_time.strftime('%H:%M')
    appointment_cost = current_app.config.get('APPOINTMENT_COST', 50)
    
    # Determine environment URL
    is_production = current_app.config.get('PAYPAL_PRODUCTION', False)
    base_url = "https://api-m.paypal.com" if is_production else "https://api-m.sandbox.paypal.com"
    
    try:
        # Create order
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": f"appointment_{appointment_id}",
                    "description": f"Cita con {professional_name} - {appointment_date} {appointment_time}",
                    "custom_id": str(appointment_id),
                    "amount": {
                        "currency_code": "EUR",
                        "value": str(appointment_cost)
                    }
                }
            ],
            "application_context": {
                "brand_name": "Gestor de Citas",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW",
                "return_url": success_url,
                "cancel_url": cancel_url
            }
        }
        
        response = requests.post(
            f"{base_url}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=order_data
        )
        response.raise_for_status()
        order = response.json()
        
        # Save payment ID to appointment
        appointment.payment_id = order.get('id')
        db.session.commit()
        
        # Find approval URL
        for link in order.get('links', []):
            if link.get('rel') == 'approve':
                return link.get('href')
        
        logger.error("No approval URL found in PayPal response")
        return None
    except Exception as e:
        logger.error(f"Error creating PayPal checkout session: {str(e)}")
        return None

def handle_webhook(payload):
    """
    Handle PayPal webhook events
    
    Args:
        payload (dict): Webhook payload from PayPal
    
    Returns:
        bool: True if event handled successfully, False otherwise
    """
    try:
        # Verify the event
        event_type = payload.get('event_type')
        resource = payload.get('resource', {})
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            # Extract appointment_id from custom_id
            custom_id = None
            for purchase_unit in resource.get('purchase_units', []):
                custom_id = purchase_unit.get('custom_id')
                if custom_id:
                    break
            
            if not custom_id:
                logger.error("No custom_id in PayPal webhook payload")
                return False
            
            # Update appointment payment status
            appointment = Appointment.query.get(int(custom_id))
            if appointment:
                appointment.payment_status = 'paid'
                appointment.payment_timestamp = datetime.utcnow()
                
                # If appointment was pending, confirm it upon payment
                if appointment.status == 'pending':
                    appointment.status = 'confirmed'
                
                db.session.commit()
                logger.info(f"Payment for appointment {custom_id} marked as completed")
                return True
            else:
                logger.error(f"Appointment {custom_id} not found")
                return False
        
        return True  # Return true for events we don't need to process
    except Exception as e:
        logger.error(f"Error handling PayPal webhook: {str(e)}")
        return False

def refund_payment(appointment_id):
    """
    Refund a payment for an appointment
    
    Args:
        appointment_id (int): ID of the appointment to refund
    
    Returns:
        bool: True if refund was successful, False otherwise
    """
    if not setup_paypal():
        logger.error("PayPal API credentials not configured")
        return False
    
    # Get appointment details
    appointment = Appointment.query.get(appointment_id)
    if not appointment or not appointment.payment_id:
        logger.error(f"Appointment {appointment_id} not found or has no payment ID")
        return False
    
    # Get access token
    access_token = get_paypal_access_token()
    if not access_token:
        return False
    
    # Determine environment URL
    is_production = current_app.config.get('PAYPAL_PRODUCTION', False)
    base_url = "https://api-m.paypal.com" if is_production else "https://api-m.sandbox.paypal.com"
    
    try:
        # First, get the capture ID from the order
        order_response = requests.get(
            f"{base_url}/v2/checkout/orders/{appointment.payment_id}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        order_response.raise_for_status()
        order_data = order_response.json()
        
        # Extract capture ID
        capture_id = None
        for purchase_unit in order_data.get('purchase_units', []):
            for capture in purchase_unit.get('payments', {}).get('captures', []):
                capture_id = capture.get('id')
                if capture_id:
                    break
            if capture_id:
                break
        
        if not capture_id:
            logger.error(f"No capture ID found for order {appointment.payment_id}")
            return False
        
        # Create refund
        refund_response = requests.post(
            f"{base_url}/v2/payments/captures/{capture_id}/refund",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json={"note_to_payer": "Reembolso de cita cancelada"}
        )
        refund_response.raise_for_status()
        
        # Update appointment status
        appointment.payment_status = 'refunded'
        db.session.commit()
        
        logger.info(f"Payment for appointment {appointment_id} refunded successfully")
        return True
    except Exception as e:
        logger.error(f"Error refunding PayPal payment: {str(e)}")
        return False