from datetime import datetime, timedelta, time
from appointment_app.database  import get_db_cursor
from datetime import datetime, timedelta, time


def validate_appointment(business_id, service_id, start_time, end_time, exclude_appointment_id=None):
    """
    Validate an appointment against business rules
    
    Args:
        business_id (int): Business ID
        service_id (int): Service ID
        start_time (datetime): Proposed start time
        end_time (datetime): Proposed end time
        exclude_appointment_id (int, optional): Appointment ID to exclude from conflict check
        
    Returns:
        tuple: (is_valid, error_message)
    """
    with get_db_cursor() as cursor:
        # Get service duration
        cursor.execute("""
            SELECT duration_minutes FROM service 
            WHERE service_id = %s AND business_id = %s
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
        def convert_to_time(td):
            """Convert timedelta to time object"""
            if isinstance(td, timedelta):
                # Convert timedelta to seconds and then to time
                total_seconds = int(td.total_seconds())
                hours = (total_seconds // 3600) % 24
                minutes = (total_seconds // 60) % 60
                seconds = total_seconds % 60
                return time(hour=hours, minute=minutes, second=seconds)
            return td  # Already a time object
            
        open_time_obj = convert_to_time(business_hours['open_time'])
        close_time_obj = convert_to_time(business_hours['close_time'])
        
        open_time = datetime.combine(start_time.date(), open_time_obj)
        close_time = datetime.combine(start_time.date(), close_time_obj)
        
        # Check if appointment is within business hours
        if start_time < open_time or end_time > close_time:
            return False, "Appointment must be within business hours"
            
        # Check service duration
        expected_duration = timedelta(minutes=service['duration_minutes'])
        actual_duration = end_time - start_time
        
        if abs((actual_duration - expected_duration).total_seconds()) > 60:  # 1 minute tolerance
            return False, f"Appointment duration must be {service['duration_minutes']} minutes"
            
        # Check for overlapping appointments
        query = """
            SELECT appointment_id FROM appointment 
            WHERE business_id = %s
            AND status != 'cancelled'
            AND appointment_id != COALESCE(%s, -1)
            AND (
                (start_time < %s AND end_time > %s) OR  # New appointment starts during existing
                (start_time < %s AND end_time > %s) OR  # New appointment ends during existing
                (start_time >= %s AND end_time <= %s)    # New appointment is within existing
            )
        """
        params = [
            business_id,
            exclude_appointment_id,
            start_time, start_time,  # First condition
            end_time, end_time,      # Second condition
            start_time, end_time     # Third condition
        ]
        
        cursor.execute(query, params)
        
        if cursor.fetchone():
            return False, "Time slot is already booked"
            
    return True, None
