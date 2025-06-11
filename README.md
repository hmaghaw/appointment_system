# Windsurf Appointment System

A robust appointment scheduling system built with Python, Flask, and MySQL. This system provides RESTful APIs for managing appointments, services, and business hours.

## Features

- **Appointment Management**: Create, view, and manage appointments
- **Customer Management**: Create, update, and find customers by phone number
- **Service Management**: Define services with durations and pricing
- **Business Hours**: Set custom business hours for each day of the week
- **Availability Checking**: Real-time availability checking based on business hours and existing appointments
- **Multi-tenant**: Supports multiple businesses with separate data isolation
- **RESTful API**: Clean, well-documented API endpoints

## API Reference

### Appointments

#### Create Appointment

```http
POST /api/appointments
```

**Request Body:**
```json
{
    "business_id": 1,
    "customer_id": 1,
    "service_id": 1,
    "start_time": "2025-06-15T14:00:00"
}
```

**Responses:**
- `201 Created` - Appointment created successfully
- `400 Bad Request` - Missing required fields or invalid data
- `404 Not Found` - Service not found
- `409 Conflict` - Time slot not available

#### Search Appointments

```http
POST /api/appointments/search
```

**Request Body:**
```json
{
    "business_id": 1,
    "customer_id": 1,
    "start_date": "2025-06-01",
    "end_date": "2025-06-30",
    "status": "scheduled"
}
```

**Responses:**
- `200 OK` - Returns list of matching appointments
- `400 Bad Request` - Invalid date format

#### Update Appointment

```http
PUT /api/appointments
```

**Request Body:**
```json
{
    "appointment_id": 1,
    "service_id": 2,
    "start_time": "2025-06-15T15:00:00",
    "status": "rescheduled"
}
```

**Responses:**
- `200 OK` - Appointment updated successfully
- `400 Bad Request` - Invalid data
- `404 Not Found` - Appointment not found

#### Cancel Appointment

```http
DELETE /api/appointments
```

**Request Body:**
```json
{
    "id": 1
}
```

**Responses:**
- `200 OK` - Appointment cancelled successfully
- `404 Not Found` - Appointment not found
- `400 Bad Request` - Invalid request

### Customers

#### Find or Create Customer by Phone

Finds an existing customer by phone number or creates a new one if not found.

```http
POST /api/customers/upsert
```

**Request Body:**
```json
{
    "customer_phone": "+12025551234",
    "business_phone": "+15551234567",
    "first_name": "John",  // Optional
    "last_name": "Doe",     // Optional
    "email": "john@example.com"  // Optional
}
```

**Responses:**

- `200 OK` - Customer found
  ```json
  {
      "customer_id": 123,
      "name": "John Doe",
      "email": "john@example.com"
  }
  ```

- `201 Created` - New customer created
  ```json
  {
      "customer_id": 124,
      "name": "Guest",
      "email": ""
  }
  ```

- `400 Bad Request` - Missing required fields
  ```json
  {
      "error": "customer_phone and business_phone are required"
  }
  ```

- `404 Not Found` - Business not found
  ```json
  {
      "error": "Business not found with the provided phone number"
  }
  ```

## Tech Stack

