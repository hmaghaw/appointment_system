from datetime import datetime, timedelta
from database import get_db_cursor


def validate_appointment(business_id, service_id, start_time, end_time):
    """
    Validate an appointment against business rules
    
    Args:
        business_id (int): Business ID
        service_id (int): Service ID
        start_time (datetime): Proposed start time
        end_time (datetime): Proposed end time
        
    Returns:
        tuple: (is_valid, error_message)
    """
    with get_db_cursor() as cursor:
        # Get service duration
        cursor.execute("""
            SELECT duration_minutes FROM service 
            WHERE id = %s AND business_id = %s
        """, (service_id, business_id))
        service = cursor.fetchone()
        
        if not service:
            return False, "Service not found"
            
        # Get business hours for the day
        day_of_week = start_time.weekday()
        cursor.execute("""
            SELECT * FROM business_hours 
            WHERE business_id = %s AND day_of_week = %s
        """, (business_id, day_of_week))
        
        business_hours = cursor.fetchone()
        
        if not business_hours or business_hours['is_closed']:
            return False, "Business is closed on this day"
            
        # Convert business hours to datetime for comparison
        open_time = datetime.combine(start_time.date(), business_hours['open_time'])
        close_time = datetime.combine(start_time.date(), business_hours['close_time'])
        
        # Check if appointment is within business hours
        if start_time < open_time or end_time > close_time:
            return False, "Appointment must be within business hours"
            
        # Check service duration
        expected_duration = timedelta(minutes=service['duration_minutes'])
        actual_duration = end_time - start_time
        
        if abs((actual_duration - expected_duration).total_seconds()) > 60:  # 1 minute tolerance
            return False, f"Appointment duration must be {service['duration_minutes']} minutes"
            
        # Check for overlapping appointments
        cursor.execute("""
            SELECT id FROM appointment 
            WHERE business_id = %s
            AND status != 'cancelled'
            AND (
                (start_time < %s AND end_time > %s) OR  # New appointment starts during existing
                (start_time < %s AND end_time > %s) OR  # New appointment ends during existing
                (start_time >= %s AND end_time <= %s)    # New appointment is within existing
            )
        """, (
            business_id,
            start_time, start_time,  # First condition
            end_time, end_time,      # Second condition
            start_time, end_time     # Third condition
        ))
        
        if cursor.fetchone():
            return False, "Time slot is already booked"
            
    return True, None
