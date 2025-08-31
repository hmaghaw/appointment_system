-- Database schema for Windsurf Appointment System

-- Create database with utf8mb4
CREATE DATABASE IF NOT EXISTS appointment_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE appointment_db;

-- Subscription plan tables (must come first due to foreign key references)
CREATE TABLE IF NOT EXISTS subscription_plan (
    subscription_plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL,
    plan_description TEXT,
    billing_cycle ENUM('monthly', 'yearly') NOT NULL DEFAULT 'monthly',
    original_price DECIMAL(10,2),
    final_price DECIMAL(10,2) NOT NULL,
    annual_savings DECIMAL(10,2),
    estimated_monthly_roi DECIMAL(10,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Business table
CREATE TABLE IF NOT EXISTS business (
    business_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Toronto',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    balance_cents BIGINT NOT NULL DEFAULT 0 COMMENT 'Credit balance for top-ups',
    is_auto_recharge BOOLEAN NOT NULL DEFAULT 0 COMMENT 'Enable auto recharge if balance below threshold',
    recharge_threshold INT NOT NULL DEFAULT 10 COMMENT 'Threshold in cents to trigger auto recharge',
    recharge_amount INT NOT NULL DEFAULT 20 COMMENT 'Recharge amount in cents when triggered',
    stripe_customer_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci;


-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'staff' CHECK (role IN ('admin', 'manager', 'staff')),
    business_id INT NOT NULL,
    permissions JSON,
    active BOOLEAN DEFAULT TRUE,
    auth_provider VARCHAR(50) DEFAULT 'email'
        CHECK (auth_provider IN (
            'email', 'google', 'facebook', 'apple',
            'email,google', 'email,facebook', 'email,apple'
        )),
    social_id VARCHAR(255) NULL,
    profile_picture_url VARCHAR(500) NULL,
    phone VARCHAR(20) NULL,
    last_login TIMESTAMP NULL,
    email_verified BOOLEAN DEFAULT FALSE,

    -- Stripe + payments
    stripe_customer_id VARCHAR(255) UNIQUE NULL COMMENT 'Stripe customer ID (cus_xxx)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT check_auth_method CHECK (
        (auth_provider = 'email' AND password_hash IS NOT NULL) OR
        (auth_provider != 'email' AND social_id IS NOT NULL) OR
        (auth_provider LIKE 'email,%' AND password_hash IS NOT NULL AND social_id IS NOT NULL)
    ),

    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,

    INDEX idx_email (email),
    INDEX idx_business_id (business_id),
    INDEX idx_social_id (social_id),
    INDEX idx_active (active),
    INDEX idx_stripe_customer (stripe_customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
-- Password reset tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_token (token),
    INDEX idx_token (token),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Business Messages
CREATE TABLE IF NOT EXISTS business_messages (
    business_message_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'greeting',
    message TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,
    INDEX idx_business_id (business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Languages
CREATE TABLE IF NOT EXISTS language (
    language_code VARCHAR(10) NOT NULL,
    language_name VARCHAR(100) NOT NULL,
    supported BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Language voices
CREATE TABLE IF NOT EXISTS language_voice (
    language_voice_id INT AUTO_INCREMENT NOT NULL,
    language_code     VARCHAR(10) NOT NULL,
    region_code       VARCHAR(20) NOT NULL,
    voice_provider    VARCHAR(100) NOT NULL,
    voice_name        VARCHAR(120) NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (language_voice_id),
    CONSTRAINT fk_language_voice_language FOREIGN KEY (language_code)
        REFERENCES language (language_code)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT uq_language_voice UNIQUE (language_code, region_code, voice_provider, voice_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Business Languages
CREATE TABLE IF NOT EXISTS business_languages (
    business_id INT NOT NULL,
    language_code VARCHAR(10) NOT NULL DEFAULT 'en',
    is_default BOOLEAN NOT NULL DEFAULT TRUE,
    language_voice_id INT,
    PRIMARY KEY (business_id, language_code),
    CONSTRAINT fk_bl_business FOREIGN KEY (business_id)
        REFERENCES business (business_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_bl_language FOREIGN KEY (language_code)
        REFERENCES language (language_code)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Business Phone Numbers
CREATE TABLE IF NOT EXISTS business_phone (
    business_phone_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    phone_sid VARCHAR(34) NOT NULL COMMENT 'Twilio Phone Number SID (starts with PN)',
    friendly_name VARCHAR(255),
    business_phone VARCHAR(20) NOT NULL,
    language_code VARCHAR(10) default 'en',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_phone (business_phone),
    UNIQUE KEY unique_phone_sid (phone_sid),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES language(language_code) ON DELETE SET NULL,
    INDEX idx_phone_sid (phone_sid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Customer
CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    language VARCHAR(10) DEFAULT '' COMMENT 'ISO 639-1 language code (e.g., en, ar, fr)',
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_customer_phone (business_id, customer_phone),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Service
CREATE TABLE IF NOT EXISTS service (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    duration_minutes INT NOT NULL,
    price DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    buffer_before_minutes INT DEFAULT 0,
    buffer_after_minutes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Business Hours
CREATE TABLE IF NOT EXISTS business_hours (
    business_hours_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    open_time TIME,
    close_time TIME,
    is_closed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_day (business_id, day_of_week),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Appointment
CREATE TABLE IF NOT EXISTS appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    customer_id INT NULL,  -- can be NULL if anonymous or deleted
    service_id INT NULL,   -- can be NULL if undecided or deleted
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    booking_type ENUM('appointment','anonymous','block', 'break', 'holiday') NOT NULL DEFAULT 'appointment',
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (service_id) REFERENCES service(service_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Business Admin Phone Numbers
CREATE TABLE IF NOT EXISTS business_admin_phone (
    business_admin_phone_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    admin_phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_admin_phone (business_id, admin_phone),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Indexes
CREATE INDEX idx_appointment_business ON appointment(business_id, start_time, end_time);
CREATE INDEX idx_appointment_customer ON appointment(customer_id);
CREATE INDEX idx_business_phone ON business_phone(business_phone);
CREATE INDEX idx_customer_business ON customer(business_id, customer_phone);

-- Translations
CREATE TABLE IF NOT EXISTS translations (
    translation_id INT AUTO_INCREMENT PRIMARY KEY,
    phrase VARCHAR(255) NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    translated_phrase TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_phrase_language (phrase, language_code),
    INDEX idx_phrase (phrase),
    INDEX idx_language (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Service Translations
CREATE TABLE IF NOT EXISTS service_translation (
    translation_id INT AUTO_INCREMENT PRIMARY KEY,
    service_id INT NOT NULL,
    language_code VARCHAR(10) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_service_language (service_id, language_code),
    FOREIGN KEY (service_id) REFERENCES service(service_id) ON DELETE CASCADE,
    INDEX idx_service_id (service_id),
    INDEX idx_language_code (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Call Metadata
CREATE TABLE IF NOT EXISTS call_meta (
    call_sid VARCHAR(50) NOT NULL,
    business_id INT NULL,
    customer_id INT NULL,
    meta JSON NOT NULL,
    call_start DATETIME NULL,
    call_end DATETIME NULL,
    call_duration INT NULL,
    call_status VARCHAR(50) NULL,
    communication_channel VARCHAR(50) NULL DEFAULT 'phone',
    direction VARCHAR(20) NULL DEFAULT 'inbound',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (call_sid),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    INDEX idx_business_id (business_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_call_start (call_start),
    INDEX idx_call_status (call_status),
    INDEX idx_communication_channel (communication_channel),
    INDEX idx_direction (direction)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Call Conversations
CREATE TABLE IF NOT EXISTS call_conversation (
    call_conversation_id BIGINT NOT NULL AUTO_INCREMENT,
    call_sid VARCHAR(64) NOT NULL,
    name VARCHAR(255) NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NULL,
    function_call JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (call_conversation_id),
    INDEX idx_call_sid (call_sid),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- SMS SID
CREATE TABLE IF NOT EXISTS sms_sid (
    business_id INT NOT NULL,
    customer_id INT NOT NULL,
    sms_sid VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (business_id, customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Twilio Transaction Log
CREATE TABLE twilio_transaction_log (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    payload JSON NOT NULL,
    response JSON,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    http_status_code INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Subscription Plan Feature
CREATE TABLE IF NOT EXISTS subscription_plan_feature (
    subscription_plan_feature_id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_plan_id INT NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value TEXT,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_plan_id) REFERENCES subscription_plan(subscription_plan_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Email Verification Tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    token VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_token (token),
    INDEX idx_token (token),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_used (used)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Premium Numbers
CREATE TABLE IF NOT EXISTS premium_numbers (
  _id INT AUTO_INCREMENT PRIMARY KEY,
  phone_number VARCHAR(20) NOT NULL,
  phone_sid VARCHAR(100),
  price DECIMAL(10, 2) NOT NULL,
  taken BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_phone_number (phone_number),
  INDEX idx_taken (taken),
  INDEX idx_phone_sid (phone_sid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE INDEX idx_phone_number ON premium_numbers (phone_number);

CREATE TABLE IF NOT EXISTS business_ledger (
  ledger_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
  business_id   INT NOT NULL,
  amount_cents  BIGINT NOT NULL,          -- +credit, -debit
  reason        VARCHAR(100),
  comments varchar(500) null,
  request_id    VARCHAR(64) NOT NULL,     -- idempotency key (unique per charge)
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (request_id),
  INDEX (business_id),
  CONSTRAINT fk_business_ledger_business
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB;

CREATE TABLE orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status ENUM('pending','paid','failed','canceled') DEFAULT 'pending',
    stripe_payment_intent_id VARCHAR(64) UNIQUE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_orders_business FOREIGN KEY (business_id) REFERENCES business(business_id)
);
CREATE TABLE provisioning (
    provisioning_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    business_id     INT NOT NULL,
    phone_number    VARCHAR(20) NOT NULL,
    is_premium smallint default 0 null,
    monthly_fee int default 0 null,
    first_time_fee int default 0 null,
    payment_intent_id VARCHAR(64)  NULL,
    status          ENUM('pending','success','failed') DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_provisioning_business
        FOREIGN KEY (business_id) REFERENCES business(business_id)
);