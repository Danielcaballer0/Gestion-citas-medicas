"""
Webhook routes for Stripe and other external services
"""
from flask import Blueprint, request, jsonify, current_app
import json
import logging
from paypal_utils import handle_webhook as handle_paypal_webhook
from sendgrid_utils import process_daily_reminders

# Configure logging
logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhooks', __name__)

@webhook_bp.route('/paypal/webhook', methods=['POST'])
def paypal_webhook():
    """
    Handle webhook events from PayPal
    """
    if request.content_type != 'application/json':
        return jsonify({'error': 'Invalid content type'}), 400
    
    payload = request.data.decode('utf-8')
    
    # Handle the webhook event
    try:
        if handle_paypal_webhook(payload):
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': 'Failed to process webhook'}), 400
    except Exception as e:
        logger.error(f"Error processing PayPal webhook: {str(e)}")
        return jsonify({'error': 'Failed to process webhook'}), 400
        logger.error(f"Error processing Wompi webhook: {str(e)}")
        return jsonify({'error': str(e)}), 400

@webhook_bp.route('/cron/daily-reminders', methods=['POST'])
def daily_reminders():
    """
    Process daily appointment reminders (to be triggered by a cron job)
    """
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != current_app.config.get('CRON_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        total, success, failed = process_daily_reminders()
        return jsonify({
            'status': 'success',
            'total': total,
            'success': success,
            'failed': failed
        }), 200
    except Exception as e:
        logger.error(f"Error processing daily reminders: {str(e)}")
        return jsonify({'error': str(e)}), 500