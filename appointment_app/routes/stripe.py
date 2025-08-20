#! /usr/bin/env python3.6
# Python 3.6 or newer required.

import json
import os
import stripe
from flask import Blueprint, jsonify, request, current_app
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from appointment_app.database import get_db_connection
from ..services.auth_token_validator import verify_bearer_token

# Load environment variables
load_dotenv()

# Initialize the blueprint
bp = Blueprint('stripe', __name__, url_prefix='/api/stripe')

# Set the Stripe API key and endpoint secret from environment variables
stripe.api_key = os.getenv('STRIPE_API_KEY')
endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')

@bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle Stripe webhook events
    """
    event = None
    payload = request.data

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False), 400

    if endpoint_secret:
        # Verify the event with the endpoint secret
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False), 400

    # Handle the event
    if event and event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        print('Payment for {} succeeded'.format(payment_intent['amount']))
        # Add your payment success handling logic here
        # handle_payment_intent_succeeded(payment_intent)
    elif event['type'] == 'payment_method.attached':
        payment_method = event['data']['object']  # contains a stripe.PaymentMethod
        # Add your payment method handling logic here
        # handle_payment_method_attached(payment_method)
    elif event['type'] == 'customer.subscription.created':
        pass
    elif event['type'] == 'customer.subscription.created':
        pass
    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        business_id = session['metadata'].get('business_id')
        plan_id = session['metadata'].get('plan_id')
        
        if business_id and plan_id:
            try:
                with get_db_connection() as connection:
                    with connection.cursor(dictionary=True) as cursor:
                        # Update the business subscription plan
                        query = """
                            UPDATE business 
                            SET subscription_plan_id = %s 
                            WHERE business_id = %s
                        """
                        cursor.execute(query, (plan_id, business_id))
                        connection.commit()
                        print(f"Updated business {business_id} with plan {plan_id}")
            except Error as e:
                print(f"Error updating business subscription: {str(e)}")
        
        previous = event['data'].get('previous_attributes', {})

    # # Detect cancellation at period end
    # if (
    #     subscription.get('cancel_at_period_end') is True and
    #     previous.get('cancel_at_period_end') is False
    # ):
    #     print(f"🚫 Subscription {subscription['id']} scheduled for cancellation at period end.")
    #     print(f"  Customer: {subscription['customer']}")
    #     print(f"  Cancel at timestamp: {subscription.get('cancel_at')}")
    #     print(f"  Canceled at: {subscription.get('canceled_at')}")
    #     print(f"  Reason: {subscription.get('cancellation_details', {}).get('reason')}")
    # else:
    #     # Unexpected event type
    #     print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

@bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """
    Create a new payment intent
    Expected JSON payload: {"amount": 1000, "currency": "usd"}
    """
    try:
        payload, error = verify_bearer_token(request)
        if error:
            return jsonify({"error": error}), 401

        data = request.get_json()
        amount = data.get('amount')
        currency = data.get('currency', 'usd')
        
        if not amount:
            return jsonify({'error': 'Amount is required'}), 400
            
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
        )
        
        return jsonify({
            'clientSecret': intent.client_secret
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/create-checkout-session', methods=['POST'])
def create_checkout():
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json()
    session = stripe.checkout.Session.create(
        mode='subscription',
        success_url='https://yourdomain.com/success',
        cancel_url='https://yourdomain.com/cancel',
        line_items=[{ 'price': 'price_xyz', 'quantity': 1 }],
        metadata={
            "system_customer_id": data["customer_id"],
            "system_customer_name": data["name"]
        }
    )
    return jsonify({'url': session.url})