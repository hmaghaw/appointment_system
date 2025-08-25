#! /usr/bin/env python3.6
# Python 3.6 or newer required.

import json
import os
import stripe
from flask import Blueprint, jsonify, request, current_app, g
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, errorcode
from appointment_app.database import get_db_connection, get_db_cursor
from ..services.auth_token_validator import verify_bearer_token
from ..database import get_db_connection
from ..services.onboarding import choose_number
import uuid

# Load environment variables
load_dotenv()

# Initialize the blueprint
bp = Blueprint('stripe', __name__, url_prefix='/api/stripe')

# Set the Stripe API key and endpoint secret from environment variables
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
#endpoint_secret = os.getenv('STRIPE_SECRET_KEY')

def get_transaction_reason(event):
    type = 'topup'
    metadata = event['data']['object']['metadata']
    if 'type' in metadata:
        type = metadata['type']
    return type

def process_event(event):
    reason = get_transaction_reason(event)
    idempotency_key = event['id']
    metadata = event['data']['object']['metadata']
    if reason == 'topup':
        amount_cents = int(metadata['amount']) * 100
        business_id = int(metadata['business_id'])
        result = apply_topup(business_id=business_id ,amount_cents=amount_cents, request_id=idempotency_key,reason=reason )
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        print('Payment for {} succeeded'.format(payment_intent['amount']))
    elif reason == 'onboarding':
        payment_intent_id = event['data']['object']['id']
        data = json.loads(metadata['signup_payload'])
        business_id = data['create_account']['business_id']
        business_name = data['create_account']['business_name']
        user_id = data['create_account']['user_id']
        phone_number = data['choose_number']['phone_number']
        phone_number_price = data['choose_number']['price']
        data['choose_number']['price']
        response = choose_number(business_id, business_name, metadata['choose_number'], headers=headers)

        business_id = start_onboarding(metadata=data)
        amount_cents = int(event['data']['object']['metadata']['topup_amount']) * 100
        result = apply_topup(business_id=business_id, amount_cents=amount_cents, request_id=idempotency_key,
                             reason=reason)

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
    if event and event['type'] == 'payment_intent.succeeded':
        process_event(event)
    elif event['type'] == 'payment_method.attached':
        payment_method = event['data']['object']  # contains a stripe.PaymentMethod
        # Add your payment method handling logic here
        # handle_payment_method_attached(payment_method)
    elif event['type'] == 'customer.subscription.created':
        pass
    elif event['type'] == 'customer.subscription.created':
        pass
    elif event['type'] == 'checkout.session.completed':
        process_event()

    return jsonify(success=True)

@bp.route('/create-customer', methods=['POST'])
def create_customer():
    """
    Create a Stripe customer for a business
    
    Request body:
    {
        "business_id": 123,
        "email": "business@example.com",
        "name": "Business Name"
    }
    
    Returns:
        JSON with Stripe customer ID or error message
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    try:
        data = request.get_json()
        required_fields = ['business_id', 'user_id', 'phone', 'email', 'name']
        
        # Validate required fields
        if not all(field in data for field in required_fields):
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields. Required: {required_fields}'
            }), 400
            
        business_id = data['business_id']
        email = data['email']
        user_id = data['user_id']
        phone = data['phone']
        name = data['name']

        # Create Stripe customer
        customer_id = create_stripe_customer_for_business(business_id, user_id, phone, email, name)
        
        return jsonify({
            'status': 'success',
            'customer_id': customer_id,
            'business_id': business_id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error creating Stripe customer: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def create_stripe_customer_for_business(business_id, user_id, phone, email, name):
    """
    Creates a Stripe Customer for a business if not already existing.

    Args:
        business_id: ID of the business in your DB
        email: Business owner email
        name: Business name

    Returns:
        stripe_customer_id (str)
    """
    with get_db_connection() as db_conn:
        with db_conn.cursor(dictionary=True) as cursor:
            # Check if already exists
            cursor.execute("SELECT stripe_customer_id FROM business WHERE business_id = %s", (business_id,))
            row = cursor.fetchone()
            if row and row.get("stripe_customer_id"):
                return row["stripe_customer_id"]
                
            # Create customer in Stripe
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "business_id": business_id,
                    "user_id": user_id,
                    "phone": phone,
                    "type": "business_customer"
                }
            )

            # Save back to DB
            cursor.execute(
                "UPDATE business SET stripe_customer_id = %s WHERE business_id = %s",
                (customer.id, business_id)
            )
            db_conn.commit()

            return customer.id


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

@bp.route('/transaction_history', methods=['POST'])
def transaction_history():
    """
    Retrieve the transaction history for a business.

    Payload:
    {
        "business_id": 17
    }

    Response:
    {
        "status": "success",
        "business_id": 17,
        "transactions": [
            {
                "created_at": "2025-08-24 10:15:00",
                "amount_dollars": 50,
                "reason": "topup"
            },
            ...
        ]
    }
    """
    payload, error = verify_bearer_token(request)
    if error:
        return jsonify({"error": error}), 401

    data = request.get_json(silent=True) or {}
    business_id = data.get('business_id')

    if not business_id:
        return jsonify({"error": "business_id is required"}), 400

    try:
        with get_db_cursor(database='appointment_db', commit=False, dictionary=True) as cursor:
            cursor.execute("""
                SELECT created_at, amount_cents, reason
                FROM business_ledger
                WHERE business_id = %s
                ORDER BY created_at DESC
            """, (business_id,))
            rows = cursor.fetchall()

            transactions = [
                {
                    "created_at": row["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    "amount_dollars": int(row["amount_cents"]) // 100,
                    "reason": row["reason"]
                }
                for row in rows
            ]

        return jsonify({
            "status": "success",
            "business_id": business_id,
            "transactions": transactions
        }), 200

    except mysql.connector.Error as err:
        return jsonify({"error": f"Database error: {str(err)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500