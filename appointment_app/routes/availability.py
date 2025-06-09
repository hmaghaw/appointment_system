from flask import Blueprint, request, jsonify
from database import get_db_cursor
from datetime import datetime, time, timedelta
import mysql.connector

bp = Blueprint('availability', __name__)

@bp.route('/', methods=['POST'])
def get_availability():
    data = request.get_json()
    business_phone = data.get('business_phone')
    service_id = data.get('service_id')
    date_str = data.get('date')
    view = data.get('view', 'day')
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    try:
        if view == 'day':
            return get_daily_availability(business_phone, service_id, target_date)
        elif view == 'week':
            return get_weekly_availability(business_phone, service_id, target_date)
        else:
            return jsonify({"error": "Invalid view parameter. Use 'day' or 'week'"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_daily_availability(business_phone, service_id, target_date):
    with get_db_cursor() as cursor:
        # Get business hours for the day
        day_of_week = target_date.weekday()
        cursor.execute("""
            SELECT * FROM business_hours 
            WHERE business_id = (
                SELECT business_id FROM business_phone 
                WHERE phone_number = %s
            ) AND day_of_week = %s
        """, (business_phone, day_of_week))
        
        hours = cursor.fetchone()
        
        if not hours or hours['is_closed']:
            return jsonify({
                "date": target_date.isoformat(),
                "times": []
            })
        
        # Get existing appointments
        cursor.execute("""
            SELECT * FROM appointment 
            WHERE DATE(start_time) = %s 
            AND business_id = (
                SELECT business_id FROM business_phone 
                WHERE phone_number = %s
            )
            AND status != 'cancelled'
            ORDER BY start_time
        """, (target_date, business_phone))
        
        appointments = cursor.fetchall()
        
        # Generate available slots
        available_slots = []
        current_time = datetime.combine(target_date, hours['open_time'])
        close_time = datetime.combine(target_date, hours['close_time'])
        
        # If no appointments, return full day
        if not appointments:
            return jsonify({
                "date": target_date.isoformat(),
                "times": [{
                    "from": hours['open_time'].strftime('%-I:%M%p').lower(),
                    "to": hours['close_time'].strftime('%-I:%M%p').lower()
                }]
            })
        
        # Find available slots between appointments
        for appt in appointments:
            appt_start = appt['start_time']
            if current_time < appt_start:
                available_slots.append({
                    "from": current_time.time().strftime('%-I:%M%p').lower(),
                    "to": appt_start.time().strftime('%-I:%M%p').lower()
                })
            current_time = max(current_time, appt['end_time'])
        
        # Add remaining time after last appointment
        if current_time < close_time:
            available_slots.append({
                "from": current_time.time().strftime('%-I:%M%p').lower(),
                "to": close_time.time().strftime('%-I:%M%p').lower()
            })
        
        return jsonify({
            "date": target_date.isoformat(),
            "times": available_slots
        })

def get_weekly_availability(business_phone, service_id, target_date):
    start_date = target_date - timedelta(days=target_date.weekday())  # Start of week (Monday)
    end_date = start_date + timedelta(days=6)  # End of week (Sunday)
    
    days = []
    current_date = start_date
    
    while current_date <= end_date:
        day_availability = get_daily_availability(business_phone, service_id, current_date)
        days.append(day_availability.get_json())
        current_date += timedelta(days=1)
    
    return jsonify({
        "week_start": start_date.isoformat(),
        "week_end": end_date.isoformat(),
        "days": days
    })
