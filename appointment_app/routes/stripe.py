#! /usr/bin/env python3.6
# Python 3.6 or newer required.

import json
import os
import stripe
from flask import Blueprint, jsonify, request, current_app
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, errorcode
from appointment_app.database import get_db_connection, get_db_cursor
from ..services.auth_token_validator import verify_bearer_token

import uuid

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

    # if endpoint_secret:
    #     # Verify the event with the endpoint secret
    #     sig_header = request.headers.get('stripe-signature')
    #     try:
    #         event = stripe.Webhook.construct_event(
    #             payload, sig_header, endpoint_secret
    #         )
    #     except stripe.error.SignatureVerificationError as e:
    #         print('⚠️  Webhook signature verification failed.' + str(e))
    #         return jsonify(success=False), 400

    event_id = event['id']
    id = event['data']['object']['id']

    metadata = event['data']['object']['metadata']
    #idempotency_key = event['request']['idempotency_key']
    idempotency_key = event['id']
    client_secret = event['data']['object']['client_secret']
    event_type = event['type']
    business_id = int(metadata['business_id'])
    amount_cents = int(metadata['amount']) * 100
    reason = metadata['type']
    # Handle the event
    if event and event['type'] == 'payment_intent.succeeded':
        metadata = event['data']['object']['metadata']
        result = apply_topup(business_id=business_id ,amount_cents=amount_cents, request_id=idempotency_key,reason=reason )
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
        metadata = event['data']['object']['metadata']
        result = apply_topup(business_id=business_id ,amount_cents=amount_cents, request_id=idempotency_key,reason=reason )
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        print('Payment for {} succeeded'.format(payment_intent['amount']))

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





@bp.route('/topup', methods=['POST'])
def topup_business_balance():
    """
    Top up a business balance (amount in dollars) and record a ledger entry.

    Payload:
    {
        "business_id": 11,
        "amount": 50,              # integer dollars
        // optional:
        // "request_id": "abc-123" # idempotency key; or use Idempotency-Key header
    }

    Behavior:
    - amount is multiplied by 100 to convert to cents
    - updates business.balance_cents
    - inserts a row in business_ledger (business_id, amount_cents, reason, request_id)
    - idempotent: same request_id won’t double-credit
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json(silent=True) or {}
    business_id = data.get('business_id')
    amount = data.get('amount')

    if not business_id or amount is None:
        return jsonify({"error": "business_id and amount are required"}), 400

    # Validate integer amount > 0 (in dollars)
    try:
        amount_dollars = int(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount must be an integer (dollars)"}), 400
    if amount_dollars <= 0:
        return jsonify({"error": "amount must be > 0"}), 400

    # Convert to cents
    amount_cents = amount_dollars * 100

    # Idempotency: payload.request_id > header > generated
    request_id = (
        data.get('request_id')
        or request.headers.get('Idempotency-Key')
        or str(uuid.uuid4())
    )
    LEDGER_REASON = 'topup'

    try:
        with get_db_cursor(database='appointment_db', commit=True, dictionary=True) as cursor:
            # 1) Lock the business row
            cursor.execute(
                "SELECT balance_cents FROM business WHERE business_id = %s FOR UPDATE",
                (business_id,)
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Business not found"}), 404

            current_balance = int(row["balance_cents"])

            # 2) Insert ledger (idempotent on request_id)
            try:
                cursor.execute("""
                    INSERT INTO business_ledger (business_id, amount_cents, reason, request_id)
                    VALUES (%s, %s, %s, %s)
                """, (business_id, amount_cents, LEDGER_REASON, request_id))
                ledger_inserted = True
            except mysql.connector.IntegrityError as e:
                if getattr(e, 'errno', None) == errorcode.ER_DUP_ENTRY:
                    ledger_inserted = False  # duplicate topup; don't re-apply
                else:
                    raise

            # 3) Apply balance only if new ledger row
            if ledger_inserted:
                cursor.execute("""
                    UPDATE business
                    SET balance_cents = balance_cents + %s
                    WHERE business_id = %s
                """, (amount_cents, business_id))

            # 4) Read the latest balance to return
            cursor.execute(
                "SELECT balance_cents FROM business WHERE business_id = %s",
                (business_id,)
            )
            new_balance_cents = int(cursor.fetchone()["balance_cents"])

            return jsonify({
                "status": "success",
                "business_id": business_id,
                "topup": {
                    "amount_dollars": amount_dollars,
                    "amount_cents": amount_cents,
                    "applied": bool(ledger_inserted),
                    "request_id": request_id,
                    "reason": LEDGER_REASON
                },
                "balance_cents": new_balance_cents
            }), 200

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def apply_topup(business_id, amount_cents, request_id, reason="topup"):
    """
    Apply a top-up to a business balance and record a ledger entry.

    Returns:
        dict: {
            "applied": bool,              # True if new ledger row was inserted
            "amount_cents": int,
            "amount_cents": int,
            "request_id": str,
            "reason": str,
            "new_balance_cents": int
        }
    Raises:
        ValueError, mysql.connector.Error
    """

    with get_db_cursor(database='appointment_db', commit=True, dictionary=True) as cursor:
        # 1) Lock business row
        cursor.execute(
            "SELECT balance_cents FROM business WHERE business_id = %s FOR UPDATE",
            (business_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("Business not found")

        # 2) Insert ledger entry (idempotent on request_id)
        try:
            cursor.execute("""
                INSERT INTO business_ledger (business_id, amount_cents, reason, request_id)
                VALUES (%s, %s, %s, %s)
            """, (business_id, amount_cents, reason, request_id))
            ledger_inserted = True
        except mysql.connector.IntegrityError as e:
            if getattr(e, 'errno', None) == errorcode.ER_DUP_ENTRY:
                ledger_inserted = False
            else:
                raise

        # 3) Update balance if new ledger row
        if ledger_inserted:
            cursor.execute("""
                UPDATE business
                SET balance_cents = balance_cents + %s
                WHERE business_id = %s
            """, (amount_cents, business_id))

        # 4) Fetch latest balance
        cursor.execute(
            "SELECT balance_cents FROM business WHERE business_id = %s",
            (business_id,)
        )
        new_balance_cents = int(cursor.fetchone()["balance_cents"])

    return {
        "applied": ledger_inserted,
        "amount_cents": amount_cents,
        "request_id": request_id,
        "reason": reason,
        "new_balance_cents": new_balance_cents
    }
