-- Initial data for Windsurf Appointment System

-- Make sure we're using the correct database
USE appointment_db;

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

-- Insert business messages
INSERT INTO business_messages (business_id, type, message, is_active) VALUES
-- Greetings
(@hair_salon_id, 'greeting', 'Welcome to Luxe Hair Studio - Where Style Meets Elegance', TRUE),
(@tech_store_id, 'greeting', 'Welcome to TechGadgets - Your One-Stop Tech Solution', TRUE),
(@clinic_id, 'greeting', 'Welcome to Wellness Medical Center - Your Health is Our Priority', TRUE),
(@ideationmax_id, 'greeting', 'Welcome to IdeationMax. The leading AI Agents development firm', TRUE),
(@codecraft_id, 'greeting', 'Welcome to CodeCraft Solutions - Building the Future with Clean Code', TRUE),
(@digital_innovators_id, 'greeting', 'Welcome to Digital Innovators - Transforming Ideas into Reality', TRUE),
-- Add some additional message types
(@hair_salon_id, 'confirmation', 'Your appointment at Luxe Hair Studio has been confirmed!', TRUE),
(@hair_salon_id, 'reminder', 'Reminder: Your appointment at Luxe Hair Studio is tomorrow at {time}', TRUE),
(@clinic_id, 'confirmation', 'Your appointment at Wellness Medical Center has been confirmed', TRUE),
(@clinic_id, 'reminder', 'Friendly reminder: Your appointment is in 24 hours', TRUE);

-- Insert business phone numbers
INSERT INTO business_phone (business_id, business_phone, is_primary) VALUES
(@hair_salon_id, '+16473605789', TRUE),  -- Luxe Hair Studio
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
(@tech_store_id, 'Virus Removal', 'Complete virus and malware removal', 120, 99.99, 10, 10, TRUE),
(@tech_store_id, 'Data Recovery', 'Recover lost files', 180, 199.99, 15, 15, TRUE),
(@tech_store_id, 'Laptop Tune-up', 'Performance optimization', 90, 79.99, 10, 10, TRUE),

-- Medical Services
(@clinic_id, 'General Check-up', 'Routine health examination', 30, 150.00, 5, 10, TRUE),
(@clinic_id, 'Vaccination', 'Immunization shots', 15, 75.00, 5, 5, TRUE),
(@clinic_id, 'Allergy Testing', 'Comprehensive allergy testing', 60, 299.00, 15, 15, TRUE),
(@clinic_id, 'Dermatology Consultation', 'Skin condition evaluation', 45, 149.99, 10, 10, TRUE),
(@clinic_id, 'Blood Work', 'Routine blood tests', 20, 89.99, 5, 5, TRUE);

-- Insert service translations for all services (English)
-- This will create English translations for all existing services
INSERT INTO service_translation (service_id, language_code, name, description)
SELECT 
    service_id, 
    'en' as language_code, 
    name, 
    description
FROM service
WHERE name IS NOT NULL AND description IS NOT NULL;

-- Add Arabic translations for all services
INSERT INTO service_translation (service_id, language_code, name, description) VALUES
-- Hair Salon Services
(1, 'ar', 'قصة شعر نسائية', 'قص وتصفيف الشعر للنساء'),
(2, 'ar', 'قصة شعر رجالية', 'قص وتصفيف الشعر للرجال'),
(3, 'ar', 'صبغة شعر', 'خدمة صبغة شعر كاملة'),
(4, 'ar', 'تصفيف الشعر', 'غسل وتنشيف وتصفيف الشعر'),
(5, 'ar', 'تشذيب اللحية', 'تشكيل وتشذيب اللحية'),

-- Tech Store Services
(6, 'ar', 'إزالة الفيروسات', 'إزالة كاملة للفيروسات والبرمجيات الخبيثة'),
(7, 'ar', 'استعادة البيانات', 'استعادة الملفات المفقودة'),
(8, 'ar', 'صيانة الحاسوب المحمول', 'تحسين أداء الحاسوب'),

-- Medical Services
(9, 'ar', 'فحص عام', 'فحص صحي روتيني'),
(10, 'ar', 'تطعيم', 'حقن التطعيمات'),
(11, 'ar', 'فحص الحساسية', 'فحص شامل للحساسية'),
(12, 'ar', 'استشارة جلدية', 'تقييم حالة الجلد'),
(13, 'ar', 'تحاليل دم', 'تحاليل دم روتينية');

-- Insert sample customers
INSERT INTO customer (business_id, customer_phone, first_name, last_name, email, is_active) VALUES
-- Hair Salon Customers
(@hair_salon_id, '+12025551001', 'John', 'Smith', 'john.smith@example.com', TRUE),
(@hair_salon_id, '+12025551002', 'Sarah', 'Johnson', 'sarah.j@example.com', TRUE),
(@hair_salon_id, '+12025551003', 'Michael', 'Brown', 'michael.b@example.com', TRUE),

-- Tech Store Customers
(@tech_store_id, '+18185551001', 'David', 'Wilson', 'david.w@example.com', TRUE),
(@tech_store_id, '+18185551002', 'Emily', 'Davis', 'emily.d@example.com', TRUE),

-- Medical Center Patients
(@clinic_id, '+17735551001', 'Robert', 'Taylor', 'robert.t@example.com', TRUE),
(@clinic_id, '+17735551002', 'Jennifer', 'Anderson', 'jennifer.a@example.com', TRUE);

-- Insert sample appointments (for the next 7 days)
SET @now = NOW();
SET @tomorrow = DATE_ADD(@now, INTERVAL 1 DAY);
SET @in_two_days = DATE_ADD(@now, INTERVAL 2 DAY);
SET @in_three_days = DATE_ADD(@now, INTERVAL 3 DAY);

-- Hair Salon Appointments
-- Get service IDs
SET @womens_haircut = (SELECT service_id FROM service WHERE name = 'Women\'s Haircut' AND business_id = @hair_salon_id);
SET @mens_haircut = (SELECT service_id FROM service WHERE name = 'Men\'s Haircut' AND business_id = @hair_salon_id);
SET @hair_coloring = (SELECT service_id FROM service WHERE name = 'Hair Coloring' AND business_id = @hair_salon_id);

-- Get customer IDs
SET @john_smith = (SELECT customer_id FROM customer WHERE customer_phone = '+12025551001' AND business_id = @hair_salon_id);
SET @sarah_johnson = (SELECT customer_id FROM customer WHERE customer_phone = '+12025551002' AND business_id = @hair_salon_id);

-- Insert appointments
INSERT INTO appointment (business_id, customer_id, service_id, start_time, end_time, status) VALUES
-- Today's appointments
(@hair_salon_id, @john_smith, @mens_haircut, 
    CONCAT(DATE(@now), ' 10:00:00'), 
    CONCAT(DATE(@now), ' 10:30:00'), 
    'scheduled'),
    
(@hair_salon_id, @sarah_johnson, @womens_haircut, 
    CONCAT(DATE(@now), ' 11:00:00'), 
    CONCAT(DATE(@now), ' 12:30:00'), 
    'scheduled'),
    
-- Tomorrow's appointments
(@hair_salon_id, @john_smith, @hair_coloring, 
    CONCAT(DATE(@tomorrow), ' 14:00:00'), 
    CONCAT(DATE(@tomorrow), ' 17:00:00'), 
    'confirmed');
