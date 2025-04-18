"""
Stripe integration utilities for handling payments in the appointment system.
"""
import os
import logging
import json
import stripe
from flask import current_app, url_for, redirect, request, flash
from models import Appointment, db
from datetime import datetime

logger = logging.getLogger(__name__)

def setup_stripe():
    """
    Initialize Stripe with API key
    """
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    return current_app.config.get('STRIPE_SECRET_KEY') is not None

def create_checkout_session(appointment_id, success_url=None, cancel_url=None):
    """
    Create a Stripe Checkout Session for an appointment
    
    Args:
        appointment_id (int): ID of the appointment to pay for
        success_url (str, optional): URL to redirect to on successful payment
        cancel_url (str, optional): URL to redirect to if payment is cancelled
    
    Returns:
        str: URL to redirect the user to for checkout
    """
    if not setup_stripe():
        logger.error("Stripe API key not configured")
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
    
    # Get domain for URLs
    domain_url = request.host_url.rstrip('/')
    
    # Prepare line items
    professional_name = appointment.professional.user.get_full_name()
    appointment_date = appointment.date.strftime('%d/%m/%Y')
    appointment_time = appointment.start_time.strftime('%H:%M')
    appointment_cost = current_app.config.get('APPOINTMENT_COST', 50) * 100  # in cents
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Cita con {professional_name}',
                            'description': f'Fecha: {appointment_date} a las {appointment_time}',
                        },
                        'unit_amount': int(appointment_cost),
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                'appointment_id': appointment_id,
                'client_id': appointment.client_id,
                'professional_id': appointment.professional_id,
            },
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return checkout_session.url
    except Exception as e:
        logger.error(f"Error creating Stripe checkout session: {str(e)}")
        return None

def handle_webhook(payload, signature):
    """
    Handle Stripe webhook events
    
    Args:
        payload (str): Raw request body
        signature (str): Stripe signature header
    
    Returns:
        bool: True if event handled successfully, False otherwise
    """
    if not setup_stripe():
        logger.error("Stripe API key not configured")
        return False
    
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        logger.warning("Stripe webhook secret not configured")
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
        else:
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
        
        # Handle specific events
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Get appointment from metadata
            appointment_id = session.get('metadata', {}).get('appointment_id')
            if not appointment_id:
                logger.error("No appointment_id in session metadata")
                return False
            
            # Update appointment payment status
            appointment = Appointment.query.get(int(appointment_id))
            if appointment:
                appointment.payment_status = 'paid'
                appointment.payment_id = session.get('id')
                appointment.payment_timestamp = datetime.utcnow()
                db.session.commit()
                logger.info(f"Payment for appointment {appointment_id} marked as completed")
                return True
            else:
                logger.error(f"Appointment {appointment_id} not found")
                return False
        
        return True  # Successfully processed event
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {str(e)}")
        return False

def refund_payment(appointment_id):
    """
    Refund a payment for an appointment
    
    Args:
        appointment_id (int): ID of the appointment to refund
    
    Returns:
        bool: True if refund successful, False otherwise
    """
    if not setup_stripe():
        logger.error("Stripe API key not configured")
        return False
    
    appointment = Appointment.query.get(appointment_id)
    if not appointment or not appointment.payment_id:
        logger.error(f"Appointment {appointment_id} not found or has no payment")
        return False
    
    try:
        # Find the payment intent from the checkout session
        session = stripe.checkout.Session.retrieve(appointment.payment_id)
        payment_intent = session.payment_intent
        
        # Create the refund
        refund = stripe.Refund.create(
            payment_intent=payment_intent,
            reason='requested_by_customer'
        )
        
        # Update appointment status
        appointment.payment_status = 'refunded'
        appointment.refund_id = refund.id
        appointment.refund_timestamp = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Payment for appointment {appointment_id} refunded successfully")
        return True
    except Exception as e:
        logger.error(f"Error refunding payment: {str(e)}")
        return False