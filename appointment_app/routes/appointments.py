from flask import Blueprint, request, jsonify
from database import get_db_cursor
import mysql.connector
from datetime import datetime

# Create blueprint
bp = Blueprint('appointments', __name__)

@bp.route('/api/appointments', methods=['GET'])
def get_appointments():
    """List all appointments"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT id, business_id, business_customer_id, service_id, 
                   start_time, end_time, status, created_at, updated_at
            FROM appointment
        """)
        appointments = cursor.fetchall()
        return jsonify(appointments)

@bp.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Create a new appointment"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['business_id', 'business_customer_id', 'service_id', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO appointment 
                (business_id, business_customer_id, service_id, start_time, end_time, status)
                VALUES (%(business_id)s, %(business_customer_id)s, %(service_id)s, 
                        %(start_time)s, %(end_time)s, 'scheduled')
            """, data)
            appointment_id = cursor.lastrowid
            
            # Fetch the created appointment
            cursor.execute("""
                SELECT * FROM appointment WHERE id = %s
            """, (appointment_id,))
            appointment = cursor.fetchone()
            return jsonify(appointment), 201
            
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
