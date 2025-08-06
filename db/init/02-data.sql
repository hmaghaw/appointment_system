-- Initial data for Windsurf Appointment System

-- Make sure we're using the correct database
USE appointment_db;

-- First, insert subscription plans since other tables reference them
-- Insert Voxxell Free plan (ID: 7)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Free',
    'Best for testing the platform — manage customers and calendar without making calls or using voice AI.',
    'monthly',
    0.00,
    0.00,
    0.00,
    TRUE,
    0
);

-- Insert Voxxell Free yearly plan (ID: 8)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Free',
    'Best for testing the platform — manage customers and calendar without making calls or using voice AI.',
    'yearly',
    0.00,
    0.00,
    0.00,
    TRUE,
    0
);

-- Insert Voxxell Starter monthly plan (ID: 1)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Starter',
    'Perfect for small Canadian businesses getting started with voice AI',
    'monthly',
    99.00,
    99.00,
    24901.00,
    TRUE,
    1
);

-- Insert Voxxell Starter yearly plan (ID: 2)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    annual_savings,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Starter',
    'Perfect for small Canadian businesses getting started with voice AI',
    'yearly',
    99.00,
    79.00,
    240.00,
    24921.00,
    TRUE,
    2
);

-- Insert Voxxell Professional monthly plan (ID: 3)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Professional',
    'Ideal for growing SMBs needing advanced voice AI capabilities',
    'monthly',
    249.00,
    249.00,
    24751.00,
    TRUE,
    3
);

-- Insert Voxxell Professional yearly plan (ID: 4)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    annual_savings,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Professional',
    'Ideal for growing SMBs needing advanced voice AI capabilities',
    'yearly',
    249.00,
    199.00,
    600.00,
    24801.00,
    TRUE,
    4
);

-- Insert Voxxell Enterprise monthly plan (ID: 5)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Enterprise',
    'Comprehensive solution for established businesses with high call volumes',
    'monthly',
    599.00,
    599.00,
    24401.00,
    TRUE,
    5
);

-- Insert Voxxell Enterprise yearly plan (ID: 6)
INSERT INTO subscription_plan (
    plan_name,
    plan_description,
    billing_cycle,
    original_price,
    final_price,
    annual_savings,
    estimated_monthly_roi,
    is_active,
    display_order
) VALUES (
    'Voxxell Enterprise',
    'Comprehensive solution for established businesses with high call volumes',
    'yearly',
    599.00,
    479.00,
    1440.00,
    24521.00,
    TRUE,
    6
);

-- Insert subscription plan features
INSERT INTO subscription_plan_feature (subscription_plan_id, feature_name, feature_value, display_order) VALUES
-- Voxxell Free (ID: 7)
(7, 'Call Limit', 'No calls allowed', 1),
(7, 'Voice AI Integrations', 'Not included', 2),
(7, 'Analytics', 'Not included', 3),
(7, 'Support', 'Community forum only', 4),
(7, 'Calendar Access', 'Basic calendar management', 5),
(7, 'Customer Management', 'Unlimited customers', 6),

-- Voxxell Free Yearly (ID: 8)
(8, 'Call Limit', 'No calls allowed', 1),
(8, 'Voice AI Integrations', 'Not included', 2),
(8, 'Analytics', 'Not included', 3),
(8, 'Support', 'Community forum only', 4),
(8, 'Calendar Access', 'Basic calendar management', 5),
(8, 'Customer Management', 'Unlimited customers', 6),

-- Voxxell Starter (ID: 1)
(1, 'Call Limit', 'Up to 500 calls/month', 1),
(1, 'Voice AI Integrations', 'Basic voice AI integrations', 2),
(1, 'Support', 'Business hours support (EST)', 3),
(1, 'Language Support', 'Canadian English & French', 4),
(1, 'Analytics Dashboard', 'Basic analytics dashboard', 5),

-- Voxxell Starter Yearly (ID: 2)
(2, 'Call Limit', 'Up to 500 calls/month', 1),
(2, 'Voice AI Integrations', 'Basic voice AI integrations', 2),
(2, 'Support', 'Business hours support (EST)', 3),
(2, 'Language Support', 'Canadian English & French', 4),
(2, 'Analytics Dashboard', 'Basic analytics dashboard', 5),

-- Voxxell Professional (ID: 3)
(3, 'Call Limit', 'Up to 2,000 calls/month', 1),
(3, 'Voice AI Integrations', 'Advanced voice AI integrations', 2),
(3, 'Support', 'Priority support (extended hours)', 3),
(3, 'Analytics & Reporting', 'Advanced analytics & reporting', 4),
(3, 'Support Channels', 'Email & chat support', 5),
(3, 'Includes', 'Everything in Starter', 6),

-- Voxxell Professional Yearly (ID: 4)
(4, 'Includes', 'Everything in Starter', 1),
(4, 'Call Limit', 'Up to 2,000 calls/month', 2),
(4, 'Voice AI Integrations', 'Advanced voice AI integrations', 3),
(4, 'Support', 'Priority support (extended hours)', 4),
(4, 'Analytics & Reporting', 'Advanced analytics & reporting', 5),
(4, 'Support Channels', 'Email & chat support', 6),

-- Voxxell Enterprise (ID: 5)
(5, 'Includes', 'Everything in Professional', 1),
(5, 'Call Limit', 'Unlimited calls', 2),
(5, 'Voice AI Integrations', 'Custom voice AI integrations', 3),
(5, 'Account Management', 'Dedicated account manager', 4),
(5, 'Analytics & Reporting', 'Custom analytics & white-label reporting', 5),
(5, 'Support', '24/7 dedicated support hotline', 6),
(5, 'Security & Compliance', 'Enterprise-grade security & compliance', 7),

-- Voxxell Enterprise Yearly (ID: 6)
(6, 'Includes', 'Everything in Professional', 1),
(6, 'Call Limit', 'Unlimited calls', 2),
(6, 'Voice AI Integrations', 'Custom voice AI integrations', 3),
(6, 'Account Management', 'Dedicated account manager', 4),
(6, 'Analytics & Reporting', 'Custom analytics & white-label reporting', 5),
(6, 'Support', '24/7 dedicated support hotline', 6),
(6, 'Security & Compliance', 'Enterprise-grade security & compliance', 7);

-- Now insert businesses with proper subscription_plan_id (default is 7 for Voxxell Free)
INSERT INTO business (name, timezone, status, subscription_plan_id) VALUES
('Luxe Hair Studio', 'America/New_York', 'active', 1),
('TechGadgets Inc.', 'America/Los_Angeles', 'active', 1),
('Wellness Medical Center', 'America/Chicago', 'active', 3),
('IdeationMax', 'America/New_York', 'active', 5),
('CodeCraft Solutions', 'America/Chicago', 'active', 5),
('Digital Innovators', 'America/Los_Angeles', 'active', 5);

-- Rest of the original data follows...
-- [Previous content from 02-data.sql after the initial business insert]

-- Set business IDs for reference
SET @hair_salon_id = 1;
SET @tech_store_id = 2;
SET @clinic_id = 3;
SET @ideationmax_id = 4;
SET @codecraft_id = 5;
SET @digital_innovators_id = 6;

-- Continue with the rest of the original 02-data.sql content...
