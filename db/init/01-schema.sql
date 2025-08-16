-- Database schema for Windsurf Appointment System

-- Create database
#CREATE DATABASE IF NOT EXISTS appointment_db;

CREATE DATABASE IF NOT EXISTS appointment_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE appointment_db;

-- Subscription plan tables (must come first due to foreign key references)
CREATE TABLE IF NOT EXISTS subscription_plan (
    subscription_plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL,
    plan_description TEXT,
    billing_cycle ENUM('monthly', 'yearly') NOT NULL DEFAULT 'monthly',
    original_price DECIMAL(10,2),         -- e.g., 99.00
    final_price DECIMAL(10,2) NOT NULL,   -- e.g., 79.00
    annual_savings DECIMAL(10,2),         -- e.g., 240.00
    estimated_monthly_roi DECIMAL(10,2),  -- e.g., 24921.00
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Business table
CREATE TABLE IF NOT EXISTS business (
    business_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    subscription_plan_id INT DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (subscription_plan_id) REFERENCES subscription_plan(subscription_plan_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- Users table for authentication and user management
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NULL,  -- NULL for social login users
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'staff' CHECK (role IN ('admin', 'manager', 'staff')),
    business_id INT NOT NULL,
    permissions JSON,
    active BOOLEAN DEFAULT TRUE,
    auth_provider VARCHAR(50) DEFAULT 'email' CHECK (auth_provider IN ('email', 'google', 'facebook', 'apple', 'email,google', 'email,facebook', 'email,apple')),
    social_id VARCHAR(255) NULL,  -- Provider's unique user ID
    profile_picture_url VARCHAR(500) NULL,
    phone VARCHAR(20) NULL,
    last_login TIMESTAMP NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Ensure either password or social login exists
    CONSTRAINT check_auth_method CHECK (
        (auth_provider = 'email' AND password_hash IS NOT NULL) OR
        (auth_provider != 'email' AND social_id IS NOT NULL) OR
        (auth_provider LIKE 'email,%' AND password_hash IS NOT NULL AND social_id IS NOT NULL)
    ),

    -- Foreign key to business
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,

    -- Indexes for performance
    INDEX idx_email (email),
    INDEX idx_business_id (business_id),
    INDEX idx_social_id (social_id),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Password reset tokens for user authentication
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB;

-- Languages
CREATE TABLE IF NOT EXISTS language (
    language_code VARCHAR(10) NOT NULL,
    language_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (language_code)
) ENGINE=InnoDB;

-- Language voices with surrogate PK and unique constraint
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
) ENGINE=InnoDB;

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
) ENGINE=InnoDB;

-- Business Phone Numbers
CREATE TABLE IF NOT EXISTS business_phone (
    business_phone_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    phone_sid VARCHAR(34) NOT NULL COMMENT 'Twilio Phone Number SID (starts with PN)',
    friendly_name VARCHAR(255) NOT NULL COMMENT 'User-friendly name for the phone number',
    business_phone VARCHAR(20) NOT NULL,
    language_code VARCHAR(10),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_phone (business_phone),
    UNIQUE KEY unique_phone_sid (phone_sid),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,
    FOREIGN KEY (language_code) REFERENCES language(language_code) ON DELETE SET NULL,
    INDEX idx_phone_sid (phone_sid)
) ENGINE=InnoDB;

-- Customer table
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
) ENGINE=InnoDB;

-- Service table
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
) ENGINE=InnoDB;

