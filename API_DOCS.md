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

### Get Business by Phone

```http
POST /business/by-phone
```

**Request Body:**
```json
{
    "business_phone": "+1234567890"
}
```

**Responses:**
- `200 OK` - Returns business information
- `400 Bad Request` - Business phone number is required
- `404 Not Found` - No business found with the provided phone number

**Example Response:**
```json
{
    "business_id": 1,
    "name": "Business Name",
    "email": "business@example.com",
    "address": "123 Business St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "country": "USA",
    "timezone": "America/New_York",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00",
    "business_phone": "+1234567890"
}
```

### Business Messages

#### Get Business Messages

```http
POST /business/messages
```

**Request Body:**
```json
{
    "business_id": 1
}
```

**Responses:**
- `200 OK` - Returns list of active messages for the business
- `400 Bad Request` - Missing or invalid business_id
- `404 Not Found` - No messages found for the business

**Example Response:**
```json
{
    "messages": [
        {
            "business_message_id": 1,
            "business_id": 1,
            "type": "greeting",
            "message": "Welcome to our business!",
            "is_active": true,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "business_name": "Example Business"
        },
        {
            "business_message_id": 2,
            "business_id": 1,
            "type": "confirmation",
            "message": "Your appointment has been confirmed!",
            "is_active": true,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "business_name": "Example Business"
        }
    ],
    "count": 2
}
```

#### Create Business Message

```http
POST /business/messages
```

**Request Body:**
```json
{
    "business_id": 1,
    "message": "Your appointment is confirmed for {time} on {date}.",
    "type": "confirmation",
    "is_active": true
}
```

**Parameters:**
- `business_id` (required): ID of the business this message belongs to
- `message` (required): The message text (can include placeholders like {time}, {date}, etc.)
- `type` (required): Type of the message (e.g., 'greeting', 'confirmation', 'reminder')
- `is_active` (optional, default: true): Whether the message is active

**Responses:**
- `201 Created` - Message created successfully
  ```json
  {
      "business_message_id": 3,
      "business_id": 1,
      "type": "confirmation",
      "message": "Your appointment is confirmed for {time} on {date}.",
      "is_active": true,
      "created_at": "2023-01-01T12:00:00",
      "updated_at": "2023-01-01T12:00:00",
      "business_name": "Example Business"
  }
  ```
- `400 Bad Request` - Missing required fields or invalid data
- `500 Internal Server Error` - Server error

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

## Call History

### Create or Update Call Metadata

```http
POST /call-history/create
```

**Request Body:**
```json
{
    "call_sid": "CA1234567890abcdef1234567890abcdef",
    "meta": {
        "from": "+1234567890",
        "to": "+1987654321",
        "status": "completed",
        "duration": "120",
        "direction": "inbound",
        "recording_url": "https://example.com/recording.mp3"
    }
}
```

**Responses:**
- `200 OK` - Call metadata created or updated successfully
  ```json
  {
      "call_sid": "CA1234567890abcdef1234567890abcdef",
      "status": "success"
  }
  ```
- `400 Bad Request` - Missing required fields
- `500 Internal Server Error` - Server error

### Read Call Metadata (with existence check)

```http
POST /call-history/read
```

**Request Body:**
```json
{
    "call_sid": "CA1234567890abcdef1234567890abcdef"
}
```

**Responses:**

- `200 OK` - Call exists (returns full metadata)
  ```json
  {
      "exists": true,
      "call_sid": "CA1234567890abcdef1234567890abcdef",
      "meta": {
          "from": "+1234567890",
          "to": "+1987654321",
          "status": "completed",
          "duration": "120",
          "direction": "inbound",
          "recording_url": "https://example.com/recording.mp3"
      },
      "created_at": "2023-01-01T12:00:00",
      "updated_at": "2023-01-01T12:05:00"
  }
  ```

- `200 OK` - Call doesn't exist
  ```json
  {
      "exists": false,
      "call_sid": "CA1234567890abcdef1234567890abcdef"
  }
  ```

- `400 Bad Request` - Missing call_sid
  ```json
  {
      "error": "call_sid is required"
  }
  ```

- `500 Internal Server Error` - Server error

## Call History

### Create or Update Call Metadata

```http
POST /api/call-history/create
```

**Request Body:**
```json
{
    "call_sid": "CA1234567890abcdef1234567890abcdef",
    "meta": {
        "from": "+1234567890",
        "to": "+1987654321",
        "status": "completed",
        "duration": "120",
        "direction": "inbound",
        "recording_url": "https://example.com/recording.mp3"
    }
}
```

**Responses:**
- `200 OK` - Call metadata created/updated successfully
- `400 Bad Request` - Missing required fields
- `500 Internal Server Error` - Server error

### Get Call Metadata

```http
POST /api/call-history/read
```

**Request Body:**
```json
{
    "call_sid": "CA1234567890abcdef1234567890abcdef"
}
```

**Success Response (200 OK):**
```json
{
    "exists": true,
    "call_sid": "CA1234567890abcdef1234567890abcdef",
    "meta": {
        "from": "+1234567890",
        "to": "+1987654321",
        "status": "completed"
    },
    "created_at": "2025-06-11T14:30:00",
    "updated_at": "2025-06-11T14:30:00"
}
```

**Not Found Response (200 OK):**
```json
{
    "exists": false,
    "call_sid": "CA1234567890abcdef1234567890abcdef"
}
```

**Error Responses:**
- `400 Bad Request` - Missing call_sid
- `500 Internal Server Error` - Server error

## Call Conversations

### Add Conversation Item

```http
POST /api/call-history/conversation/add
```

**Request Body:**
```json
{
    "call_sid": "CA1234567890abcdef1234567890abcdef",
    "role": "user",
    "content": "Hello, I'd like to book an appointment."
}
```

**Responses:**
- `201 Created` - Conversation item created successfully
- `400 Bad Request` - Missing required fields or invalid role
- `500 Internal Server Error` - Server error

### List Conversation Items

```http
POST /api/call-history/conversation/list
```

**Request Body:**
```json
{
    "call_sid": "CA1234567890abcdef1234567890abcdef"
}
```

**Success Response (200 OK):**
```json
{
    "status": "success",
    "call_sid": "CA1234567890abcdef1234567890abcdef",
    "count": 2,
    "items": [
        {
            "call_conversation_id": 1,
            "call_sid": "CA1234567890abcdef1234567890abcdef",
            "role": "user",
            "content": "Hello, I'd like to book an appointment.",
            "created_at": "2025-06-11T15:30:00",
            "updated_at": "2025-06-11T15:30:00"
        },
        {
            "call_conversation_id": 2,
            "call_sid": "CA1234567890abcdef1234567890abcdef",
            "role": "assistant",
            "content": "I'd be happy to help you with that. What date works for you?",
            "created_at": "2025-06-11T15:30:05",
            "updated_at": "2025-06-11T15:30:05"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request` - Missing call_sid
- `500 Internal Server Error` - Server error

## Rate Limiting
API requests are subject to rate limiting:
- 100 requests per minute per IP address
- 1000 requests per hour per user token

Exceeding these limits will result in a `429 Too Many Requests` response.
