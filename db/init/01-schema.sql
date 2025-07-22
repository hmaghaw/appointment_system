-- Database schema for Windsurf Appointment System

-- Create database
CREATE DATABASE IF NOT EXISTS appointment_db;

USE appointment_db;

-- Business table
CREATE TABLE IF NOT EXISTS business (
    business_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

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

-- Business Phone Numbers
CREATE TABLE IF NOT EXISTS business_phone (
    business_phone_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    business_phone VARCHAR(20) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_phone (business_phone),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Customer table
CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_customer_phone (business_id, customer_phone),
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores translations for service names and descriptions';
