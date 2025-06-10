# Windsurf Appointment System API Documentation

## Base URL
All API endpoints are relative to the base URL: `http://your-domain.com/api`

## Authentication
All API endpoints require authentication using JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## Table of Contents
- [Appointments](#appointments)
- [Availability](#availability)
- [Business](#business)
- [Customers](#customers)

---

## Appointments

### Create Appointment

```http
POST /appointments
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

### Search Appointments

```http
POST /appointments/search
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

### Update Appointment

```http
PUT /appointments
```

**Request Body:**
```json
{
    "id": 1,
    "service_id": 2,
    "start_time": "2025-06-15T15:00:00",
    "status": "rescheduled"
}
```

**Responses:**
- `200 OK` - Appointment updated successfully
- `400 Bad Request` - Invalid data
- `404 Not Found` - Appointment not found

### Cancel Appointment

```http
DELETE /appointments
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

---

## Availability

### Check Daily Availability

```http
POST /availability
```

**Request Body:**
```json
{
    "business_phone": "+15551234567",
    "service_id": 1,
    "date": "2025-06-15",
    "view": "day"
}
```

**Responses:**
- `200 OK` - Returns available time slots for the day
- `400 Bad Request` - Invalid date format or missing fields
- `404 Not Found` - Business or service not found

### Check Weekly Availability

```http
POST /availability
```

**Request Body:**
```json
{
    "business_phone": "+15551234567",
    "service_id": 1,
    "date": "2025-06-15",
    "view": "week"
}
```

**Responses:**
- `200 OK` - Returns available time slots for the week
- `400 Bad Request` - Invalid date format or missing fields
- `404 Not Found` - Business or service not found

---

## Business

### Get Business Greeting

```http
POST /business/greeting
```

**Request Body:**
```json
{
    "business_id": 1
}
```

**Responses:**
- `200 OK` - Returns business greeting information
- `400 Bad Request` - Missing business_id
- `404 Not Found` - Business or greeting not found

---

## Customers

### Create Customer

```http
POST /customers
```

**Request Body:**
```json
{
    "business_id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "customer_phone": "+12025551234",
    "email": "john.doe@example.com",
    "notes": "Preferred contact method: SMS"
}
```

**Responses:**
- `201 Created` - Customer created successfully
- `400 Bad Request` - Missing required fields or invalid data
- `409 Conflict` - Phone number already exists for this business

### Find or Create Customer by Phone

```http
POST /customers/upsert
```

**Request Body:**
```json
{
    "customer_phone": "+12025551234",
    "business_phone": "+15551234567",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
}
```

**Responses:**
- `200 OK` - Customer found
  ```json
  {
      "customer_id": 123,
      "name": "John Doe",
      "email": "john.doe@example.com"
  }
  ```
- `201 Created` - New customer created
- `400 Bad Request` - Missing required fields
- `404 Not Found` - Business not found

### Update Customer

```http
PUT /customers
```

**Request Body:**
```json
{
    "id": 123,
    "first_name": "John",
    "last_name": "Smith",
    "email": "john.smith@example.com",
    "customer_phone": "+12025556789",
    "notes": "Updated contact information",
    "is_active": true
}
```

**Responses:**
- `200 OK` - Customer updated successfully
- `400 Bad Request` - Invalid data
- `404 Not Found` - Customer not found
- `409 Conflict` - Phone number already in use by another customer

## Error Responses

### Standard Error Format
```json
{
    "error": "Error message describing the issue"
}
```

### Common Status Codes
- `400 Bad Request` - Invalid request data or missing required fields
- `401 Unauthorized` - Authentication failed or token missing
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate entry)
- `500 Internal Server Error` - Server error

## Date and Time Format
All dates and times should be in ISO 8601 format:
- Date: `YYYY-MM-DD`
- Time: `HH:MM:SS`
- DateTime: `YYYY-MM-DDTHH:MM:SS`

## Pagination
For endpoints that return lists of items, the following query parameters are supported:
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)

Example: `/api/appointments?page=2&per_page=10`

## Rate Limiting
API requests are subject to rate limiting:
- 100 requests per minute per IP address
- 1000 requests per hour per user token

Exceeding these limits will result in a `429 Too Many Requests` response.
