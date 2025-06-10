import pytest
from datetime import datetime, time, timedelta
from email.utils import parsedate_to_datetime
from app import create_app
from database import get_db_cursor

def parse_http_date(date_str):
    """Parse HTTP date string to datetime object"""
    try:
        return parsedate_to_datetime(date_str)
    except (TypeError, ValueError):
        # Fallback to ISO format if HTTP date parsing fails
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

# Test data
BUSINESS_ID = 1
SERVICE_ID = 1
CUSTOMER_ID = 1
TODAY = datetime.now().date()
TEST_DATETIME = datetime.combine(TODAY, time(10, 0))  # 10:00 AM today

# Sample service data for testing
SAMPLE_SERVICE = {
    'service_id': SERVICE_ID,
    'business_id': BUSINESS_ID,
    'name': 'Test Service',
    'duration_minutes': 30,
    'price': 50.00
}

# Sample business hours for testing
BUSINESS_HOURS = {
    'business_id': BUSINESS_ID,
    'day_of_week': TODAY.weekday(),
    'open_time': time(9, 0),  # 9:00 AM
    'close_time': time(17, 0),  # 5:00 PM
    'is_closed': False
}

@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    # Use SQLite in-memory database for testing
    app = create_app({
        'TESTING': True,
        'DB_HOST': 'localhost',
        'DB_USER': 'user',
        'DB_PASSWORD': 'password',
        'DB_NAME': ':memory:',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })

    # Create test data
    with app.app_context():
        with get_db_cursor(commit=True) as cursor:
            # Drop tables if they exist
            cursor.execute("DROP TABLE IF EXISTS appointment")
            cursor.execute("DROP TABLE IF EXISTS service")
            cursor.execute("DROP TABLE IF EXISTS business_hours")
            
            # Create service table
            cursor.execute("""
                CREATE TABLE service (
                    service_id INT NOT NULL PRIMARY KEY,
                    business_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    duration_minutes INT NOT NULL,
                    price DECIMAL(10,2) NOT NULL
                )
            """)
            
            # Create business_hours table
            cursor.execute("""
                CREATE TABLE business_hours (
                    business_hours_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    business_id INT NOT NULL,
                    day_of_week INT NOT NULL,
                    open_time TIME NOT NULL,
                    close_time TIME NOT NULL,
                    is_closed BOOLEAN DEFAULT FALSE,
                    UNIQUE (business_id, day_of_week)
                )
            """)
            
            # Create appointment table
            cursor.execute("""
                CREATE TABLE appointment (
                    appointment_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    business_id INT NOT NULL,
                    customer_id INT NOT NULL,
                    service_id INT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    status VARCHAR(20) DEFAULT 'scheduled',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test service
            cursor.execute("""
                INSERT INTO service 
                (service_id, business_id, name, duration_minutes, price)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    business_id = VALUES(business_id),
                    name = VALUES(name),
                    duration_minutes = VALUES(duration_minutes),
                    price = VALUES(price)
            """, (
                SAMPLE_SERVICE['service_id'],
                SAMPLE_SERVICE['business_id'],
                SAMPLE_SERVICE['name'],
                SAMPLE_SERVICE['duration_minutes'],
                SAMPLE_SERVICE['price']
            ))
            
            # Insert business hours for the entire week
            for day in range(7):
                cursor.execute("""
                    INSERT INTO business_hours 
                    (business_id, day_of_week, open_time, close_time, is_closed)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        open_time = VALUES(open_time),
                        close_time = VALUES(close_time),
                        is_closed = VALUES(is_closed)
                """, (
                    BUSINESS_HOURS['business_id'],
                    day,
                    BUSINESS_HOURS['open_time'].strftime('%H:%M:%S'),
                    BUSINESS_HOURS['close_time'].strftime('%H:%M:%S'),
                    False  # Not closed
                ))

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_create_appointment_success(client):
    """Test creating a valid appointment"""
    # Test data - ensure it's during business hours
    start_time = datetime.combine(TODAY, time(10, 0))  # 10:00 AM today
    
    # Make request
    response = client.post('/api/appointments', json={
        'business_id': BUSINESS_ID,
        'customer_id': CUSTOMER_ID,
        'service_id': SERVICE_ID,
        'start_time': start_time.isoformat()
    })
    
    # Verify response
    assert response.status_code == 201, f"Response: {response.get_json()}"
    data = response.get_json()
    assert data['business_id'] == BUSINESS_ID
    assert data['service_id'] == SERVICE_ID
    assert data['customer_id'] == CUSTOMER_ID
    assert data['status'] == 'scheduled'
    
    # Verify end time is 30 minutes after start time (service duration)
    expected_end_time = start_time + timedelta(minutes=30)
    actual_end_time = parse_http_date(data['end_time'])
    # Compare only the time components since the date might have timezone adjustments
    assert actual_end_time.time() == expected_end_time.time(), \
        f"Expected end time {expected_end_time.time()}, but got {actual_end_time.time()}"

def test_create_appointment_missing_fields(client):
    """Test creating an appointment with missing fields"""
    response = client.post('/api/appointments', json={
        'business_id': BUSINESS_ID,
        # Missing customer_id and service_id
    })
    
    assert response.status_code == 400
    assert 'Missing required fields' in response.get_json()['error']

def test_create_appointment_invalid_time_format(client):
    """Test creating an appointment with invalid time format"""
    response = client.post('/api/appointments', json={
        'business_id': BUSINESS_ID,
        'customer_id': CUSTOMER_ID,
        'service_id': SERVICE_ID,
        'start_time': 'invalid-time-format'
    })
    
    assert response.status_code == 400
    assert 'Invalid date/time format' in response.get_json()['error']

def test_create_appointment_service_not_found(client):
    """Test creating an appointment with non-existent service"""
    start_time = TEST_DATETIME + timedelta(days=1)
    
    response = client.post('/api/appointments', json={
        'business_id': BUSINESS_ID,
        'customer_id': CUSTOMER_ID,
        'service_id': 999,  # Non-existent service
        'start_time': start_time.isoformat()
    })
    
    assert response.status_code == 404
    assert 'Service not found' in response.get_json()['error']

def test_create_appointment_outside_business_hours(client):
    """Test creating an appointment outside business hours"""
    # 8:00 AM (before opening at 9:00 AM)
    start_time = datetime.combine(TODAY, time(8, 0))
    
    response = client.post('/api/appointments', json={
        'business_id': BUSINESS_ID,
        'customer_id': CUSTOMER_ID,
        'service_id': SERVICE_ID,
        'start_time': start_time.isoformat()
    })
    
    assert response.status_code == 400
    response_data = response.get_json()
    assert 'error' in response_data
    assert any(term in response_data['error'].lower() 
              for term in ['outside', 'business hours', 'closed', 'open']), \
           f"Unexpected error message: {response_data['error']}"

def test_search_appointments(client):
    """Test searching for appointments with filters"""
    # Create test appointments with different properties
    now = datetime.now()
    today = now.date()
    tomorrow = today + timedelta(days=1)
    
    # Test data: 4 appointments with different properties
    test_appointments = [
        # Today's appointment for business 1, customer 1
        {
            'business_id': 1,
            'customer_id': 1,
            'service_id': 1,
            'start_time': datetime.combine(today, time(10, 0)),
            'status': 'scheduled'
        },
        # Tomorrow's appointment for business 1, customer 2
        {
            'business_id': 1,
            'customer_id': 2,
            'service_id': 1,
            'start_time': datetime.combine(tomorrow, time(11, 0)),
            'status': 'confirmed'
        },
        # Today's appointment for business 2, customer 1
        {
            'business_id': 2,
            'customer_id': 1,
            'service_id': 2,
            'start_time': datetime.combine(today, time(14, 0)),
            'status': 'scheduled'
        },
        # Tomorrow's appointment for business 2, customer 2
        {
            'business_id': 2,
            'customer_id': 2,
            'service_id': 2,
            'start_time': datetime.combine(tomorrow, time(15, 0)),
            'status': 'cancelled'
        }
    ]
    
    # Insert test appointments
    with client.application.app_context():
        with get_db_cursor(commit=True) as cursor:
            for appt in test_appointments:
                cursor.execute("""
                    INSERT INTO appointment 
                    (business_id, customer_id, service_id, start_time, end_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    appt['business_id'],
                    appt['customer_id'],
                    appt['service_id'],
                    appt['start_time'],
                    appt['start_time'] + timedelta(minutes=30),
                    appt['status']
                ))
    
    # Test 1: Get all appointments
    response = client.post('/api/appointments/search', json={})
    assert response.status_code == 200
    appointments = response.get_json()
    assert len(appointments) == 4
    
    # Test 2: Filter by business_id
    response = client.post('/api/appointments/search', json={'business_id': 1})
    assert response.status_code == 200
    appointments = response.get_json()
    assert len(appointments) == 2
    assert all(a['business_id'] == 1 for a in appointments)
    
    # Test 3: Filter by customer_id
    response = client.post('/api/appointments/search', json={'customer_id': 1})
    assert response.status_code == 200
    appointments = response.get_json()
    assert len(appointments) == 2
    assert all(a['customer_id'] == 1 for a in appointments)
    
    # Test 4: Filter by date range (today only)
    response = client.post('/api/appointments/search', json={
        'start_date': today.isoformat(),
        'end_date': today.isoformat()
    })
    assert response.status_code == 200
    appointments = response.get_json()
    assert len(appointments) == 2
    for appt in appointments:
        # Handle both ISO format and HTTP date format
        try:
            appt_date = datetime.fromisoformat(appt['start_time'].replace('Z', '+00:00')).date()
        except ValueError:
            # Handle HTTP date format (e.g., 'Mon, 09 Jun 2025 14:00:00 GMT')
            appt_date = parsedate_to_datetime(appt['start_time']).date()
        assert appt_date == today
    
    # Test 5: Filter by status
    response = client.post('/api/appointments/search', json={'status': 'scheduled'})
    assert response.status_code == 200
    appointments = response.get_json()
    assert len(appointments) == 2
    assert all(a['status'] == 'scheduled' for a in appointments)
    
    # Test 6: Combined filters
    response = client.post('/api/appointments/search', json={
        'business_id': 1,
        'start_date': today.isoformat(),
        'status': 'scheduled'
    })
    assert response.status_code == 200
    appointments = response.get_json()
    assert len(appointments) == 1
    appt = appointments[0]
    assert appt['business_id'] == 1
    assert appt['status'] == 'scheduled'
    # Handle both ISO format and HTTP date format
    try:
        appt_date = datetime.fromisoformat(appt['start_time'].replace('Z', '+00:00')).date()
    except ValueError:
        appt_date = parsedate_to_datetime(appt['start_time']).date()
    assert appt_date == today
