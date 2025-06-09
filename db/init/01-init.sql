-- Create database and user
CREATE DATABASE IF NOT EXISTS appointment_db;
CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON appointment_db.* TO 'app_user'@'%';
FLUSH PRIVILEGES;

USE appointment_db;

-- Business table
CREATE TABLE IF NOT EXISTS business (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Business Phone Numbers
CREATE TABLE IF NOT EXISTS business_phone (
    id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_phone (phone_number),
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Customer table
CREATE TABLE IF NOT EXISTS customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_phone (phone_number)
) ENGINE=InnoDB;

-- Business Customer (junction table)
CREATE TABLE IF NOT EXISTS business_customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    customer_id INT NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_customer (business_id, customer_id),
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Service table
CREATE TABLE IF NOT EXISTS service (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Business Hours
CREATE TABLE IF NOT EXISTS business_hours (
    id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    day_of_week TINYINT NOT NULL, -- 0=Monday, 6=Sunday
    open_time TIME,
    close_time TIME,
    is_closed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_business_day (business_id, day_of_week),
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Appointment table
CREATE TABLE IF NOT EXISTS appointment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    business_customer_id INT NOT NULL,
    service_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled', -- scheduled, confirmed, completed, cancelled, no_show
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES business(id) ON DELETE CASCADE,
    FOREIGN KEY (business_customer_id) REFERENCES business_customer(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES service(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Add indexes for performance
CREATE INDEX idx_appointment_business ON appointment(business_id, start_time, end_time);
CREATE INDEX idx_appointment_customer ON appointment(business_customer_id);
CREATE INDEX idx_business_phone ON business_phone(phone_number);

-- Insert businesses
INSERT INTO business (name, timezone, status) VALUES 
('Luxe Hair Studio', 'America/New_York', 'active'),
('TechGadgets Inc.', 'America/Los_Angeles', 'active'),
('Wellness Medical Center', 'America/Chicago', 'active');

-- Set business IDs
SET @hair_salon_id = 1;
SET @tech_store_id = 2;
SET @clinic_id = 3;

-- Insert business phone numbers
INSERT INTO business_phone (business_id, phone_number, is_primary) VALUES
(@hair_salon_id, '+12025551234', TRUE),  -- Luxe Hair Studio
(@hair_salon_id, '+12025554321', FALSE),  -- Secondary number
(@tech_store_id, '+18185559876', TRUE),   -- TechGadgets
(@clinic_id, '+17735550123', TRUE);       -- Wellness Medical

-- Insert business hours for all businesses
-- Luxe Hair Studio hours
INSERT INTO business_hours (business_id, day_of_week, open_time, close_time, is_closed) VALUES
-- Monday-Friday: 9AM-7PM
(@hair_salon_id, 0, '09:00:00', '19:00:00', FALSE),  -- Monday
(@hair_salon_id, 1, '09:00:00', '19:00:00', FALSE),  -- Tuesday
(@hair_salon_id, 2, '09:00:00', '19:00:00', FALSE),  -- Wednesday
(@hair_salon_id, 3, '09:00:00', '19:00:00', FALSE),  -- Thursday
(@hair_salon_id, 4, '09:00:00', '19:00:00', FALSE),  -- Friday
-- Saturday: 9AM-5PM, Sunday: Closed
(@hair_salon_id, 5, '09:00:00', '17:00:00', FALSE),  -- Saturday
(@hair_salon_id, 6, NULL, NULL, TRUE),               -- Sunday

-- TechGadgets Inc. hours (Mon-Sat: 10AM-8PM, Sun: 11AM-6PM)
(@tech_store_id, 0, '10:00:00', '20:00:00', FALSE),
(@tech_store_id, 1, '10:00:00', '20:00:00', FALSE),
(@tech_store_id, 2, '10:00:00', '20:00:00', FALSE),
(@tech_store_id, 3, '10:00:00', '20:00:00', FALSE),
(@tech_store_id, 4, '10:00:00', '20:00:00', FALSE),
(@tech_store_id, 5, '10:00:00', '20:00:00', FALSE),
(@tech_store_id, 6, '11:00:00', '18:00:00', FALSE),

-- Wellness Medical Center hours (Weekdays: 8AM-6PM, Sat: 9AM-1PM, Sun: Closed)
(@clinic_id, 0, '08:00:00', '18:00:00', FALSE),
(@clinic_id, 1, '08:00:00', '18:00:00', FALSE),
(@clinic_id, 2, '08:00:00', '18:00:00', FALSE),
(@clinic_id, 3, '08:00:00', '18:00:00', FALSE),
(@clinic_id, 4, '08:00:00', '18:00:00', FALSE),
(@clinic_id, 5, '09:00:00', '13:00:00', FALSE),
(@clinic_id, 6, NULL, NULL, TRUE);

-- Insert services for each business
-- Hair Salon Services
INSERT INTO service (business_id, name, description, duration_minutes, price, buffer_before_minutes, buffer_after_minutes, is_active) VALUES
-- Hair Salon Services
(@hair_salon_id, 'Classic Haircut', 'Basic haircut with styling', 45, 45.00, 5, 10, TRUE),
(@hair_salon_id, 'Premium Haircut', 'Haircut with wash and blow dry', 60, 65.00, 5, 15, TRUE),
(@hair_salon_id, 'Full Color', 'Complete hair coloring service', 120, 120.00, 10, 20, TRUE),
(@hair_salon_id, 'Highlights', 'Partial or full highlights', 150, 150.00, 10, 20, TRUE),
(@hair_salon_id, 'Keratin Treatment', 'Smoothing keratin treatment', 180, 250.00, 15, 30, TRUE),
(@hair_salon_id, 'Beard Trim', 'Beard shaping and trimming', 30, 25.00, 5, 5, TRUE),

-- Tech Store Services
(@tech_store_id, 'Phone Screen Replacement', 'Replace broken phone screen', 60, 129.99, 10, 10, TRUE),
(@tech_store_id, 'Virus Removal', 'Remove viruses and malware', 120, 99.99, 10, 10, TRUE),
(@tech_store_id, 'Data Recovery', 'Recover lost files', 180, 199.99, 15, 15, TRUE),
(@tech_store_id, 'Laptop Tune-up', 'Performance optimization', 90, 79.99, 10, 10, TRUE),

-- Medical Services
(@clinic_id, 'General Check-up', 'Routine health examination', 30, 150.00, 5, 10, TRUE),
(@clinic_id, 'Vaccination', 'Standard vaccination', 20, 75.00, 5, 5, TRUE),
(@clinic_id, 'Dental Cleaning', 'Teeth cleaning and check-up', 45, 120.00, 5, 10, TRUE),
(@clinic_id, 'Eye Exam', 'Comprehensive eye examination', 60, 95.00, 5, 10, TRUE);

-- Insert sample customers
INSERT INTO customer (phone_number, first_name, last_name, email) VALUES
('+14155551234', 'John', 'Smith', 'john.smith@example.com'),
('+14155552345', 'Sarah', 'Johnson', 'sarah.j@example.com'),
('+14155553456', 'Michael', 'Brown', 'michael.b@example.com'),
('+14155554567', 'Emily', 'Davis', 'emily.d@example.com'),
('+14155555678', 'David', 'Wilson', 'david.w@example.com');

-- Set customer IDs
SET @customer1_id = 1;
SET @customer2_id = 2;
SET @customer3_id = 3;
SET @customer4_id = 4;
SET @customer5_id = 5;

-- Link customers to businesses (business_customer table)
-- John Smith uses all three businesses
INSERT INTO business_customer (business_id, customer_id, phone_number, first_name, last_name, email) VALUES
(@hair_salon_id, @customer1_id, '+14155551234', 'John', 'Smith', 'john.smith@example.com'),
(@tech_store_id, @customer1_id, '+14155551234', 'John', 'Smith', 'john.smith@example.com'),
(@clinic_id, @customer1_id, '+14155551234', 'John', 'Smith', 'john.smith@example.com'),

-- Sarah Johnson uses hair salon and clinic
(@hair_salon_id, @customer2_id, '+14155552345', 'Sarah', 'Johnson', 'sarah.j@example.com'),
(@clinic_id, @customer2_id, '+14155552345', 'Sarah', 'Johnson', 'sarah.j@example.com'),

-- Michael Brown uses tech store and clinic
(@tech_store_id, @customer3_id, '+14155553456', 'Michael', 'Brown', 'michael.b@example.com'),
(@clinic_id, @customer3_id, '+14155553456', 'Michael', 'Brown', 'michael.b@example.com'),

-- Emily Davis uses hair salon and tech store
(@hair_salon_id, @customer4_id, '+14155554567', 'Emily', 'Davis', 'emily.d@example.com'),
(@tech_store_id, @customer4_id, '+14155554567', 'Emily', 'Davis', 'emily.d@example.com'),

-- David Wilson uses all three businesses
(@hair_salon_id, @customer5_id, '+14155555678', 'David', 'Wilson', 'david.w@example.com'),
(@tech_store_id, @customer5_id, '+14155555678', 'David', 'Wilson', 'david.w@example.com'),
(@clinic_id, @customer5_id, '+14155555678', 'David', 'Wilson', 'david.w@example.com');

-- Insert sample appointments (for the next 7 days)
-- Function to generate random status
DELIMITER //
CREATE FUNCTION random_status() RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    DECLARE statuses VARCHAR(100) DEFAULT 'scheduled,confirmed,completed,cancelled,no_show';
    DECLARE pos INT;
    DECLARE result VARCHAR(20);
    
    SET pos = 1 + FLOOR(RAND() * 5);
    SET result = SUBSTRING_INDEX(SUBSTRING_INDEX(statuses, ',', pos), ',', -1);
    RETURN result;
END //
DELIMITER ;

-- Insert appointments for the hair salon
INSERT INTO appointment (business_id, business_customer_id, service_id, start_time, end_time, status, notes)
SELECT 
    @hair_salon_id,
    bc.id,
    s.id,
    DATE_ADD(CURRENT_DATE, INTERVAL FLOOR(RAND() * 7) DAY) + INTERVAL '09:00:00' HOUR_MINUTE + INTERVAL (FLOOR(RAND() * 9) * 60) MINUTE,
    DATE_ADD(CURRENT_DATE, INTERVAL FLOOR(RAND() * 7) DAY) + INTERVAL '09:00:00' HOUR_MINUTE + INTERVAL ((FLOOR(RAND() * 9) + 1) * 60) MINUTE,
    random_status(),
    CASE WHEN RAND() > 0.7 THEN 'Special instructions or notes' ELSE NULL END
FROM 
    business_customer bc
    JOIN service s ON s.business_id = @hair_salon_id
WHERE 
    bc.business_id = @hair_salon_id
LIMIT 15;

-- Insert appointments for the tech store
INSERT INTO appointment (business_id, business_customer_id, service_id, start_time, end_time, status, notes)
SELECT 
    @tech_store_id,
    bc.id,
    s.id,
    DATE_ADD(CURRENT_DATE, INTERVAL FLOOR(RAND() * 7) DAY) + INTERVAL '10:00:00' HOUR_MINUTE + INTERVAL (FLOOR(RAND() * 10) * 60) MINUTE,
    DATE_ADD(CURRENT_DATE, INTERVAL FLOOR(RAND() * 7) DAY) + INTERVAL '10:00:00' HOUR_MINUTE + INTERVAL ((FLOOR(RAND() * 10) + 1) * 60) MINUTE,
    random_status(),
    CASE WHEN RAND() > 0.7 THEN 'Device details or special requests' ELSE NULL END
FROM 
    business_customer bc
    JOIN service s ON s.business_id = @tech_store_id
WHERE 
    bc.business_id = @tech_store_id
LIMIT 10;

-- Insert appointments for the clinic
INSERT INTO appointment (business_id, business_customer_id, service_id, start_time, end_time, status, notes)
SELECT 
    @clinic_id,
    bc.id,
    s.id,
    DATE_ADD(CURRENT_DATE, INTERVAL FLOOR(RAND() * 7) DAY) + INTERVAL '08:00:00' HOUR_MINUTE + INTERVAL (FLOOR(RAND() * 10) * 60) MINUTE,
    DATE_ADD(CURRENT_DATE, INTERVAL FLOOR(RAND() * 7) DAY) + INTERVAL '08:00:00' HOUR_MINUTE + INTERVAL ((FLOOR(RAND() * 10) + 1) * 60) MINUTE,
    random_status(),
    CASE WHEN RAND() > 0.7 THEN 'Medical notes or special requirements' ELSE NULL END
FROM 
    business_customer bc
    JOIN service s ON s.business_id = @clinic_id
WHERE 
    bc.business_id = @clinic_id
LIMIT 12;

-- Drop the temporary function
DROP FUNCTION IF EXISTS random_status;
