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

-- Business Greetings
CREATE TABLE IF NOT EXISTS business_greetings (
    business_greeting_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    greeting_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES business(business_id) ON DELETE CASCADE
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

-- Add indexes for performance
CREATE INDEX idx_appointment_business ON appointment(business_id, start_time, end_time);
CREATE INDEX idx_appointment_customer ON appointment(customer_id);
CREATE INDEX idx_business_phone ON business_phone(business_phone);
CREATE INDEX idx_customer_business ON customer(business_id, customer_phone);

-- Insert businesses
INSERT INTO business (name, timezone, status) VALUES 
('Luxe Hair Studio', 'America/New_York', 'active'),
('TechGadgets Inc.', 'America/Los_Angeles', 'active'),
('Wellness Medical Center', 'America/Chicago', 'active'),
('IdeationMax', 'America/New_York', 'active'),
('CodeCraft Solutions', 'America/Chicago', 'active'),
('Digital Innovators', 'America/Los_Angeles', 'active');

-- Set business IDs for reference
SET @hair_salon_id = 1;
SET @tech_store_id = 2;
SET @clinic_id = 3;
SET @ideationmax_id = 4;
SET @codecraft_id = 5;
SET @digital_innovators_id = 6;

-- Insert business greetings
INSERT INTO business_greetings (business_id, greeting_text, is_active) VALUES
(@hair_salon_id, 'Welcome to Luxe Hair Studio - Where Style Meets Elegance', TRUE),
(@tech_store_id, 'Welcome to TechGadgets - Your One-Stop Tech Solution', TRUE),
(@clinic_id, 'Welcome to Wellness Medical Center - Your Health is Our Priority', TRUE),
(@ideationmax_id, 'Welcome to IdeationMax. The leading AI Agents development firm', TRUE),
(@codecraft_id, 'Welcome to CodeCraft Solutions - Building the Future with Clean Code', TRUE),
(@digital_innovators_id, 'Welcome to Digital Innovators - Transforming Ideas into Reality', TRUE);

-- Insert business phone numbers
INSERT INTO business_phone (business_id, business_phone, is_primary) VALUES
(@hair_salon_id, '+12025551234', TRUE),  -- Luxe Hair Studio
(@hair_salon_id, '+12025554321', FALSE),  -- Secondary number
(@tech_store_id, '+18185559876', TRUE),   -- TechGadgets
(@clinic_id, '+17735550123', TRUE),       -- Wellness Medical
(@ideationmax_id, '+12025551034', TRUE),  -- IdeationMax
(@codecraft_id, '+13125556789', TRUE),    -- CodeCraft Solutions
(@digital_innovators_id, '+19185554321', TRUE); -- Digital Innovators

-- Insert business hours for all businesses
-- Luxe Hair Salon hours
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
(@clinic_id, 6, NULL, NULL, TRUE),

-- IdeationMax hours (Weekdays: 9AM-6PM, Weekends: Closed)
(@ideationmax_id, 0, '09:00:00', '18:00:00', FALSE),
(@ideationmax_id, 1, '09:00:00', '18:00:00', FALSE),
(@ideationmax_id, 2, '09:00:00', '18:00:00', FALSE),
(@ideationmax_id, 3, '09:00:00', '18:00:00', FALSE),
(@ideationmax_id, 4, '09:00:00', '18:00:00', FALSE),
(@ideationmax_id, 5, NULL, NULL, TRUE),
(@ideationmax_id, 6, NULL, NULL, TRUE),

-- CodeCraft Solutions hours (Weekdays: 10AM-7PM, Sat: 10AM-4PM, Sun: Closed)
(@codecraft_id, 0, '10:00:00', '19:00:00', FALSE),
(@codecraft_id, 1, '10:00:00', '19:00:00', FALSE),
(@codecraft_id, 2, '10:00:00', '19:00:00', FALSE),
(@codecraft_id, 3, '10:00:00', '19:00:00', FALSE),
(@codecraft_id, 4, '10:00:00', '19:00:00', FALSE),
(@codecraft_id, 5, '10:00:00', '16:00:00', FALSE),
(@codecraft_id, 6, NULL, NULL, TRUE);

-- Insert services for businesses
-- Hair Salon Services
INSERT INTO service (business_id, name, description, duration_minutes, price, buffer_before_minutes, buffer_after_minutes, is_active) VALUES
(@hair_salon_id, 'Women\'s Haircut', 'Haircut and style for women', 90, 75.00, 10, 10, TRUE),
(@hair_salon_id, 'Men\'s Haircut', 'Haircut and style for men', 30, 40.00, 5, 5, TRUE),
(@hair_salon_id, 'Hair Coloring', 'Full hair coloring service', 180, 150.00, 15, 15, TRUE),
(@hair_salon_id, 'Blowout', 'Wash and blow dry', 45, 50.00, 5, 5, TRUE),
(@hair_salon_id, 'Beard Trim', 'Beard shaping and trimming', 30, 25.00, 5, 5, TRUE),

-- Tech Store Services
(@tech_store_id, 'Phone Screen Replacement', 'Replace broken phone screen', 60, 129.99, 10, 10, TRUE),
(@tech_store_id, 'Virus Removal', 'Remove viruses and malware', 120, 99.99, 10, 10, TRUE),
(@tech_store_id, 'Data Recovery', 'Recover lost or deleted files', 240, 199.99, 15, 15, TRUE),
(@tech_store_id, 'Laptop Tune-up', 'Clean and optimize laptop performance', 90, 79.99, 10, 10, TRUE),
(@tech_store_id, 'Device Setup', 'Set up new devices and transfer data', 60, 49.99, 5, 5, TRUE),

-- Medical Center Services
(@clinic_id, 'Annual Physical', 'Comprehensive physical examination', 30, 199.00, 10, 10, TRUE),
(@clinic_id, 'Vaccination', 'Routine immunization', 15, 49.99, 5, 5, TRUE),
(@clinic_id, 'Allergy Testing', 'Comprehensive allergy testing', 60, 299.00, 15, 15, TRUE),
(@clinic_id, 'Dermatology Consultation', 'Skin condition evaluation', 45, 149.99, 10, 10, TRUE),
(@clinic_id, 'Blood Work', 'Routine blood tests', 20, 89.99, 5, 5, TRUE);

-- Insert sample customers
-- For Luxe Hair Salon
INSERT INTO customer (business_id, first_name, last_name, email, customer_phone, notes) VALUES
(@hair_salon_id, 'Sarah', 'Johnson', 'sarah.j@example.com', '+12025551234', 'Prefers corner chair'),
(@hair_salon_id, 'Michael', 'Chen', 'michael.c@example.com', '+12025551235', 'Allergic to almonds'),
(@hair_salon_id, 'Emily', 'Rodriguez', 'emily.r@example.com', '+12025551236', 'VIP customer');

-- For TechGadgets
INSERT INTO customer (business_id, first_name, last_name, email, customer_phone, notes) VALUES
(@tech_store_id, 'David', 'Kim', 'david.k@example.com', '+18185551234', 'Frequent buyer'),
(@tech_store_id, 'Jennifer', 'Martinez', 'jennifer.m@example.com', '+18185551235', 'Interested in new releases');

-- For Wellness Medical Center
INSERT INTO customer (business_id, first_name, last_name, email, customer_phone, notes) VALUES
(@clinic_id, 'Robert', 'Wilson', 'robert.w@example.com', '+17735551234', 'Annual checkup'),
(@clinic_id, 'Lisa', 'Anderson', 'lisa.a@example.com', '+17735551235', 'Allergy shots');

-- Set customer IDs for appointments
SET @sarah_id = (SELECT id FROM customer WHERE customer_phone = '+12025551234' LIMIT 1);
SET @michael_id = (SELECT id FROM customer WHERE customer_phone = '+12025551235' LIMIT 1);
SET @emily_id = (SELECT id FROM customer WHERE customer_phone = '+12025551236' LIMIT 1);
SET @david_id = (SELECT id FROM customer WHERE customer_phone = '+18185551234' LIMIT 1);
SET @jennifer_id = (SELECT id FROM customer WHERE customer_phone = '+18185551235' LIMIT 1);
SET @robert_id = (SELECT id FROM customer WHERE customer_phone = '+17735551234' LIMIT 1);
SET @lisa_id = (SELECT id FROM customer WHERE customer_phone = '+17735551235' LIMIT 1);

-- Insert sample appointments
-- For Luxe Hair Salon
INSERT INTO appointment (business_id, customer_id, service_id, start_time, end_time, status, notes) VALUES
(@hair_salon_id, @sarah_id, 1, DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL '10:00' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL '11:30' HOUR_MINUTE, 'scheduled', 'Highlights and cut'),
(@hair_salon_id, @michael_id, 2, DATE_ADD(NOW(), INTERVAL 2 DAY) + INTERVAL '14:00' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 2 DAY) + INTERVAL '14:30' HOUR_MINUTE, 'scheduled', 'Regular trim'),
(@hair_salon_id, @emily_id, 3, DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL '15:00' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL '16:00' HOUR_MINUTE, 'confirmed', 'Balayage');

