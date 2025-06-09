import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, time, timedelta
from services.availability_service import get_daily_availability

# Test data
BUSINESS_PHONE = "+12025551234"
SERVICE_ID = 1
TARGET_DATE = datetime(2025, 6, 10).date()  # A Tuesday
BUSINESS_ID = 1

# Common business hours (9 AM to 5 PM)
BUSINESS_HOURS = {
    'business_id': BUSINESS_ID,
    'day_of_week': 1,  # Tuesday (0=Monday, 6=Sunday)
    'open_time': time(9, 0),  # 9:00 AM
    'close_time': time(17, 0),  # 5:00 PM
    'is_closed': False
}

# Helper function to create mock appointments
def create_appointment(start_time_str, end_time_str):
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M')
    return {
        'start_time': start_time,
        'end_time': end_time
    }

# Fixture for the database cursor
@pytest.fixture
def mock_db_cursor():
    with patch('services.availability_service.get_db_cursor') as mock_cursor:
        yield mock_cursor

def test_full_day_available(mock_db_cursor):
    """Test when the entire day is available (no appointments)"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = BUSINESS_HOURS
    mock_cursor.fetchall.return_value = []
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    result = get_daily_availability(BUSINESS_PHONE, SERVICE_ID, TARGET_DATE)
    
    # Verify
    assert result['date'] == '2025-06-10'
    assert len(result['times']) == 1
    assert result['times'][0]['from'] == '9:00am'
    assert result['times'][0]['to'] == '5:00pm'

def test_closed_business(mock_db_cursor):
    """Test when business is closed on the given day"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    closed_hours = BUSINESS_HOURS.copy()
    closed_hours['is_closed'] = True
    mock_cursor.fetchone.return_value = closed_hours
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    result = get_daily_availability(BUSINESS_PHONE, SERVICE_ID, TARGET_DATE)
    
    # Verify
    assert result['date'] == '2025-06-10'
    assert len(result['times']) == 0

def test_single_appointment_middle_of_day(mock_db_cursor):
    """Test with a single appointment in the middle of the day"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = BUSINESS_HOURS
    mock_cursor.fetchall.return_value = [
        create_appointment('2025-06-10 12:00', '2025-06-10 13:00')
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    result = get_daily_availability(BUSINESS_PHONE, SERVICE_ID, TARGET_DATE)
    
    # Verify
    assert len(result['times']) == 2
    assert result['times'][0]['from'] == '9:00am'
    assert result['times'][0]['to'] == '12:00pm'
    assert result['times'][1]['from'] == '1:00pm'
    assert result['times'][1]['to'] == '5:00pm'

def test_multiple_appointments(mock_db_cursor):
    """Test with multiple appointments throughout the day"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = BUSINESS_HOURS
    mock_cursor.fetchall.return_value = [
        create_appointment('2025-06-10 10:00', '2025-06-10 11:00'),
        create_appointment('2025-06-10 13:00', '2025-06-10 14:00'),
        create_appointment('2025-06-10 15:00', '2025-06-10 16:00')
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    result = get_daily_availability(BUSINESS_PHONE, SERVICE_ID, TARGET_DATE)
    
    # Verify
    assert len(result['times']) == 4
    assert result['times'][0]['from'] == '9:00am'
    assert result['times'][0]['to'] == '10:00am'
    assert result['times'][1]['from'] == '11:00am'
    assert result['times'][1]['to'] == '1:00pm'
    assert result['times'][2]['from'] == '2:00pm'
    assert result['times'][2]['to'] == '3:00pm'
    assert result['times'][3]['from'] == '4:00pm'
    assert result['times'][3]['to'] == '5:00pm'

def test_appointment_at_opening(mock_db_cursor):
    """Test when there's an appointment right at opening time"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = BUSINESS_HOURS
    mock_cursor.fetchall.return_value = [
        create_appointment('2025-06-10 09:00', '2025-06-10 10:00')
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    result = get_daily_availability(BUSINESS_PHONE, SERVICE_ID, TARGET_DATE)
    
    # Verify
    assert len(result['times']) == 1
    assert result['times'][0]['from'] == '10:00am'
    assert result['times'][0]['to'] == '5:00pm'

def test_appointment_at_closing(mock_db_cursor):
    """Test when there's an appointment right before closing"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = BUSINESS_HOURS
    mock_cursor.fetchall.return_value = [
        create_appointment('2025-06-10 16:00', '2025-06-10 17:00')
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    result = get_daily_availability(BUSINESS_PHONE, SERVICE_ID, TARGET_DATE)
    
    # Verify
    assert len(result['times']) == 1
    assert result['times'][0]['from'] == '9:00am'
    assert result['times'][0]['to'] == '4:00pm'
