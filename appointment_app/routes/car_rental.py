from flask import Blueprint, jsonify, request
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..database import get_db_cursor

bp = Blueprint('car_rental', __name__, url_prefix='/api/car-rental')

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