-- For TechGadgets
INSERT INTO appointment (business_id, customer_id, service_id, start_time, end_time, status, notes) VALUES
(@tech_store_id, @david_id, 4, DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL '11:00' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL '12:00' HOUR_MINUTE, 'scheduled', 'iPhone 14 screen replacement'),
(@tech_store_id, @jennifer_id, 5, DATE_ADD(NOW(), INTERVAL 3 DAY) + INTERVAL '13:00' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 3 DAY) + INTERVAL '15:00' HOUR_MINUTE, 'scheduled', 'Laptop virus removal');

-- For Wellness Medical Center
INSERT INTO appointment (business_id, customer_id, service_id, start_time, end_time, status, notes) VALUES
(@clinic_id, @robert_id, 6, DATE_ADD(NOW(), INTERVAL 2 DAY) + INTERVAL '09:00' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 2 DAY) + INTERVAL '09:30' HOUR_MINUTE, 'scheduled', 'Annual physical'),
(@clinic_id, @lisa_id, 7, DATE_ADD(NOW(), INTERVAL 1 WEEK) + INTERVAL '10:30' HOUR_MINUTE, 
  DATE_ADD(NOW(), INTERVAL 1 WEEK) + INTERVAL '11:00' HOUR_MINUTE, 'scheduled', 'Allergy shot');