- **Backend**: Python 3.8+
- **Framework**: Flask
- **Database**: MySQL 8.0+
- **API Documentation**: OpenAPI/Swagger
- **Testing**: pytest

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/windsurf-appointment-system.git
   cd windsurf-appointment-system
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   FLASK_APP=appointment_app
   FLASK_ENV=development
   DB_HOST=localhost
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_NAME=appointment_system
   SECRET_KEY=your-secret-key-here
   ```

5. Initialize the database:
   ```bash
   flask init-db
   ```

6. Run the development server:
   ```bash
   flask run
   ```

## API Documentation

### Authentication
All API endpoints require authentication using JWT tokens.

### Endpoints

#### Appointments

- `GET /api/appointments` - List all appointments
- `POST /api/appointments` - Create a new appointment
- `PUT /api/appointments` - Update an existing appointment
  ```json
  {
    "appointment_id": 123,
    "service_id": 5,
    "start_time": "2025-06-15T14:00:00",
    "status": "rescheduled"
  }
  ```
- `DELETE /api/appointments` - Cancel an appointment
  ```json
  {
    "id": 123
  }
  ```
  
  **Note:** The cancel endpoint now uses the DELETE method and expects the appointment ID in the request body.

#### Services

- `GET /api/services` - List all services
- `POST /api/services` - Create a new service

#### Business

- `POST /api/business/by-phone` - Get business information by phone number
  ```json
  {
      "business_phone": "+1234567890"
  }
  ```
  Returns business details including name, address, contact info, and timezone.

#### Business Hours

- `GET /api/business-hours` - Get business hours
- `PUT /api/business-hours` - Update business hours

## Running Tests

To run the test suite:

```bash
pytest
```

## Development

### Code Style

This project follows PEP 8 style guidelines. Before committing, please run:

```bash
black .
flake8
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask for the web framework
- SQLAlchemy for ORM
- pytest for testing
- All contributors who have helped improve this project

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Database Design](#database-design)
4. [API Documentation](#api-documentation)
5. [Integration](#integration)
6. [Security](#security)
7. [Deployment](#deployment)

## System Overview

The Appointment Reservation System is a SaaS platform that enables businesses to manage appointments through voice and SMS interactions. The system connects customers with businesses via Twilio-powered phone numbers, providing an AI-driven interface for appointment scheduling and management.

### Key Features
- Multi-tenant architecture supporting multiple businesses
- Voice and SMS-based appointment management
- Business-specific service catalogs
- Customer identification via phone numbers
- Real-time availability checking
- Automated notifications and reminders

## Architecture

### High-Level Block Diagram

```mermaid
graph TD
    A[Customer] -->|Phone Call/SMS| B[Twilio]
    B -->|Webhook| C[Webhook Handler]
    C -->|API Calls| D[Appointment API]
    D --> E[(Database)]
    F[Business Admin] -->|Management| D
    G[System Admin] -->|Administration| D
    H[Background Jobs] -->|Async Processing| D
    
    style A fill:#e1f5fe,stroke:#01579b
    style B fill:#fff3e0,stroke:#e65100
    style C fill:#e8f5e9,stroke#2e7d32
    style D fill:#f3e5f5,stroke#6a1b9a
    style E fill:#e0f7fa,stroke#00838f
    style F fill:#f1f8e9,stroke#33691e
    style G fill#f3e5f5,stroke#4a148c
    style H fill#fff3e0,stroke#e65100
```

### Component Breakdown

1. **Twilio**: Handles all telephony services
2. **Webhook Handler**: Processes incoming calls/SMS from Twilio
3. **Appointment API**: Core business logic and data access
4. **Database**: Persistent data storage
5. **Admin Interfaces**: For business and system administration
6. **Background Jobs**: For notifications and async processing


## Database Schema

### Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    BUSINESS ||--o{ BUSINESS_GREETINGS : has
    BUSINESS ||--o{ BUSINESS_PHONE : has
    BUSINESS ||--o{ CUSTOMER : has
    BUSINESS ||--o{ SERVICE : offers
    BUSINESS ||--o{ BUSINESS_HOURS : has
    CUSTOMER ||--o{ APPOINTMENT : schedules
    SERVICE ||--o{ APPOINTMENT : booked_in
    
    BUSINESS {
        int business_id PK
        string name
        string timezone
        string status
        datetime created_at
        datetime updated_at
    }
    
    BUSINESS_GREETINGS {
        int business_greeting_id PK
        int business_id FK
        text greeting_text
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    BUSINESS_PHONE {
        int business_phone_id PK
        int business_id FK
        string business_phone
        boolean is_primary
        datetime created_at
    }
    
    CUSTOMER {
        int customer_id PK
        int business_id FK
        string customer_phone
        string first_name
        string last_name
        string email
        text notes
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    SERVICE {
        int service_id PK
        int business_id FK
        string name
        text description
        int duration_minutes
        decimal price
        boolean is_active
        int buffer_before_minutes
        int buffer_after_minutes
        datetime created_at
        datetime updated_at
    }
    
    BUSINESS_HOURS {
        int business_hours_id PK
        int business_id FK
        tinyint day_of_week
        time open_time
        time close_time
        boolean is_closed
        datetime created_at
        datetime updated_at
    }
    
    APPOINTMENT {
        int appointment_id PK
        int business_id FK
        int customer_id FK
        int service_id FK
        datetime start_time
        datetime end_time
        string status
        text notes
        datetime created_at
        datetime updated_at
    }
```


#### Textual ERD
```
BUSINESS
  - id (PK)
  - name
  - timezone
  - status
  - created_at
  - updated_at

BUSINESS_PHONE
  - id (PK)
  - business_id (FK to BUSINESS)
  - phone_number
  - is_primary
  - created_at

SERVICE
  - id (PK)
  - business_id (FK to BUSINESS)
  - name
  - description
  - duration_minutes
  - price
  - is_active
  - buffer_before_minutes
  - buffer_after_minutes
  - created_at
  - updated_at

CUSTOMER
  - id (PK)
  - phone_number
  - first_name
  - last_name
  - email
  - created_at
  - updated_at

BUSINESS_CUSTOMER
  - id (PK)
  - business_id (FK to BUSINESS)
  - customer_id (FK to CUSTOMER)
  - phone_number
  - first_name
  - last_name
  - email
  - notes
  - created_at
  - updated_at

APPOINTMENT
  - id (PK)
  - business_id (FK to BUSINESS)
  - business_customer_id (FK to BUSINESS_CUSTOMER)
  - service_id (FK to SERVICE)
  - start_time
  - end_time
  - status
  - notes
  - created_at
  - updated_at

BUSINESS_HOURS
  - id (PK)
  - business_id (FK to BUSINESS)
  - day_of_week
  - open_time
  - close_time
  - is_closed
  - created_at
  - updated_at
```

## API Documentation

The Appointment System provides a RESTful API for managing appointments and checking availability. The API follows REST conventions and returns JSON responses.

### Base URL
```
http://localhost:5000/api
```

### Authentication
All endpoints require an API key. Include it in the `Authorization` header:
```
Authorization: Bearer YOUR_API_KEY
```

### Error Responses
All error responses follow this format:
```json
{
  "error": "Error message describing the issue"
}
```

### Health Check

#### Check API Status
```
GET /health
```

**Response**
```json
{
  "status": "healthy"
}
```

### Appointments

#### List All Appointments
```
GET /appointments
```

**Response**
```json
[
  {
    "id": 1,
    "business_id": 1,
    "business_customer_id": 1,
    "service_id": 1,
    "start_time": "2025-06-10T10:00:00",
    "end_time": "2025-06-10T11:00:00",
    "status": "scheduled",
    "created_at": "2025-06-09T08:00:00",
    "updated_at": "2025-06-09T08:00:00"
  }
]
```

#### Create New Appointment
```
POST /appointments
```

**Request Body**
```json
{
  "business_id": 1,
  "business_customer_id": 1,
  "service_id": 1,
  "start_time": "2025-06-10T10:00:00",
  "end_time": "2025-06-10T11:00:00"
}
```

**Response (201 Created)**
```json
{
  "id": 1,
  "business_id": 1,
  "business_customer_id": 1,
  "service_id": 1,
  "start_time": "2025-06-10T10:00:00",
  "end_time": "2025-06-10T11:00:00",
  "status": "scheduled",
  "created_at": "2025-06-09T08:00:00",
  "updated_at": "2025-06-09T08:00:00"
}
```

**Error Responses**
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Server error

### Availability

#### Check Availability
```
POST /availability
```

**Request Body**
```json
{
  "business_phone": "+12025551234",
  "service_id": 1,
  "date": "2025-06-10",
  "view": "day"
}
```

**Parameters**
- `business_phone` (string, required): Business phone number in E.164 format
- `service_id` (integer, required): ID of the service
- `date` (string, required): Date in YYYY-MM-DD format
- `view` (string, optional): 'day' or 'week' (default: 'day')

**Response**
```json
{
  "date": "2025-06-10",
  "times": [
    "09:00",
    "09:30",
    "10:00",
    "10:30",
    "11:00"
  ]
}
```

### Swagger UI
For interactive API documentation and testing, access the Swagger UI at:
```
http://localhost:5000/api/docs
```

### 1. Business Management

#### Get Business by Phone
```http
POST /businesses/lookup
Content-Type: application/json

{
    "business_phone": "+1234567890"
}
```

#### Update Business
```http
POST /businesses/update
Content-Type: application/json

{
    "business_phone": "+1234567890",
    "updates": {
        "name": "New Business Name",
        "timezone": "America/New_York"
    }
}
```

### 2. Customer Management

#### Find or Create Customer
```http
POST /customers/find-or-create
Content-Type: application/json

{
    "business_phone": "+1234567890",
    "customer_phone": "+1987654321",
    "customer_details": {
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### 3. Appointment Management

#### Check Availability
```http
POST /appointments/availability
Content-Type: application/json

{
    "business_phone": "+1234567890",
    "service_id": 1,
    "date_range": {
        "start_date": "2025-06-15",
        "end_date": "2025-06-22"
    }
}
```

#### Book Appointment
```http
POST /appointments
Content-Type: application/json

{
    "business_phone": "+1234567890",
    "customer_phone": "+1987654321",
    "appointment_details": {
        "service_id": 1,
        "start_time": "2025-06-15T09:00:00-04:00"
    }
}
```

### 4. Service Management

#### List Services
```http
POST /services/list
Content-Type: application/json

{
    "business_phone": "+1234567890"
}
```

#### Get Service Details
```http
POST /services/details
Content-Type: application/json

{
    "business_phone": "+1234567890",
    "service_id": 1
}
```

#### Create Service
```http
POST /services/create
Content-Type: application/json

{
    "business_phone": "+1234567890",
    "service_details": {
        "name": "Haircut",
        "description": "Professional haircut with styling",
        "duration_minutes": 30,
        "price": 35.00
    }
}
```

## Integration

### Twilio Webhook Configuration

#### Incoming Call Webhook
```
POST https://webhooks.appointments.example.com/twilio/voice
```

#### Expected Request Format
```http
POST /twilio/voice
Content-Type: application/x-www-form-urlencoded

Called=+1234567890&Caller=+1987654321&CallSid=CA123...
```

#### Example Response (TwiML)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather numDigits="1" action="/twilio/menu" method="POST">
        <Say>Thank you for calling Sample Business. Press 1 to book an appointment. Press 2 for business hours. Press 3 to speak with a representative.</Say>
    </Gather>
</Response>
```

## Security

### Authentication & Authorization
- API Key authentication for all endpoints
- Role-based access control (Business Admin, Staff, System Admin)
- JWT for web sessions

### Data Protection
- All sensitive data encrypted at rest
- TLS 1.2+ for all communications
- Rate limiting on all endpoints
- Input validation and sanitization

### Compliance
- GDPR compliant data handling
- PCI DSS compliance for payment processing
- Regular security audits

## Deployment

### Infrastructure Requirements
- Containerized deployment (Docker)
- Orchestration (Kubernetes/ECS)
- PostgreSQL 13+ database
- Redis for caching
- Object storage for media

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Security
JWT_SECRET=your-secret-key
API_KEYS=webhook-key-123,business-key-456

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token

# App
NODE_ENV=production
PORT=3000
```

### Monitoring
- Prometheus for metrics
- Grafana for visualization
- ELK stack for logging
- Sentry for error tracking

---

This document provides a comprehensive overview of the Appointment Reservation System. For implementation details or specific integration questions, please refer to the API documentation or contact the development team.
