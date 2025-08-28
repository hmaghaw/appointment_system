import os
from appointment_app.database import get_db_cursor
from datetime import datetime, time, timedelta


def format_time(dt):
    """Format time in a cross-platform way
    
    Args:
        dt: Can be a datetime, time, or timedelta object
        
    Returns:
        str: Formatted time string (e.g., '9:00am')
    """
    if isinstance(dt, timedelta):
        # Convert timedelta to time
        hours, remainder = divmod(dt.seconds // 60, 60)
        minutes = remainder % 60
        dt = time(hour=hours, minute=minutes)
    
    # If it's a datetime, get the time part
    if hasattr(dt, 'time'):
        dt = dt.time()
        
    if os.name == 'nt':  # Windows
        return dt.strftime('%#I:%M%p').lower()
    else:  # Unix/Mac
        return dt.strftime('%-I:%M%p').lower()


def get_daily_availability(business_phone, service_id, target_date):
    """
    Get available time slots for a specific day
    
    Args:
        business_phone (str): Business phone number
        service_id (int): Service ID
        target_date (date): Date to check availability for
        
    Returns:
        dict: Dictionary with date and list of available time slots
    """
    with get_db_cursor() as cursor:
        # Get business hours for the day
        day_of_week = target_date.weekday()
        cursor.execute("""
            SELECT * FROM business_hours 
            WHERE business_id = (
                SELECT business_id FROM business_phone 
                WHERE business_phone = %s
            ) AND day_of_week = %s
        """, (business_phone, day_of_week))
        
        hours = cursor.fetchone()
        
        if not hours or hours['is_closed']:
            return {
                "date": target_date.isoformat(),
                "times": []
            }
        
        # Get existing appointments
        cursor.execute("""
            SELECT * FROM appointment 
            WHERE DATE(start_time) = %s 
            AND business_id = (
                SELECT business_id FROM business_phone 
                WHERE business_phone = %s
            )
            AND status != 'cancelled'
            ORDER BY start_time
        """, (target_date, business_phone))
        
        appointments = cursor.fetchall()
        
        # Generate available slots
        available_slots = []
        
        # Helper function to convert time or timedelta to time object
        def to_time(value):
            if isinstance(value, time):
                return value
            elif isinstance(value, timedelta):
                return (datetime.min + value).time()
            return value
            
        # Get open and close times as time objects
        open_time = to_time(hours['open_time'])
        close_time = to_time(hours['close_time'])
        
        # Combine with target date for datetime operations
        open_datetime = datetime.combine(target_date, open_time)
        close_datetime = datetime.combine(target_date, close_time)
            
        current_time = datetime.combine(target_date, open_time)
        close_time = datetime.combine(target_date, close_time)
        
        # If no appointments, return full day
        if not appointments:
            return {
                "date": target_date.isoformat(),
                "times": [{
                    "from": format_time(hours['open_time'].time() if hasattr(hours['open_time'], 'time') else hours['open_time']),
                    "to": format_time(hours['close_time'].time() if hasattr(hours['close_time'], 'time') else hours['close_time'])
                }]
            }
        
        # Check time before first appointment
        first_appointment = min(appointments, key=lambda x: x['start_time'])
        if current_time < first_appointment['start_time']:
            available_slots.append({
                "from": format_time(current_time.time()),
                "to": format_time(first_appointment['start_time'].time())
            })
        
        # Check time between appointments
        for i in range(len(appointments) - 1):
            current_end = appointments[i]['end_time']
            next_start = appointments[i + 1]['start_time']
            if current_end < next_start:
                available_slots.append({
                    "from": format_time(current_end.time()),
                    "to": format_time(next_start.time())
                })
        
        # Check time after last appointment
        last_appointment = max(appointments, key=lambda x: x['end_time'])
        if last_appointment['end_time'] < close_time:
            available_slots.append({
                "from": format_time(last_appointment['end_time'].time()),
                "to": format_time(close_time.time())
            })
        
        return {
            "date": target_date.isoformat(),
            "times": available_slots
        }


def get_weekly_availability(business_phone, service_id, start_date):
    """
    Get available time slots for a week starting from the given date
    
    Args:
        business_phone (str): Business phone number
        service_id (int): Service ID
        start_date (date): Start date of the week
        
    Returns:
        list: List of daily availability objects
    """
    weekly_availability = []
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        daily_availability = get_daily_availability(business_phone, service_id, current_date)
        weekly_availability.append(daily_availability)
    
    return weekly_availability