-- Business hours are already inserted above

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
(@clinic_id, 'Eye Exam', 'Comprehensive eye examination', 60, 95.00, 5, 10, TRUE),
(@clinic_id, 'Physical Therapy', 'Therapy session with specialist', 60, 120.00, 10, 15, TRUE),
(@clinic_id, 'Allergy Testing', 'Comprehensive allergy screening', 90, 250.00, 15, 15, TRUE),
(@clinic_id, 'Nutrition Counseling', 'Personalized diet planning', 60, 110.00, 10, 10, TRUE),

-- IdeationMax Services
(@ideationmax_id, 'AI Consultation', 'Initial consultation for AI solutions', 60, 199.00, 15, 15, TRUE),
(@ideationmax_id, 'Custom AI Agent Development', 'Development of custom AI agent solutions', 240, 999.00, 30, 30, TRUE),
(@ideationmax_id, 'AI Integration Service', 'Integration of AI into existing systems', 180, 750.00, 20, 20, TRUE),
(@ideationmax_id, 'Machine Learning Model Training', 'Custom ML model development', 300, 1499.00, 30, 30, TRUE),

-- CodeCraft Solutions Services
(@codecraft_id, 'Code Review', 'In-depth code review and optimization', 90, 299.00, 15, 15, TRUE),
(@codecraft_id, 'System Architecture', 'Design and planning of system architecture', 120, 499.00, 20, 20, TRUE),
(@codecraft_id, 'API Development', 'Custom RESTful API development', 180, 899.00, 30, 30, TRUE),
(@codecraft_id, 'DevOps Implementation', 'CI/CD pipeline setup', 240, 1499.00, 30, 30, TRUE),

-- Digital Innovators Services
(@digital_innovators_id, 'Digital Strategy Session', '1-hour strategy consultation', 60, 249.00, 15, 15, TRUE),
(@digital_innovators_id, 'MVP Development', 'Minimum Viable Product development', 300, 2999.00, 60, 60, TRUE),
(@digital_innovators_id, 'UI/UX Design', 'User interface and experience design', 120, 599.00, 20, 20, TRUE);

-- Customer data is already inserted above