-- Business Hours
CREATE TABLE IF NOT EXISTS business_hours (
    business_hours_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    day_of_week TINYINT NOT NULL, -- 0=Monday, 6=Sunday
    open_time TIME,
    close_time TIME,
    is_closed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_day (business_id, day_of_week),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Appointment table
CREATE TABLE IF NOT EXISTS appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    customer_id INT NOT NULL,
    service_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled', -- scheduled, confirmed, completed, cancelled, no_show
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES service(service_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Business Admin Phone Numbers
CREATE TABLE IF NOT EXISTS business_admin_phone (
    business_admin_phone_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    admin_phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_admin_phone (business_id, admin_phone),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Add indexes for performance
CREATE INDEX idx_appointment_business ON appointment(business_id, start_time, end_time);
CREATE INDEX idx_appointment_customer ON appointment(customer_id);
CREATE INDEX idx_business_phone ON business_phone(business_phone);
CREATE INDEX idx_customer_business ON customer(business_id, customer_phone);

-- Translations table
CREATE TABLE IF NOT EXISTS translations (
    translation_id INT AUTO_INCREMENT PRIMARY KEY,
    phrase VARCHAR(255) NOT NULL COMMENT 'The original phrase to be translated',
    language_code VARCHAR(10) NOT NULL COMMENT 'ISO 639-1 language code (e.g., en, ar, fr)',
    translated_phrase TEXT NOT NULL COMMENT 'The translated phrase in the target language',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_phrase_language (phrase, language_code),
    INDEX idx_phrase (phrase),
    INDEX idx_language (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Service Translations
CREATE TABLE IF NOT EXISTS service_translation (
    translation_id INT AUTO_INCREMENT PRIMARY KEY,
    service_id INT NOT NULL,
    language_code VARCHAR(10) NOT NULL COMMENT 'ISO 639-1 language code (e.g., en, es, fr)',
    name VARCHAR(255) COMMENT 'Translated service name',
    description TEXT COMMENT 'Translated service description',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_service_language (service_id, language_code),
    FOREIGN KEY (service_id) REFERENCES service(service_id) ON DELETE CASCADE,
    INDEX idx_service_id (service_id),
    INDEX idx_language_code (language_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Stores translations for service names and descriptions';

CREATE TABLE IF NOT EXISTS `call_meta` (
    `call_sid` VARCHAR(50) NOT NULL COMMENT 'Unique identifier for the call from the telephony provider',
    `business_id` INT NULL COMMENT 'Business ID associated with the call',
    `customer_id` INT NULL COMMENT 'Customer ID associated with the call',
    `meta` JSON NOT NULL COMMENT 'JSON object containing call metadata',
    `call_start` DATETIME NULL COMMENT 'When the call started',
    `call_end` DATETIME NULL COMMENT 'When the call ended',
    `call_duration` INT NULL COMMENT 'Call duration in seconds',
    `call_status` VARCHAR(50) NULL COMMENT 'Status of the call (e.g., Completed, In Progress)',
    `communication_channel` VARCHAR(50) NULL DEFAULT 'phone' COMMENT 'Communication channel (e.g., phone, sms, whatsapp)',
    `direction` VARCHAR(20) NULL DEFAULT 'inbound' COMMENT 'Call direction (inbound/outbound)',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When the call record was first created',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'When the call record was last updated',
    PRIMARY KEY (`call_sid`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_updated_at` (`updated_at`),
    INDEX `idx_business_id` (`business_id`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_call_start` (`call_start`),
    INDEX `idx_call_status` (`call_status`),
    INDEX `idx_communication_channel` (`communication_channel`),
    INDEX `idx_direction` (`direction`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Stores call metadata with call_sid as primary key';

CREATE TABLE IF NOT EXISTS `call_conversation` (
    `call_conversation_id` BIGINT NOT NULL AUTO_INCREMENT,
    `call_sid` VARCHAR(64) NOT NULL,
    `name` VARCHAR(255) NULL,
    `role` VARCHAR(50) NOT NULL,
    `content` TEXT NULL,
    `function_call` JSON NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`call_conversation_id`),
    INDEX `idx_call_sid` (`call_sid`),
    INDEX `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table to track SMS message IDs
CREATE TABLE IF NOT EXISTS `sms_sid` (
    `business_id` INT NOT NULL COMMENT 'ID of the business associated with the SMS',
    `customer_id` INT NOT NULL COMMENT 'ID of the customer associated with the SMS',
    `sms_sid` VARCHAR(64) NOT NULL COMMENT 'Unique identifier for the SMS from the provider',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When the SMS record was created',
    PRIMARY KEY (`business_id`, `customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Tracks SMS message IDs for business-customer communications';

CREATE TABLE twilio_transaction_log (
    transaction_id       INT AUTO_INCREMENT PRIMARY KEY,
    endpoint             VARCHAR(255) NOT NULL,
    payload              JSON NOT NULL,
    response             JSON,
    success              BOOLEAN NOT NULL,
    error_message        TEXT,
    http_status_code     INT,
    created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
);

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
);
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create premium_numbers table for storing premium phone numbers
CREATE TABLE IF NOT EXISTS `premium_numbers` (
  `_id` INT AUTO_INCREMENT PRIMARY KEY,
  `phone_number` VARCHAR(20) NOT NULL COMMENT 'The premium phone number',
  `phone_sid` VARCHAR(100) COMMENT 'The SID from the telephony provider',
  `price` DECIMAL(10, 2) NOT NULL COMMENT 'Price of the premium number',
  `taken` BOOLEAN DEFAULT FALSE COMMENT 'Whether the number is currently in use',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_phone_number` (`phone_number`),
  INDEX `idx_taken` (`taken`),
  INDEX `idx_phone_sid` (`phone_sid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Stores premium phone numbers available for purchase';

-- Add index for faster lookups on phone number
CREATE INDEX `idx_phone_number` ON `premium_numbers` (`phone_number`);