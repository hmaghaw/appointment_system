from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
from typing import List, Dict, Any, Optional
from appointment_app.database import get_db_cursor, get_db_connection, db_transaction
from decimal import Decimal
from typing import Optional, List, Dict, Any
bp = Blueprint('car_rental', __name__, url_prefix='/api/car_rental')


class ReservationRequest:
    """Data class for reservation request payload"""

    def _safe_int(self, value, default=-1):
        """Safely convert value to int, returning default if conversion fails"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def __init__(self, data: Dict[str, Any]):
        self.business_id = self._safe_int(data.get('business_id'))
        self.customer_id = self._safe_int(data.get('customer_id'))
        self.pickup_datetime = data.get('pickup_datetime')
        self.dropoff_datetime = data.get('dropoff_datetime')
        self.pickup_location_id = self._safe_int(data.get('pickup_location_id'))
        self.dropoff_location_id = self._safe_int(data.get('dropoff_location_id'))
        self.vehicle_class_id = self._safe_int(data.get('vehicle_class_id'))
        self.vehicle_id = self._safe_int(data.get('vehicle_id'))  # Optional
        self.rate_plan_id = self._safe_int(data.get('rate_plan_id'))
        self.rental_request_id = self._safe_int(data.get('rental_request_id'))  # Optional
        self.add_ons = data.get('add_ons', [])  # Optional
        self.insurance_options = data.get('insurance_options', [])  # Optional

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate required fields"""
        required_fields = [
            ('business_id', int),
            ('customer_id', int),
            ('pickup_datetime', str),
            ('dropoff_datetime', str),
            ('pickup_location_id', int),
            ('dropoff_location_id', int),
            ('rate_plan_id', int)
        ]

        for field_name, field_type in required_fields:
            value = getattr(self, field_name)
            if value is None:
                return False, f"Missing required field: {field_name}"
            if not isinstance(value, field_type):
                return False, f"Invalid type for {field_name}, expected {field_type.__name__}"

        # Validate datetime format
        try:
            self.pickup_datetime = datetime.fromisoformat(self.pickup_datetime.replace('Z', '+00:00'))
            self.dropoff_datetime = datetime.fromisoformat(self.dropoff_datetime.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            return False, f"Invalid datetime format: {str(e)}"

        # Validate date logic
        if self.dropoff_datetime <= self.pickup_datetime:
            return False, "Dropoff datetime must be after pickup datetime"

        # Validate add_ons format
        if not isinstance(self.add_ons, list):
            return False, "add_ons must be an array"

        for addon in self.add_ons:
            if not isinstance(addon, dict) or 'add_on_id' not in addon or 'quantity' not in addon:
                return False, "Invalid add_on format. Each must have add_on_id and quantity"

        # Validate insurance_options format
        if not isinstance(self.insurance_options, list):
            return False, "insurance_options must be an array"

        for insurance in self.insurance_options:
            if not isinstance(insurance, dict) or 'insurance_option_id' not in insurance:
                return False, "Invalid insurance_option format. Each must have insurance_option_id"

        return True, None

def build_voice_confirmation(response):
    pickup = datetime.fromisoformat(response['pickup_datetime'])
    dropoff = datetime.fromisoformat(response['dropoff_datetime'])

    addons = response.get('add_ons', [])
    insurance = response.get('insurance_options', [])

    addons_text = ""
    if addons:
        addons_text = ", with " + ", ".join(
            f"{a['quantity']} {a['add_on_name']}" if a.get("quantity", 1) > 1 else a['add_on_name']
            for a in addons
        )

    insurance_text = ""
    if insurance:
        insurance_text = ", and insurance"

    return (
        f"You're renting a {response['car_specs']} for {response['rental_days']} days, "
        f"from {pickup.strftime('%B %d at %I:%M %p')} "
        f"to {dropoff.strftime('%B %d at %I:%M %p')}"
        f"{addons_text}{insurance_text}. "
        f"The total is ${response['total_amount']:.2f}. "
        f"Shall I confirm your booking?"
    )


def check_vehicle_availability(
        vehicle_id: int,
        pickup_datetime: datetime,
        dropoff_datetime: datetime
) -> bool:
    """
    Check if a vehicle is available for the requested time period
    Returns True if available, False if conflicting schedules exist
    """
    query = """
            SELECT COUNT(*) as conflict_count
            FROM car_rental_vehicle_schedule
            WHERE vehicle_id = %s
              AND status IN ('tentative', 'confirmed', 'active')
              AND (
                (start_datetime < %s AND end_datetime > %s) OR
                (start_datetime < %s AND end_datetime > %s) OR
                (start_datetime >= %s AND end_datetime <= %s)
                ) \
            """

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(query, (
            vehicle_id,
            dropoff_datetime, pickup_datetime,
            dropoff_datetime, pickup_datetime,
            pickup_datetime, dropoff_datetime
        ))
        result = cursor.fetchone()

    return result['conflict_count'] == 0


def find_available_vehicle(
        business_id: int,
        vehicle_class_id: int,
        pickup_location_id: int,
        pickup_datetime: datetime,
        dropoff_datetime: datetime
) -> Optional[int]:
    """
    Find an available vehicle of the requested class at the pickup location
    Returns vehicle_id or None if no vehicles available
    """
    query = """
            SELECT v.vehicle_id
            FROM car_rental_vehicle v
                     JOIN car_rental_vehicle_inventory i ON v.vehicle_id = i.vehicle_id
            WHERE v.business_id = %s
              AND v.vehicle_class_id = %s
              AND v.is_active = 1
              AND i.location_id = %s
              AND i.operational_status = 'ready'
              AND NOT EXISTS (SELECT 1 \
                              FROM car_rental_vehicle_schedule s \
                              WHERE s.vehicle_id = v.vehicle_id \
                                AND s.status IN ('tentative', 'confirmed', 'active') \
                                AND ( \
                                  (s.start_datetime < %s AND s.end_datetime > %s) OR \
                                  (s.start_datetime < %s AND s.end_datetime > %s) OR \
                                  (s.start_datetime >= %s AND s.end_datetime <= %s) \
                                  ))
                LIMIT 1 \
            """

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(query, (
            business_id,
            vehicle_class_id,
            pickup_location_id,
            dropoff_datetime, pickup_datetime,
            dropoff_datetime, pickup_datetime,
            pickup_datetime, dropoff_datetime
        ))
        result = cursor.fetchone()

    return result['vehicle_id'] if result else None


def calculate_rental_days(pickup_datetime: datetime, dropoff_datetime: datetime) -> int:
    """Calculate number of rental days (minimum 1 day)"""
    duration = dropoff_datetime - pickup_datetime
    days = duration.days
    if duration.seconds > 0:
        days += 1
    return max(1, days)


def get_rate_price(
        vehicle_class_id: int,
        pickup_location_id: int,
        pickup_datetime: datetime,
        rate_plan_id: int
) -> Optional[Dict[str, Decimal]]:
    if rate_plan_id == -1:
        rate_plan_id = 1
    """Get pricing information for the rate plan"""
    query = """
            SELECT price_per_day, price_per_week
            FROM car_rental_rate_plan_price
            WHERE rate_plan_id = %s
              AND vehicle_class_id = %s
              AND location_id = %s
              AND effective_from <= %s
              AND (effective_to IS NULL OR effective_to >= %s) LIMIT 1 \
            """

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(query, (
            rate_plan_id,
            vehicle_class_id,
            pickup_location_id,
            pickup_datetime.date(),
            pickup_datetime.date()
        ))
        result = cursor.fetchone()

    return result


def calculate_base_amount(
        rate_info: Dict[str, Decimal],
        rental_days: int
) -> Decimal:
    """Calculate base rental amount based on days and rate"""
    price_per_day = Decimal(str(rate_info['price_per_day']))
    price_per_week = Decimal(str(rate_info['price_per_week'])) if rate_info['price_per_week'] else None

    if price_per_week and rental_days >= 7:
        weeks = rental_days // 7
        remaining_days = rental_days % 7
        return (weeks * price_per_week) + (remaining_days * price_per_day)
    else:
        return rental_days * price_per_day


def get_addon_pricing(add_on_id: int) -> Optional[Dict[str, Any]]:
    """Get add-on pricing information"""
    query = """
            SELECT name, pricing_unit, base_price
            FROM car_rental_add_on
            WHERE add_on_id = %s \
              AND is_active = 1 \
            """

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(query, (add_on_id,))
        result = cursor.fetchone()

    return result


def get_insurance_pricing(insurance_option_id: int) -> Optional[Dict[str, Any]]:
    """Get insurance option pricing information"""
    query = """
            SELECT name, pricing_unit, base_price
            FROM car_rental_insurance_option
            WHERE insurance_option_id = %s \
              AND is_active = 1 \
            """

    with get_db_cursor(dictionary=True) as cursor:
        cursor.execute(query, (insurance_option_id,))
        result = cursor.fetchone()

    return result


def calculate_addon_amount(
        addon_info: Dict[str, Any],
        quantity: int,
        rental_days: int
) -> Decimal:
    """Calculate add-on amount based on pricing unit"""
    base_price = Decimal(str(addon_info['base_price']))
    pricing_unit = addon_info['pricing_unit']

    if pricing_unit == 'per_day':
        return base_price * quantity * rental_days
    elif pricing_unit == 'per_rental':
        return base_price * quantity
    else:
        return base_price * quantity


def calculate_insurance_amount(
        insurance_info: Dict[str, Any],
        rental_days: int
) -> Decimal:
    """Calculate insurance amount based on pricing unit"""
    base_price = Decimal(str(insurance_info['base_price']))
    pricing_unit = insurance_info['pricing_unit']

    if pricing_unit == 'per_day':
        return base_price * rental_days
    elif pricing_unit == 'per_rental':
        return base_price
    else:
        return base_price


def calculate_taxes(base_amount: Decimal, tax_rate: Decimal = Decimal('0.13')) -> Decimal:
    """Calculate taxes (default 13% HST for Ontario)"""
    return (base_amount * tax_rate).quantize(Decimal('0.01'))


@bp.route('/make_reservation', methods=['POST'])
def make_reservation():
    """
    Create a new car rental reservation

    Expected JSON Payload:
    {
        "business_id": 1,
        "customer_id": 123,
        "pickup_datetime": "2026-02-15T10:00:00",
        "dropoff_datetime": "2026-02-20T10:00:00",
        "pickup_location_id": 1,
        "dropoff_location_id": 1,
        "vehicle_class_id": 3,
        "vehicle_id": 5,  // optional
        "rate_plan_id": 1,
        "rental_request_id": 10,  // optional
        "add_ons": [  // optional
            {"add_on_id": 1, "quantity": 1},
            {"add_on_id": 2, "quantity": 2}
        ],
        "insurance_options": [  // optional
            {"insurance_option_id": 1}
        ]
    }

    Returns:
    {
        "success": true,
        "response": {
            "reservation_id": 123,
            "vehicle_schedule_id": 456,
            "vehicle_id": 5,
            "base_amount": 350.00,
            "taxes_amount": 45.50,
            "total_amount": 395.50,
            "reservation_status": "confirmed"
        }
    }
    """

    # Parse and validate request
    reservation_req = ReservationRequest(request.get_json() or {})
    is_valid, error_message = reservation_req.validate()

    if not is_valid:
        return jsonify({
            'success': False,
            'error': error_message
        })

    # Get database connection
    connection = None
    cursor = None

    try:
        selected_vehicle_id = reservation_req.vehicle_id

        if not selected_vehicle_id:
            # Find an available vehicle
            selected_vehicle_id = find_available_vehicle(
                reservation_req.business_id,
                reservation_req.vehicle_class_id,
                reservation_req.pickup_location_id,
                reservation_req.pickup_datetime,
                reservation_req.dropoff_datetime
            )

            if not selected_vehicle_id:
                connection.rollback()
                return jsonify({
                    'success': False,
                    'error': 'No vehicles available for the requested class and time period'
                })
        else:
            # Validate specific vehicle
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT v.vehicle_id
                       FROM car_rental_vehicle v
                                JOIN car_rental_vehicle_inventory i ON v.vehicle_id = i.vehicle_id
                       WHERE v.vehicle_id = %s
                         AND v.business_id = %s
                         AND v.is_active = 1
                         AND i.location_id = %s
                         AND i.operational_status = 'ready'""",
                    (selected_vehicle_id, reservation_req.business_id,
                     reservation_req.pickup_location_id)
                )

                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'error': 'Requested vehicle is not available or invalid'
                    })

            # Check availability
            if not check_vehicle_availability(
                    selected_vehicle_id,
                    reservation_req.pickup_datetime,
                    reservation_req.dropoff_datetime
            ):
                return jsonify({
                    'success': False,
                    'error': 'Requested vehicle is not available for the specified time period'
                })

        # 6. Calculate rental days
        rental_days = calculate_rental_days(
            reservation_req.pickup_datetime,
            reservation_req.dropoff_datetime
        )

        # 7. Get rate pricing
        rate_info = get_rate_price(
            reservation_req.vehicle_class_id,
            reservation_req.pickup_location_id,
            reservation_req.pickup_datetime,
            reservation_req.rate_plan_id
        )

        if not rate_info:
            return jsonify({
                'success': False,
                'error': 'No pricing found for the selected rate plan and vehicle class'
            })

        # 8. Calculate base amount
        base_amount = calculate_base_amount(rate_info, rental_days)

        # 9. Process add-ons
        addon_total = Decimal('0.00')
        addon_details = []

        for addon in reservation_req.add_ons:
            addon_info = get_addon_pricing(addon['add_on_id'])
            if not addon_info:
                return jsonify({
                    'success': False,
                    'error': f"Invalid add-on ID: {addon['add_on_id']}"
                })

            addon_amount = calculate_addon_amount(
                addon_info,
                addon['quantity'],
                rental_days
            )
            addon_total += addon_amount
            addon_details.append({
                'add_on_id': addon['add_on_id'],
                'quantity': addon['quantity'],
                'price': addon_amount
            })

        # 10. Process insurance options
        insurance_total = Decimal('0.00')
        insurance_details = []

        for insurance in reservation_req.insurance_options:
            insurance_info = get_insurance_pricing(insurance['insurance_option_id'])
            if not insurance_info:
                return jsonify({
                    'success': False,
                    'error': f"Invalid insurance option ID: {insurance['insurance_option_id']}"
                })

            insurance_amount = calculate_insurance_amount(insurance_info, rental_days)
            insurance_total += insurance_amount
            insurance_details.append({
                'insurance_option_id': insurance['insurance_option_id'],
                'price': insurance_amount
            })

        # 11. Calculate totals
        subtotal = base_amount + addon_total + insurance_total
        taxes_amount = calculate_taxes(subtotal)
        total_amount = subtotal + taxes_amount

        # 12. Create reservation
        insert_reservation_query = """
                                   INSERT INTO car_rental_reservation (business_id, customer_id, \
                                                                       reservation_status, \
                                                                       pickup_datetime, dropoff_datetime, \
                                                                       pickup_location_id, dropoff_location_id, \
                                                                       vehicle_class_id, vehicle_id, rate_plan_id, \
                                                                       base_amount, taxes_amount, total_amount) \
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                                   """
        with db_transaction(dictionary=True) as cursor:
            cursor.execute(insert_reservation_query, (
                reservation_req.business_id,
                reservation_req.customer_id,
                'confirmed',
                reservation_req.pickup_datetime,
                reservation_req.dropoff_datetime,
                reservation_req.pickup_location_id,
                reservation_req.dropoff_location_id,
                reservation_req.vehicle_class_id,
                selected_vehicle_id,
                reservation_req.rate_plan_id,
                float(base_amount),
                float(taxes_amount),
                float(total_amount)
            ))

            reservation_id = cursor.lastrowid

            # 13. Create vehicle schedule block
            insert_schedule_query = """
                                    INSERT INTO car_rental_vehicle_schedule (business_id, vehicle_id, schedule_type, status, \
                                                                             start_datetime, end_datetime, \
                                                                             car_rental_reservation_id) \
                                    VALUES (%s, %s, %s, %s, %s, %s, %s) \
                                    """

            cursor.execute(insert_schedule_query, (
                reservation_req.business_id,
                selected_vehicle_id,
                'reservation',
                'confirmed',
                reservation_req.pickup_datetime,
                reservation_req.dropoff_datetime,
                reservation_id
            ))

            vehicle_schedule_id = cursor.lastrowid

            # 14. Update reservation with schedule ID
            cursor.execute(
                "UPDATE car_rental_reservation SET vehicle_schedule_id = %s WHERE reservation_id = %s",
                (vehicle_schedule_id, reservation_id)
            )

            # 15. Insert add-ons
            for addon_detail in addon_details:
                cursor.execute(
                    """INSERT INTO car_rental_reservation_add_on
                           (reservation_id, add_on_id, quantity, price)
                       VALUES (%s, %s, %s, %s)""",
                    (reservation_id, addon_detail['add_on_id'],
                     addon_detail['quantity'], float(addon_detail['price']))
                )

            # 16. Insert insurance options
            for insurance_detail in insurance_details:
                cursor.execute(
                    """INSERT INTO car_rental_reservation_insurance
                           (reservation_id, insurance_option_id, price)
                       VALUES (%s, %s, %s)""",
                    (reservation_id, insurance_detail['insurance_option_id'],
                     float(insurance_detail['price']))
                )

        # Return success response
        return jsonify({
            'success': True,
            'response': {
                'reservation_id': reservation_id,
                'vehicle_schedule_id': vehicle_schedule_id,
                'vehicle_id': selected_vehicle_id,
                'rental_days': rental_days,
                'base_amount': float(base_amount),
                'addon_amount': float(addon_total),
                'insurance_amount': float(insurance_total),
                'subtotal': float(subtotal),
                'taxes_amount': float(taxes_amount),
                'total_amount': float(total_amount),
                'reservation_status': 'confirmed',
                'pickup_datetime': reservation_req.pickup_datetime.isoformat(),
                'dropoff_datetime': reservation_req.dropoff_datetime.isoformat()
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error creating reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while creating the reservation'
        })


@bp.route('/list_branches', methods=['POST'])
def list_branches():
    """
    List all active car rental branches for a business
    
    Request body: {
        "business_id": 123  # ID of the business
    }
    
    Returns: List of active car rental locations
    """
    data = request.get_json()
    if not data or 'business_id' not in data:
        return jsonify({'error': 'Business ID is required'}), 400

    business_id = data['business_id']
    
    try:
        with get_db_cursor() as cursor:
            query = """
                SELECT 
                    location_id,
                    name,
                    address_line1,
                    address_line2,
                    city,
                    province_state,
                    country,
                    postal_code,
                    latitude,
                    longitude,
                    phone
                FROM car_rental_location
                WHERE business_id = %s AND is_active = 1
                ORDER BY name
            """
            cursor.execute(query, (business_id,))
            columns = [col[0] for col in cursor.description]
            # Step 1: Fetch all rows from the cursor
            rows = cursor.fetchall()

            # Step 2: Initialize the result list
            branches = []

            # Step 3: Convert each row into a dictionary
            for row in rows:
                # Extract only the required columns
                row_data = {col: row[col] for col in columns}

                # Append to the result list
                branches.append(row_data)
            
            return jsonify({
                'success': True,
                'branches': branches
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/confirm_reservation', methods=['POST'])
def confirm_reservation():
    """
    Preview a car rental reservation with detailed pricing and vehicle information
    WITHOUT creating the reservation in the database.
    This allows the customer to review before final confirmation.

    Expected JSON Payload:
    {
        "business_id": 98,
        "customer_id": 52,
        "pickup_datetime": "2026-02-15T10:00:00",
        "dropoff_datetime": "2026-02-20T10:00:00",
        "pickup_location_id": 4,
        "dropoff_location_id": 4,
        "vehicle_class_id": 1,
        "vehicle_id": 1,  // optional
        "rate_plan_id": 1,
        "add_ons": [  // optional
            {"add_on_id": 1, "quantity": 1},
            {"add_on_id": 2, "quantity": 2}
        ],
        "insurance_options": [  // optional
            {"insurance_option_id": 1}
        ]
    }

    Returns:
    {
        "success": true,
        "response": {
            "vehicle_id": 1,
            "car_specs": "Toyota-2024 Camry",
            "rental_days": 5,
            "base_amount": 225.0,
            "addon_amount": 160.0,
            "insurance_amount": 125.0,
            "subtotal": 510.0,
            "taxes_amount": 66.3,
            "total_amount": 576.3,
            "pickup_datetime": "2026-02-15T10:00:00",
            "dropoff_datetime": "2026-02-20T10:00:00",
            "add_ons": [
                {"add_on_id": 1, "add_on_name": "GPS Navigation", "quantity": 1},
                {"add_on_id": 2, "add_on_name": "Child Seat", "quantity": 2}
            ],
            "insurance_options": [
                {"insurance_option_id": 1, "insurance_option_name": "Collision Damage Waiver"}
            ]
        }
    }
    """

    # Parse and validate request
    reservation_req = ReservationRequest(request.get_json() or {})
    is_valid, error_message = reservation_req.validate()

    if not is_valid:
        return jsonify({
            'success': False,
            'error': error_message
        }), 400

    try:
        selected_vehicle_id = reservation_req.vehicle_id

        if not selected_vehicle_id:
            # Find an available vehicle
            selected_vehicle_id = find_available_vehicle(
                reservation_req.business_id,
                reservation_req.vehicle_class_id,
                reservation_req.pickup_location_id,
                reservation_req.pickup_datetime,
                reservation_req.dropoff_datetime
            )

            if not selected_vehicle_id:
                return jsonify({
                    'success': False,
                    'error': 'No vehicles available for the requested class and time period'
                }), 404
        else:
            # Validate specific vehicle exists and is available
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute(
                    """SELECT v.vehicle_id
                       FROM car_rental_vehicle v
                                JOIN car_rental_vehicle_inventory i ON v.vehicle_id = i.vehicle_id
                       WHERE v.vehicle_id = %s
                         AND v.business_id = %s
                         AND v.vehicle_class_id = %s
                         AND v.is_active = 1
                         AND i.location_id = %s
                         AND i.operational_status = 'ready'""",
                    (selected_vehicle_id, reservation_req.business_id,
                     reservation_req.vehicle_class_id, reservation_req.pickup_location_id)
                )

                if not cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'error': 'Requested vehicle is not available or invalid'
                    }), 400

            # Check availability for the time period
            if not check_vehicle_availability(
                    selected_vehicle_id,
                    reservation_req.pickup_datetime,
                    reservation_req.dropoff_datetime
            ):
                return jsonify({
                    'success': False,
                    'error': 'Requested vehicle is not available for the specified time period'
                }), 409

        # Get vehicle specifications
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(
                """SELECT concat(m.model_name, ' ', m.body_type, ' ',v.transmission, ' ',v.model_year) as car_specs
                    FROM car_rental_vehicle v
                    JOIN car_rental_vehicle_model m
                      ON v.vehicle_model_id = m.vehicle_model_id
                    WHERE v.vehicle_id = %s""",
                (selected_vehicle_id,)
            )
            vehicle_info = cursor.fetchone()

        if not vehicle_info:
            return jsonify({
                'success': False,
                'error': 'Vehicle information not found'
            }), 404

        car_specs = vehicle_info['car_specs']

        # Calculate rental days
        rental_days = calculate_rental_days(
            reservation_req.pickup_datetime,
            reservation_req.dropoff_datetime
        )

        # Get rate pricing
        rate_info = get_rate_price(
            reservation_req.vehicle_class_id,
            reservation_req.pickup_location_id,
            reservation_req.pickup_datetime,
            reservation_req.rate_plan_id
        )

        if not rate_info:
            return jsonify({
                'success': False,
                'error': 'No pricing found for the selected rate plan and vehicle class'
            }), 404

        # Calculate base amount
        base_amount = calculate_base_amount(rate_info, rental_days)

        # Process add-ons
        addon_total = Decimal('0.00')
        addon_details = []

        for addon in reservation_req.add_ons:
            addon_info = get_addon_pricing(addon['add_on_id'])
            if not addon_info:
                return jsonify({
                    'success': False,
                    'error': f"Invalid add-on ID: {addon['add_on_id']}"
                }), 400

            addon_amount = calculate_addon_amount(
                addon_info,
                addon['quantity'],
                rental_days
            )
            addon_total += addon_amount
            addon_details.append({
                'add_on_id': addon['add_on_id'],
                'add_on_name': addon_info['name'],
                'quantity': addon['quantity']
            })

        # Process insurance options
        insurance_total = Decimal('0.00')
        insurance_details = []

        for insurance in reservation_req.insurance_options:
            insurance_info = get_insurance_pricing(insurance['insurance_option_id'])
            if not insurance_info:
                return jsonify({
                    'success': False,
                    'error': f"Invalid insurance option ID: {insurance['insurance_option_id']}"
                }), 400

            insurance_amount = calculate_insurance_amount(insurance_info, rental_days)
            insurance_total += insurance_amount
            insurance_details.append({
                'insurance_option_id': insurance['insurance_option_id'],
                'insurance_option_name': insurance_info['name']
            })

        # Calculate totals
        subtotal = base_amount + addon_total + insurance_total
        taxes_amount = calculate_taxes(subtotal)
        total_amount = subtotal + taxes_amount

        response = {
                'vehicle_id': selected_vehicle_id,
                'car_specs': car_specs,
                'rental_days': rental_days,
                'base_amount': float(base_amount),
                'addon_amount': float(addon_total),
                'insurance_amount': float(insurance_total),
                'subtotal': float(subtotal),
                'taxes_amount': float(taxes_amount),
                'total_amount': float(total_amount),
                'pickup_datetime': reservation_req.pickup_datetime.isoformat(),
                'dropoff_datetime': reservation_req.dropoff_datetime.isoformat(),
                'add_ons': addon_details,
                'insurance_options': insurance_details
            }
        confirmation_message = build_voice_confirmation(response)
        # Return preview response (NO database insertion)
        return jsonify({
            'success': True,
            'response': response,
            'confirmation_message': confirmation_message
        })

    except Exception as e:
        current_app.logger.error(f"Error confirming reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing the reservation preview'
        }), 500


@bp.route('/cancel_reservation', methods=['POST'])
def cancel_reservation():
    """
    Cancel an existing car rental reservation

    Expected JSON Payload:
    {
        "reservation_id": 4,
        "business_id": 98  // optional for additional validation
    }

    Returns:
    {
        "success": true,
        "response": {
            "reservation_id": 4,
            "reservation_status": "cancelled",
            "cancelled_at": "2026-01-03T14:30:00",
            "message": "Reservation cancelled successfully"
        }
    }
    """

    data = request.get_json() or {}

    # Validate required fields
    if 'reservation_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: reservation_id'
        }), 400

    reservation_id = data.get('reservation_id')
    business_id = data.get('business_id')  # Optional

    try:
        # Check if reservation exists and get its current status
        with get_db_cursor(dictionary=True) as cursor:
            query = """
                    SELECT reservation_id, \
                           business_id, \
                           reservation_status, \
                           vehicle_schedule_id, \
                           pickup_datetime
                    FROM car_rental_reservation
                    WHERE reservation_id = %s \
                    """

            params = [reservation_id]
            if business_id:
                query += " AND business_id = %s"
                params.append(business_id)

            cursor.execute(query, tuple(params))
            reservation = cursor.fetchone()

        if not reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404

        # Check if reservation can be cancelled
        if reservation['reservation_status'] == 'cancelled':
            return jsonify({
                'success': False,
                'error': 'Reservation is already cancelled'
            }), 400

        if reservation['reservation_status'] == 'completed':
            return jsonify({
                'success': False,
                'error': 'Cannot cancel a completed reservation'
            }), 400

        if reservation['reservation_status'] == 'active':
            return jsonify({
                'success': False,
                'error': 'Cannot cancel an active rental. Please process return first.'
            }), 400

        # Check if pickup time has passed (optional business rule)
        current_time = datetime.now()
        if reservation['pickup_datetime'] and reservation['pickup_datetime'] < current_time:
            return jsonify({
                'success': False,
                'error': 'Cannot cancel a reservation after the pickup time has passed'
            }), 400

        cancelled_at = current_time

        # Cancel the reservation and update vehicle schedule
        with db_transaction(dictionary=True) as cursor:
            # Update reservation status
            cursor.execute(
                """UPDATE car_rental_reservation
                   SET reservation_status = 'cancelled',
                       updated_at         = %s
                   WHERE reservation_id = %s""",
                (cancelled_at, reservation_id)
            )

            # Update or delete vehicle schedule block
            if reservation['vehicle_schedule_id']:
                cursor.execute(
                    """UPDATE car_rental_vehicle_schedule
                       SET status     = 'cancelled',
                           updated_at = %s
                       WHERE vehicle_schedule_id = %s""",
                    (cancelled_at, reservation['vehicle_schedule_id'])
                )

        return jsonify({
            'success': True,
            'response': {
                'reservation_id': reservation_id,
                'reservation_status': 'cancelled',
                'cancelled_at': cancelled_at.isoformat(),
                'message': 'Reservation cancelled successfully'
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error cancelling reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while cancelling the reservation'
        }), 500

@bp.route('/update_reservation', methods=['POST'])
def update_reservation():
    """
    Update an existing car rental reservation
    Can modify: duration (pickup/dropoff times), add-ons, and insurance options
    Vehicle cannot be changed - only availability for new duration is verified

    Expected JSON Payload:
    {
        "reservation_id": 4,
        "business_id": 98,  // optional for validation
        "pickup_datetime": "2026-02-15T10:00:00",  // optional
        "dropoff_datetime": "2026-02-22T10:00:00",  // optional
        "add_ons": [  // optional - replaces all existing add-ons
            {"add_on_id": 1, "quantity": 2},
            {"add_on_id": 3, "quantity": 1}
        ],
        "insurance_options": [  // optional - replaces all existing insurance
            {"insurance_option_id": 2}
        ]
    }

    Returns:
    {
        "success": true,
        "response": {
            "reservation_id": 4,
            "vehicle_id": 1,
            "car_specs": "Toyota-2024 Camry",
            "rental_days": 7,
            "base_amount": 315.0,
            "addon_amount": 180.0,
            "insurance_amount": 140.0,
            "subtotal": 635.0,
            "taxes_amount": 82.55,
            "total_amount": 717.55,
            "reservation_status": "confirmed",
            "pickup_datetime": "2026-02-15T10:00:00",
            "dropoff_datetime": "2026-02-22T10:00:00",
            "add_ons": [
                {"add_on_id": 1, "add_on_name": "GPS Navigation", "quantity": 2},
                {"add_on_id": 3, "add_on_name": "Wifi Hotspot", "quantity": 1}
            ],
            "insurance_options": [
                {"insurance_option_id": 2, "insurance_option_name": "Personal Accident Insurance"}
            ],
            "message": "Reservation updated successfully"
        }
    }
    """

    data = request.get_json() or {}

    # Validate required fields
    if 'reservation_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: reservation_id'
        }), 400

    reservation_id = data.get('reservation_id')
    business_id = data.get('business_id')
    new_pickup_datetime = data.get('pickup_datetime')
    new_dropoff_datetime = data.get('dropoff_datetime')
    new_add_ons = data.get('add_ons')
    new_insurance_options = data.get('insurance_options')

    # Validate at least one field is being updated
    if not any([new_pickup_datetime, new_dropoff_datetime, new_add_ons is not None,
                new_insurance_options is not None]):
        return jsonify({
            'success': False,
            'error': 'At least one field must be provided for update (pickup_datetime, dropoff_datetime, add_ons, or insurance_options)'
        }), 400

    try:
        # Get existing reservation details
        with get_db_cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    r.reservation_id,
                    r.business_id,
                    r.reservation_status,
                    r.pickup_datetime,
                    r.dropoff_datetime,
                    r.vehicle_id,
                    r.vehicle_class_id,
                    r.pickup_location_id,
                    r.dropoff_location_id,
                    r.rate_plan_id,
                    r.vehicle_schedule_id,
                    CONCAT(m.model_name, ' ', m.body_type, ' ', v.transmission, ' ', v.model_year) as car_specs
                FROM car_rental_reservation r
                JOIN car_rental_vehicle v ON r.vehicle_id = v.vehicle_id
                JOIN car_rental_vehicle_model m ON v.vehicle_model_id = m.vehicle_model_id
                WHERE r.reservation_id = %s
                    """

            params = [reservation_id]
            if business_id:
                query += " AND r.business_id = %s"
                params.append(business_id)

            cursor.execute(query, tuple(params))
            reservation = cursor.fetchone()

        if not reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404

        # Check if reservation can be updated
        if reservation['reservation_status'] not in ['confirmed', 'pending']:
            return jsonify({
                'success': False,
                'error': f"Cannot update reservation with status: {reservation['reservation_status']}"
            }), 400

        # Validate and parse datetime if provided
        pickup_datetime = reservation['pickup_datetime']
        dropoff_datetime = reservation['dropoff_datetime']

        if new_pickup_datetime:
            try:
                pickup_datetime = datetime.fromisoformat(new_pickup_datetime.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                return jsonify({
                    'success': False,
                    'error': f"Invalid pickup_datetime format: {str(e)}"
                }), 400

        if new_dropoff_datetime:
            try:
                dropoff_datetime = datetime.fromisoformat(new_dropoff_datetime.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                return jsonify({
                    'success': False,
                    'error': f"Invalid dropoff_datetime format: {str(e)}"
                }), 400

        # Validate date logic
        if dropoff_datetime <= pickup_datetime:
            return jsonify({
                'success': False,
                'error': 'Dropoff datetime must be after pickup datetime'
            }), 400

        # Check vehicle availability if dates are changing
        if new_pickup_datetime or new_dropoff_datetime:
            # Check availability excluding current reservation's schedule
            query = """
                    SELECT COUNT(*) as conflict_count
                    FROM car_rental_vehicle_schedule
                    WHERE vehicle_id = %s
                      AND vehicle_schedule_id != %s
                      AND status IN ('tentative' \
                        , 'confirmed' \
                        , 'active')
                      AND (
                        (start_datetime \
                        < %s \
                      AND end_datetime \
                        > %s) \
                       OR
                        (start_datetime \
                        < %s \
                      AND end_datetime \
                        > %s) \
                       OR
                        (start_datetime >= %s \
                      AND end_datetime <= %s)
                        ) \
                    """

            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute(query, (
                    reservation['vehicle_id'],
                    reservation['vehicle_schedule_id'],
                    dropoff_datetime, pickup_datetime,
                    dropoff_datetime, pickup_datetime,
                    pickup_datetime, dropoff_datetime
                ))
                result = cursor.fetchone()

            if result['conflict_count'] > 0:
                return jsonify({
                    'success': False,
                    'error': 'Vehicle is not available for the requested time period'
                }), 409

        # Calculate rental days
        rental_days = calculate_rental_days(pickup_datetime, dropoff_datetime)

        # Get rate pricing
        rate_info = get_rate_price(
            reservation['vehicle_class_id'],
            reservation['pickup_location_id'],
            pickup_datetime,
            reservation['rate_plan_id']
        )

        if not rate_info:
            return jsonify({
                'success': False,
                'error': 'No pricing found for the rate plan and vehicle class'
            }), 404

        # Calculate base amount
        base_amount = calculate_base_amount(rate_info, rental_days)

        # Process add-ons (use new ones if provided, otherwise keep existing)
        addon_total = Decimal('0.00')
        addon_details = []

        add_ons_to_process = new_add_ons if new_add_ons is not None else []

        # Validate add-ons format if provided
        if new_add_ons is not None:
            if not isinstance(new_add_ons, list):
                return jsonify({
                    'success': False,
                    'error': 'add_ons must be an array'
                }), 400

            for addon in new_add_ons:
                if not isinstance(addon, dict) or 'add_on_id' not in addon or 'quantity' not in addon:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid add_on format. Each must have add_on_id and quantity'
                    }), 400

        for addon in add_ons_to_process:
            addon_info = get_addon_pricing(addon['add_on_id'])
            if not addon_info:
                return jsonify({
                    'success': False,
                    'error': f"Invalid add-on ID: {addon['add_on_id']}"
                }), 400

            addon_amount = calculate_addon_amount(
                addon_info,
                addon['quantity'],
                rental_days
            )
            addon_total += addon_amount
            addon_details.append({
                'add_on_id': addon['add_on_id'],
                'add_on_name': addon_info['name'],
                'quantity': addon['quantity'],
                'price': addon_amount
            })

        # Process insurance options (use new ones if provided, otherwise keep existing)
        insurance_total = Decimal('0.00')
        insurance_details = []

        insurance_to_process = new_insurance_options if new_insurance_options is not None else []

        # Validate insurance format if provided
        if new_insurance_options is not None:
            if not isinstance(new_insurance_options, list):
                return jsonify({
                    'success': False,
                    'error': 'insurance_options must be an array'
                }), 400

            for insurance in new_insurance_options:
                if not isinstance(insurance, dict) or 'insurance_option_id' not in insurance:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid insurance_option format. Each must have insurance_option_id'
                    }), 400

        for insurance in insurance_to_process:
            insurance_info = get_insurance_pricing(insurance['insurance_option_id'])
            if not insurance_info:
                return jsonify({
                    'success': False,
                    'error': f"Invalid insurance option ID: {insurance['insurance_option_id']}"
                }), 400

            insurance_amount = calculate_insurance_amount(insurance_info, rental_days)
            insurance_total += insurance_amount
            insurance_details.append({
                'insurance_option_id': insurance['insurance_option_id'],
                'insurance_option_name': insurance_info['name'],
                'price': insurance_amount
            })

        # Calculate totals
        subtotal = base_amount + addon_total + insurance_total
        taxes_amount = calculate_taxes(subtotal)
        total_amount = subtotal + taxes_amount

        # Update reservation in database
        with db_transaction(dictionary=True) as cursor:
            # Update reservation
            cursor.execute(
                """UPDATE car_rental_reservation
                   SET pickup_datetime  = %s,
                       dropoff_datetime = %s,
                       base_amount      = %s,
                       taxes_amount     = %s,
                       total_amount     = %s,
                       updated_at       = %s
                   WHERE reservation_id = %s""",
                (
                    pickup_datetime,
                    dropoff_datetime,
                    float(base_amount),
                    float(taxes_amount),
                    float(total_amount),
                    datetime.now(),
                    reservation_id
                )
            )

            # Update vehicle schedule if dates changed
            if new_pickup_datetime or new_dropoff_datetime:
                cursor.execute(
                    """UPDATE car_rental_vehicle_schedule
                       SET start_datetime = %s,
                           end_datetime   = %s,
                           updated_at     = %s
                       WHERE vehicle_schedule_id = %s""",
                    (
                        pickup_datetime,
                        dropoff_datetime,
                        datetime.now(),
                        reservation['vehicle_schedule_id']
                    )
                )

            # Update add-ons if provided
            if new_add_ons is not None:
                # Delete existing add-ons
                cursor.execute(
                    "DELETE FROM car_rental_reservation_add_on WHERE reservation_id = %s",
                    (reservation_id,)
                )

                # Insert new add-ons
                for addon_detail in addon_details:
                    cursor.execute(
                        """INSERT INTO car_rental_reservation_add_on
                               (reservation_id, add_on_id, quantity, price)
                           VALUES (%s, %s, %s, %s)""",
                        (
                            reservation_id,
                            addon_detail['add_on_id'],
                            addon_detail['quantity'],
                            float(addon_detail['price'])
                        )
                    )

            # Update insurance options if provided
            if new_insurance_options is not None:
                # Delete existing insurance
                cursor.execute(
                    "DELETE FROM car_rental_reservation_insurance WHERE reservation_id = %s",
                    (reservation_id,)
                )

                # Insert new insurance options
                for insurance_detail in insurance_details:
                    cursor.execute(
                        """INSERT INTO car_rental_reservation_insurance
                               (reservation_id, insurance_option_id, price)
                           VALUES (%s, %s, %s)""",
                        (
                            reservation_id,
                            insurance_detail['insurance_option_id'],
                            float(insurance_detail['price'])
                        )
                    )

        # Prepare response (remove 'price' from details for response)
        response_addons = [
            {
                'add_on_id': addon['add_on_id'],
                'add_on_name': addon['add_on_name'],
                'quantity': addon['quantity']
            }
            for addon in addon_details
        ]

        response_insurance = [
            {
                'insurance_option_id': ins['insurance_option_id'],
                'insurance_option_name': ins['insurance_option_name']
            }
            for ins in insurance_details
        ]

        return jsonify({
            'success': True,
            'response': {
                'reservation_id': reservation_id,
                'vehicle_id': reservation['vehicle_id'],
                'car_specs': reservation['car_specs'],
                'rental_days': rental_days,
                'base_amount': float(base_amount),
                'addon_amount': float(addon_total),
                'insurance_amount': float(insurance_total),
                'subtotal': float(subtotal),
                'taxes_amount': float(taxes_amount),
                'total_amount': float(total_amount),
                'reservation_status': reservation['reservation_status'],
                'pickup_datetime': pickup_datetime.isoformat(),
                'dropoff_datetime': dropoff_datetime.isoformat(),
                'add_ons': response_addons,
                'insurance_options': response_insurance,
                'message': 'Reservation updated successfully'
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error updating reservation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while updating the reservation'
        }), 500


@bp.route('/list_available_vehicles', methods=['POST'])
def list_available_vehicles():
    """
    List all available vehicles for a given time period
    Can optionally filter by location and/or vehicle class

    Expected JSON Payload:
    {
        "business_id": 98,               // mandatory - business ID
        "from": "2026-02-15T10:00:00",  // mandatory - pickup datetime
        "to": "2026-02-20T10:00:00",    // mandatory - dropoff datetime
        "location_id": 1,                // optional - filter by pickup location
        "vehicle_class_id": 2            // optional - filter by vehicle class
    }

    Returns:
    {
        "success": true,
        "response": {
            "available_vehicles": [
                {
                    "vehicle_id": 1,
                    "car_specs": "Camry Sedan Automatic 2024",
                    "vehicle_class_id": 2,
                    "vehicle_class_name": "Standard",
                    "location_id": 1,
                    "location_name": "Downtown Branch",
                    "license_plate": "ABC123",
                    "vin": "1HGBH41JXMN109186",
                    "color": "Silver",
                    "seats": 5,
                    "doors": 4,
                    "transmission": "Automatic",
                    "fuel_type": "Gasoline",
                    "daily_mileage_limit": 200
                },
                {
                    "vehicle_id": 5,
                    "car_specs": "Accord Sedan Automatic 2023",
                    "vehicle_class_id": 2,
                    "vehicle_class_name": "Standard",
                    "location_id": 1,
                    "location_name": "Downtown Branch",
                    "license_plate": "XYZ789",
                    "vin": "1HGBH41JXMN109187",
                    "color": "Blue",
                    "seats": 5,
                    "doors": 4,
                    "transmission": "Automatic",
                    "fuel_type": "Gasoline",
                    "daily_mileage_limit": 200
                }
            ],
            "count": 2,
            "search_criteria": {
                "business_id": 98,
                "from": "2026-02-15T10:00:00",
                "to": "2026-02-20T10:00:00",
                "location_id": 1,
                "vehicle_class_id": 2
            }
        }
    }
    """

    data = request.get_json() or {}

    # Validate required fields
    if 'business_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: business_id'
        }), 400

    if 'from' not in data or 'to' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: from and to datetime are mandatory'
        }), 400

    business_id = int(data.get('business_id'))
    from_datetime = data.get('from')
    to_datetime = data.get('to')
    location_id = data.get('location_id')
    vehicle_class_id = data.get('vehicle_class_id')

    # Validate business_id type
    if not isinstance(business_id, int):
        return jsonify({
            'success': False,
            'error': 'Invalid type for business_id, expected integer'
        }), 400

    # Validate and parse datetime
    try:
        pickup_datetime = datetime.fromisoformat(from_datetime.replace('Z', '+00:00'))
        dropoff_datetime = datetime.fromisoformat(to_datetime.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        return jsonify({
            'success': False,
            'error': f"Invalid datetime format: {str(e)}"
        }), 400

    # Validate date logic
    if dropoff_datetime <= pickup_datetime:
        return jsonify({
            'success': False,
            'error': 'Dropoff datetime (to) must be after pickup datetime (from)'
        }), 400

    try:
        # Build dynamic query
        query = """
                SELECT v.vehicle_id, \
                       CONCAT(m.model_name, ' ', m.body_type, ' ', v.transmission, ' ', v.model_year) as car_specs, 
                       v.vehicle_class_id, 
                       v.daily_price, 
                       v.weekly_price,                     
                       vc.class_name as vehicle_class_name, 
                       i.location_id, 
                       l.name  as location_name, 
                       v.license_plate, 
                       v.vin, 
                       v.color, 
                       v.seats, 
                       v.doors, 
                       v.transmission, 
                       v.fuel_type, 
                       v.daily_mileage_limit
                FROM car_rental_vehicle v
                         JOIN car_rental_vehicle_model m ON v.vehicle_model_id = m.vehicle_model_id
                         JOIN car_rental_vehicle_class vc ON v.vehicle_class_id = vc.vehicle_class_id
                         JOIN car_rental_vehicle_inventory i ON v.vehicle_id = i.vehicle_id
                         JOIN car_rental_location l ON i.location_id = l.location_id
                WHERE v.business_id = %s
                  AND v.is_active = 1
                  AND i.operational_status = 'ready' \
                """

        params = [business_id]

        # Add optional filters
        if location_id:
            query += " AND i.location_id = %s"
            params.append(location_id)

        if vehicle_class_id:
            query += " AND v.vehicle_class_id = %s"
            params.append(vehicle_class_id)

        # Add availability check - exclude vehicles with conflicting schedules
        query += """
              AND NOT EXISTS (
                SELECT 1
                FROM car_rental_vehicle_schedule s
                WHERE s.vehicle_id = v.vehicle_id
                  AND s.status IN ('tentative', 'confirmed', 'active')
                  AND (
                    (s.start_datetime < %s AND s.end_datetime > %s) OR
                    (s.start_datetime < %s AND s.end_datetime > %s) OR
                    (s.start_datetime >= %s AND s.end_datetime <= %s)
                  )
              )
            ORDER BY vc.class_name, m.model_name, v.model_year DESC
        """

        # Add datetime parameters for availability check
        params.extend([
            dropoff_datetime, pickup_datetime,
            dropoff_datetime, pickup_datetime,
            pickup_datetime, dropoff_datetime
        ])

        # Execute query
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(query, tuple(params))
            vehicles = cursor.fetchall()

        # Format response
        available_vehicles = []
        for vehicle in vehicles:
            available_vehicles.append({
                'vehicle_id': vehicle['vehicle_id'],
                'car_specs': vehicle['car_specs'],
                'vehicle_class_id': vehicle['vehicle_class_id'],
                'daily_price': vehicle['daily_price'],
                'weekly_price': vehicle['weekly_price'],
                'vehicle_class_name': vehicle['vehicle_class_name'],
                'location_id': vehicle['location_id'],
                'location_name': vehicle['location_name']
                # 'license_plate': vehicle['license_plate'],
                # 'vin': vehicle['vin'],
                # 'color': vehicle['color'],
                # 'seats': vehicle['seats'],
                # 'doors': vehicle['doors'],
                # 'transmission': vehicle['transmission'],
                # 'fuel_type': vehicle['fuel_type'],
                # 'daily_mileage_limit': vehicle['daily_mileage_limit']
            })

        return jsonify({
            'success': True,
            'response': {
                'available_vehicles': available_vehicles,
                'count': len(available_vehicles),
                'search_criteria': {
                    'business_id': business_id,
                    'from': pickup_datetime.isoformat(),
                    'to': dropoff_datetime.isoformat(),
                    'location_id': location_id,
                    'vehicle_class_id': vehicle_class_id
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error listing available vehicles: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while retrieving available vehicles'
        }), 500


@bp.route('/list_add_ons', methods=['POST'])
def list_add_ons():
    """
    List all active add-ons for a business

    Expected JSON Payload:
    {
        "business_id": 98  // mandatory - business ID
    }

    Returns:
    {
        "success": true,
        "response": {
            "add_ons": [
                {
                    "add_on_id": 1,
                    "name": "GPS Navigation",
                    "pricing_unit": "per_day",
                    "base_price": 10.00
                },
                {
                    "add_on_id": 2,
                    "name": "Child Seat",
                    "pricing_unit": "per_rental",
                    "base_price": 25.00
                },
                {
                    "add_on_id": 3,
                    "name": "Additional Driver",
                    "pricing_unit": "per_day",
                    "base_price": 15.00
                }
            ],
            "count": 3
        }
    }
    """

    data = request.get_json() or {}

    # Validate required field
    if 'business_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: business_id'
        }), 400

    business_id = data.get('business_id')

    # Validate business_id type
    if not isinstance(business_id, int):
        return jsonify({
            'success': False,
            'error': 'Invalid type for business_id, expected integer'
        }), 400

    try:
        # Query to get all active add-ons for the business
        query = """
                SELECT add_on_id, \
                       name, \
                       pricing_unit, \
                       base_price
                FROM car_rental_add_on
                WHERE business_id = %s
                  AND is_active = 1
                ORDER BY name \
                """

        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(query, (business_id,))
            add_ons = cursor.fetchall()

        # Format response
        add_ons_list = []
        for add_on in add_ons:
            add_ons_list.append({
                'add_on_id': add_on['add_on_id'],
                'name': add_on['name'],
                'pricing_unit': add_on['pricing_unit'],
                'base_price': float(add_on['base_price'])
            })

        return jsonify({
            'success': True,
            'response': {
                'add_ons': add_ons_list,
                'count': len(add_ons_list)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error listing add-ons: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while retrieving add-ons'
        }), 500


@bp.route('/list_insurance_options', methods=['POST'])
def list_insurance_options():
    """
    List all active insurance options for a business

    Expected JSON Payload:
    {
        "business_id": 98  // mandatory - business ID
    }

    Returns:
    {
        "success": true,
        "response": {
            "insurance_options": [
                {
                    "insurance_option_id": 1,
                    "name": "Collision Damage Waiver",
                    "pricing_unit": "per_day",
                    "base_price": 25.00
                },
                {
                    "insurance_option_id": 2,
                    "name": "Personal Accident Insurance",
                    "pricing_unit": "per_day",
                    "base_price": 20.00
                },
                {
                    "insurance_option_id": 3,
                    "name": "Theft Protection",
                    "pricing_unit": "per_rental",
                    "base_price": 50.00
                }
            ],
            "count": 3
        }
    }
    """

    data = request.get_json() or {}

    # Validate required field
    if 'business_id' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: business_id'
        }), 400

    business_id = data.get('business_id')

    # Validate business_id type
    if not isinstance(business_id, int):
        return jsonify({
            'success': False,
            'error': 'Invalid type for business_id, expected integer'
        }), 400

    try:
        # Query to get all active insurance options for the business
        query = """
                SELECT insurance_option_id, \
                       name, \
                       pricing_unit, \
                       base_price
                FROM car_rental_insurance_option
                WHERE business_id = %s
                  AND is_active = 1
                ORDER BY name \
                """

        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(query, (business_id,))
            insurance_options = cursor.fetchall()

        # Format response
        insurance_options_list = []
        for insurance in insurance_options:
            insurance_options_list.append({
                'insurance_option_id': insurance['insurance_option_id'],
                'name': insurance['name'],
                'pricing_unit': insurance['pricing_unit'],
                'base_price': float(insurance['base_price'])
            })

        return jsonify({
            'success': True,
            'response': {
                'insurance_options': insurance_options_list,
                'count': len(insurance_options_list)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error listing insurance options: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while retrieving insurance options'
        }), 500