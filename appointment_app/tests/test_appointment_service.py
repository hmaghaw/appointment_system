import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, time, timedelta
from services.appointment_service import validate_appointment

# Test data
BUSINESS_ID = 1
SERVICE_ID = 1
TODAY = datetime.now().date()
TEST_DATETIME = datetime.combine(TODAY, time(10, 0))  # 10:00 AM today

# Mock data
MOCK_SERVICE = {'duration_minutes': 30}
MOCK_BUSINESS_HOURS = {
    'open_time': time(9, 0),  # 9:00 AM
    'close_time': time(17, 0),  # 5:00 PM
    'is_closed': False
}

# Fixture for the database cursor
@pytest.fixture
def mock_db_cursor():
    with patch('services.appointment_service.get_db_cursor') as mock_cursor:
        yield mock_cursor

def test_validate_appointment_success(mock_db_cursor):
    """Test successful appointment validation"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Mock service lookup
    mock_cursor.fetchone.side_effect = [
        MOCK_SERVICE,  # Service lookup
        MOCK_BUSINESS_HOURS,  # Business hours
        None  # No overlapping appointments
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Test data
    start_time = TEST_DATETIME
    end_time = start_time + timedelta(minutes=30)  # 30 min service
    
    # Execute
    is_valid, error = validate_appointment(BUSINESS_ID, SERVICE_ID, start_time, end_time)
    
    # Verify
    assert is_valid is True
    assert error is None
    
    # Verify SQL queries were executed
    assert mock_cursor.execute.call_count == 3

def test_validate_appointment_service_not_found(mock_db_cursor):
    """Test validation when service is not found"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Service not found
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    is_valid, error = validate_appointment(BUSINESS_ID, 999, TEST_DATETIME, TEST_DATETIME + timedelta(hours=1))
    
    # Verify
    assert is_valid is False
    assert "Service not found" in error

def test_validate_appointment_business_closed(mock_db_cursor):
    """Test validation when business is closed"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [
        MOCK_SERVICE,
        {'is_closed': True}  # Business is closed
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Execute
    is_valid, error = validate_appointment(BUSINESS_ID, SERVICE_ID, TEST_DATETIME, TEST_DATETIME + timedelta(hours=1))
    
    # Verify
    assert is_valid is False
    assert "Business is closed" in error

def test_validate_appointment_outside_hours(mock_db_cursor):
    """Test validation when appointment is outside business hours"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [
        MOCK_SERVICE,
        MOCK_BUSINESS_HOURS
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Test data - before opening
    start_time = datetime.combine(TODAY, time(8, 0))  # 8:00 AM
    end_time = start_time + timedelta(minutes=30)
    
    # Execute
    is_valid, error = validate_appointment(BUSINESS_ID, SERVICE_ID, start_time, end_time)
    
    # Verify
    assert is_valid is False
    assert "within business hours" in error

def test_validate_appointment_wrong_duration(mock_db_cursor):
    """Test validation when appointment duration doesn't match service duration"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [
        MOCK_SERVICE,  # Service lookup
        MOCK_BUSINESS_HOURS  # Business hours
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Test data - 1 hour instead of 30 minutes
    start_time = TEST_DATETIME
    end_time = start_time + timedelta(hours=1)
    
    # Execute
    is_valid, error = validate_appointment(BUSINESS_ID, SERVICE_ID, start_time, end_time)
    
    # Verify
    assert is_valid is False
    assert "duration must be 30 minutes" in error

def test_validate_appointment_overlapping(mock_db_cursor):
    """Test validation when there's an overlapping appointment"""
    # Setup mock
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.side_effect = [
        MOCK_SERVICE,  # Service lookup
        MOCK_BUSINESS_HOURS,  # Business hours
        {'id': 1, 'start_time': TEST_DATETIME, 'end_time': TEST_DATETIME + timedelta(minutes=30)}  # Overlapping appointment
    ]
    mock_db_cursor.return_value = mock_cursor
    
    # Test data
    start_time = TEST_DATETIME
    end_time = start_time + timedelta(minutes=30)
    
    # Execute
    is_valid, error = validate_appointment(BUSINESS_ID, SERVICE_ID, start_time, end_time)
    
    # Verify
    assert is_valid is False
    assert "already booked" in error
