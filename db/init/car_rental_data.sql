-- ============================
-- CAR RENTAL TEST DATA
-- 3 Branches: Toronto, Mississauga, Brampton
-- Common vehicle classes across all branches
-- Sample vehicles distributed randomly
-- ============================

-- Assume business_id = 1 exists in the business table
SET @business_id = 98;

-- ============================
-- LOCATIONS (3 Branches)
-- ============================
INSERT INTO car_rental_location (business_id, name, address_line1, city, province_state, country, postal_code, phone, latitude, longitude, is_active)
VALUES
  (@business_id, 'Toronto Downtown', '123 King Street West', 'Toronto', 'Ontario', 'Canada', 'M5H 1A1', '416-555-0101', 43.648360, -79.381710, 1),
  (@business_id, 'Mississauga Airport', '6750 Airport Road', 'Mississauga', 'Ontario', 'Canada', 'L4V 1V1', '905-555-0102', 43.677223, -79.630556, 1),
  (@business_id, 'Brampton City Centre', '45 Main Street North', 'Brampton', 'Ontario', 'Canada', 'L6X 1N1', '905-555-0103', 43.731548, -79.762421, 1);

-- Get location IDs
SET @loc_toronto = LAST_INSERT_ID();
SET @loc_mississauga = @loc_toronto + 1;
SET @loc_brampton = @loc_toronto + 2;

-- ============================
-- VEHICLE CLASSES (Common across all branches)
-- ============================
INSERT INTO car_rental_vehicle_class (business_id, class_code, class_name, description, is_active)
VALUES
  (@business_id, 'ECON', 'Economy', 'Compact and fuel-efficient vehicles', 1),
  (@business_id, 'COMP', 'Compact', 'Small cars perfect for city driving', 1),
  (@business_id, 'MID', 'Midsize', 'Comfortable sedans with more space', 1),
  (@business_id, 'FULL', 'Full-Size', 'Large sedans with premium comfort', 1),
  (@business_id, 'SUV', 'SUV', 'Sport utility vehicles for families', 1),
  (@business_id, 'LUX', 'Luxury', 'Premium vehicles with high-end features', 1),
  (@business_id, 'VAN', 'Minivan', 'Multi-passenger vehicles', 1),
  (@business_id, 'TRUCK', 'Pickup Truck', 'Utility trucks for cargo', 1);

-- Get class IDs
SET @class_econ = LAST_INSERT_ID();
SET @class_comp = @class_econ + 1;
SET @class_mid = @class_econ + 2;
SET @class_full = @class_econ + 3;
SET @class_suv = @class_econ + 4;
SET @class_lux = @class_econ + 5;
SET @class_van = @class_econ + 6;
SET @class_truck = @class_econ + 7;

-- ============================
-- VEHICLE MAKES
-- ============================
INSERT INTO car_rental_vehicle_make (make_name)
VALUES
  ('Toyota'),
  ('Honda'),
  ('Ford'),
  ('Chevrolet'),
  ('BMW'),
  ('Mercedes-Benz'),
  ('Nissan'),
  ('Hyundai'),
  ('Dodge'),
  ('Jeep');

-- Get make IDs
SET @make_toyota = LAST_INSERT_ID();
SET @make_honda = @make_toyota + 1;
SET @make_ford = @make_toyota + 2;
SET @make_chevrolet = @make_toyota + 3;
SET @make_bmw = @make_toyota + 4;
SET @make_mercedes = @make_toyota + 5;
SET @make_nissan = @make_toyota + 6;
SET @make_hyundai = @make_toyota + 7;
SET @make_dodge = @make_toyota + 8;
SET @make_jeep = @make_toyota + 9;

-- ============================
-- VEHICLE MODELS
-- ============================
INSERT INTO car_rental_vehicle_model (vehicle_make_id, model_name, body_type)
VALUES
  -- Toyota
  (@make_toyota, 'Corolla', 'Sedan'),
  (@make_toyota, 'Camry', 'Sedan'),
  (@make_toyota, 'RAV4', 'SUV'),
  (@make_toyota, 'Highlander', 'SUV'),
  (@make_toyota, 'Sienna', 'Minivan'),

  -- Honda
  (@make_honda, 'Civic', 'Sedan'),
  (@make_honda, 'Accord', 'Sedan'),
  (@make_honda, 'CR-V', 'SUV'),
  (@make_honda, 'Pilot', 'SUV'),
  (@make_honda, 'Odyssey', 'Minivan'),

  -- Ford
  (@make_ford, 'Focus', 'Sedan'),
  (@make_ford, 'Fusion', 'Sedan'),
  (@make_ford, 'Escape', 'SUV'),
  (@make_ford, 'Explorer', 'SUV'),
  (@make_ford, 'F-150', 'Pickup Truck'),

  -- Chevrolet
  (@make_chevrolet, 'Cruze', 'Sedan'),
  (@make_chevrolet, 'Malibu', 'Sedan'),
  (@make_chevrolet, 'Equinox', 'SUV'),
  (@make_chevrolet, 'Silverado', 'Pickup Truck'),

  -- BMW
  (@make_bmw, '3 Series', 'Sedan'),
  (@make_bmw, '5 Series', 'Sedan'),
  (@make_bmw, 'X5', 'SUV'),

  -- Mercedes-Benz
  (@make_mercedes, 'C-Class', 'Sedan'),
  (@make_mercedes, 'E-Class', 'Sedan'),
  (@make_mercedes, 'GLE', 'SUV'),

  -- Nissan
  (@make_nissan, 'Sentra', 'Sedan'),
  (@make_nissan, 'Altima', 'Sedan'),
  (@make_nissan, 'Rogue', 'SUV'),

  -- Hyundai
  (@make_hyundai, 'Elantra', 'Sedan'),
  (@make_hyundai, 'Sonata', 'Sedan'),
  (@make_hyundai, 'Tucson', 'SUV'),
  (@make_hyundai, 'Santa Fe', 'SUV'),

  -- Dodge
  (@make_dodge, 'Grand Caravan', 'Minivan'),
  (@make_dodge, 'Ram 1500', 'Pickup Truck'),

  -- Jeep
  (@make_jeep, 'Cherokee', 'SUV'),
  (@make_jeep, 'Grand Cherokee', 'SUV');

-- ============================
-- VEHICLES (Distributed across locations)
-- ============================

-- ECONOMY CARS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Toyota Corolla
  (@business_id, '1HGBH41JXMN109186', 'ABC-1234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Corolla' LIMIT 1), @class_econ, 2023, 'White', 5, 4, 'Automatic', 'Gasoline', 200, 1),
  (@business_id, '2HGBH41JXMN109187', 'ABC-1235', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Corolla' LIMIT 1), @class_econ, 2022, 'Silver', 5, 4, 'Automatic', 'Gasoline', 200, 1),
  (@business_id, '3HGBH41JXMN109188', 'ABC-1236', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Corolla' LIMIT 1), @class_econ, 2023, 'Black', 5, 4, 'Manual', 'Gasoline', 200, 1),

  -- Hyundai Elantra
  (@business_id, '4HGBH41JXMN109189', 'DEF-2234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Elantra' LIMIT 1), @class_econ, 2023, 'Blue', 5, 4, 'Automatic', 'Gasoline', 200, 1),
  (@business_id, '5HGBH41JXMN109190', 'DEF-2235', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Elantra' LIMIT 1), @class_econ, 2022, 'Red', 5, 4, 'Automatic', 'Gasoline', 200, 1);

-- COMPACT CARS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Honda Civic
  (@business_id, '6HGBH41JXMN109191', 'GHI-3234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Civic' LIMIT 1), @class_comp, 2023, 'Gray', 5, 4, 'Automatic', 'Gasoline', 200, 1),
  (@business_id, '7HGBH41JXMN109192', 'GHI-3235', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Civic' LIMIT 1), @class_comp, 2022, 'White', 5, 4, 'Automatic', 'Gasoline', 200, 1),
  (@business_id, '8HGBH41JXMN109193', 'GHI-3236', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Civic' LIMIT 1), @class_comp, 2023, 'Blue', 5, 4, 'CVT', 'Gasoline', 200, 1),

  -- Nissan Sentra
  (@business_id, '9HGBH41JXMN109194', 'JKL-4234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Sentra' LIMIT 1), @class_comp, 2022, 'Silver', 5, 4, 'Automatic', 'Gasoline', 200, 1);

-- MIDSIZE CARS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Toyota Camry
  (@business_id, 'AHGBH41JXMN109195', 'MNO-5234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Camry' LIMIT 1), @class_mid, 2023, 'Black', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'BHGBH41JXMN109196', 'MNO-5235', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Camry' LIMIT 1), @class_mid, 2022, 'Silver', 5, 4, 'Automatic', 'Gasoline', 250, 1),

  -- Honda Accord
  (@business_id, 'CHGBH41JXMN109197', 'PQR-6234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Accord' LIMIT 1), @class_mid, 2023, 'White', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'DHGBH41JXMN109198', 'PQR-6235', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Accord' LIMIT 1), @class_mid, 2022, 'Blue', 5, 4, 'CVT', 'Gasoline', 250, 1),

  -- Nissan Altima
  (@business_id, 'EHGBH41JXMN109199', 'STU-7234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Altima' LIMIT 1), @class_mid, 2022, 'Gray', 5, 4, 'Automatic', 'Gasoline', 250, 1);

-- FULL-SIZE CARS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Chevrolet Malibu
  (@business_id, 'FHGBH41JXMN109200', 'VWX-8234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Malibu' LIMIT 1), @class_full, 2023, 'Black', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'GHGBH41JXMN109201', 'VWX-8235', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Malibu' LIMIT 1), @class_full, 2022, 'White', 5, 4, 'Automatic', 'Gasoline', 250, 1),

  -- Ford Fusion
  (@business_id, 'HHGBH41JXMN109202', 'YZA-9234', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Fusion' LIMIT 1), @class_full, 2022, 'Silver', 5, 4, 'Automatic', 'Gasoline', 250, 1);

-- SUVs
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Toyota RAV4
  (@business_id, 'IHGBH41JXMN109203', 'BCD-1134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'RAV4' LIMIT 1), @class_suv, 2023, 'Blue', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'JHGBH41JXMN109204', 'BCD-1135', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'RAV4' LIMIT 1), @class_suv, 2022, 'Black', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'KHGBH41JXMN109205', 'BCD-1136', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'RAV4' LIMIT 1), @class_suv, 2023, 'White', 5, 4, 'AWD-Auto', 'Hybrid', 250, 1),

  -- Honda CR-V
  (@business_id, 'LHGBH41JXMN109206', 'EFG-2134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'CR-V' LIMIT 1), @class_suv, 2023, 'Gray', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'MHGBH41JXMN109207', 'EFG-2135', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'CR-V' LIMIT 1), @class_suv, 2022, 'Red', 5, 4, 'Automatic', 'Gasoline', 250, 1),

  -- Jeep Cherokee
  (@business_id, 'NHGBH41JXMN109208', 'HIJ-3134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Cherokee' LIMIT 1), @class_suv, 2022, 'Green', 5, 4, 'Automatic', 'Gasoline', 250, 1),

  -- Ford Escape
  (@business_id, 'OHGBH41JXMN109209', 'KLM-4134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Escape' LIMIT 1), @class_suv, 2023, 'Silver', 5, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'PHGBH41JXMN109210', 'KLM-4135', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Escape' LIMIT 1), @class_suv, 2022, 'Blue', 5, 4, 'Automatic', 'Gasoline', 250, 1);

-- LUXURY CARS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- BMW 3 Series
  (@business_id, 'QHGBH41JXMN109211', 'NOP-5134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = '3 Series' LIMIT 1), @class_lux, 2023, 'Black', 5, 4, 'Automatic', 'Gasoline', 300, 1),
  (@business_id, 'RHGBH41JXMN109212', 'NOP-5135', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = '3 Series' LIMIT 1), @class_lux, 2022, 'White', 5, 4, 'Automatic', 'Gasoline', 300, 1),

  -- BMW 5 Series
  (@business_id, 'SHGBH41JXMN109213', 'QRS-6134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = '5 Series' LIMIT 1), @class_lux, 2023, 'Gray', 5, 4, 'Automatic', 'Gasoline', 300, 1),

  -- Mercedes C-Class
  (@business_id, 'THGBH41JXMN109214', 'TUV-7134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'C-Class' LIMIT 1), @class_lux, 2023, 'Silver', 5, 4, 'Automatic', 'Gasoline', 300, 1),
  (@business_id, 'UHGBH41JXMN109215', 'TUV-7135', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'C-Class' LIMIT 1), @class_lux, 2022, 'Black', 5, 4, 'Automatic', 'Gasoline', 300, 1);

-- MINIVANS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Honda Odyssey
  (@business_id, 'VHGBH41JXMN109216', 'WXY-8134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Odyssey' LIMIT 1), @class_van, 2023, 'Silver', 8, 4, 'Automatic', 'Gasoline', 250, 1),
  (@business_id, 'WHGBH41JXMN109217', 'WXY-8135', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Odyssey' LIMIT 1), @class_van, 2022, 'White', 8, 4, 'Automatic', 'Gasoline', 250, 1),

  -- Toyota Sienna
  (@business_id, 'XHGBH41JXMN109218', 'ZAB-9134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Sienna' LIMIT 1), @class_van, 2023, 'Blue', 8, 4, 'Automatic', 'Hybrid', 250, 1),

  -- Dodge Grand Caravan
  (@business_id, 'YHGBH41JXMN109219', 'CDE-0134', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Grand Caravan' LIMIT 1), @class_van, 2022, 'Red', 7, 4, 'Automatic', 'Gasoline', 250, 1);

-- PICKUP TRUCKS
INSERT INTO car_rental_vehicle (business_id, vin, license_plate, vehicle_model_id, vehicle_class_id, model_year, color, seats, doors, transmission, fuel_type, daily_mileage_limit, is_active)
VALUES
  -- Ford F-150
  (@business_id, 'ZHGBH41JXMN109220', 'FGH-1034', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'F-150' LIMIT 1), @class_truck, 2023, 'Black', 5, 4, 'Automatic', 'Gasoline', 300, 1),
  (@business_id, '1HGBH41JXMN109221', 'FGH-1035', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'F-150' LIMIT 1), @class_truck, 2022, 'White', 5, 4, 'Automatic', 'Diesel', 300, 1),

  -- Chevrolet Silverado
  (@business_id, '2HGBH41JXMN109222', 'IJK-2034', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Silverado' LIMIT 1), @class_truck, 2023, 'Silver', 5, 4, 'Automatic', 'Gasoline', 300, 1),

  -- Dodge Ram 1500
  (@business_id, '3HGBH41JXMN109223', 'LMN-3034', (SELECT vehicle_model_id FROM car_rental_vehicle_model WHERE model_name = 'Ram 1500' LIMIT 1), @class_truck, 2022, 'Blue', 5, 4, 'Automatic', 'Gasoline', 300, 1);

-- ============================
-- VEHICLE INVENTORY (Assign vehicles to locations randomly)
-- ============================
INSERT INTO car_rental_vehicle_inventory (vehicle_id, location_id, operational_status, odometer_km)
SELECT
  v.vehicle_id,
  -- Distribute vehicles across 3 locations
  CASE
    WHEN v.vehicle_id % 3 = 1 THEN @loc_toronto
    WHEN v.vehicle_id % 3 = 2 THEN @loc_mississauga
    ELSE @loc_brampton
  END as location_id,
  'ready' as operational_status,
  FLOOR(5000 + (RAND() * 15000)) as odometer_km
FROM car_rental_vehicle v
WHERE v.business_id = @business_id;

-- ============================
-- RATE PLANS
-- ============================
INSERT INTO car_rental_rate_plan (business_id, name, currency, is_active)
VALUES
  (@business_id, 'Standard Rates', 'CAD', 1),
  (@business_id, 'Weekend Special', 'CAD', 1),
  (@business_id, 'Corporate', 'CAD', 1);

SET @rate_standard = LAST_INSERT_ID();
SET @rate_weekend = @rate_standard + 1;
SET @rate_corporate = @rate_standard + 2;

-- ============================
-- RATE PLAN PRICES (Standard Rates for all locations and classes)
-- ============================
INSERT INTO car_rental_rate_plan_price (rate_plan_id, vehicle_class_id, location_id, price_per_day, price_per_week, effective_from, effective_to)
VALUES
  -- Toronto rates
  (@rate_standard, @class_econ, @loc_toronto, 45.00, 250.00, '2024-01-01', NULL),
  (@rate_standard, @class_comp, @loc_toronto, 55.00, 300.00, '2024-01-01', NULL),
  (@rate_standard, @class_mid, @loc_toronto, 70.00, 400.00, '2024-01-01', NULL),
  (@rate_standard, @class_full, @loc_toronto, 85.00, 500.00, '2024-01-01', NULL),
  (@rate_standard, @class_suv, @loc_toronto, 95.00, 550.00, '2024-01-01', NULL),
  (@rate_standard, @class_lux, @loc_toronto, 150.00, 900.00, '2024-01-01', NULL),
  (@rate_standard, @class_van, @loc_toronto, 110.00, 650.00, '2024-01-01', NULL),
  (@rate_standard, @class_truck, @loc_toronto, 120.00, 700.00, '2024-01-01', NULL),

  -- Mississauga rates
  (@rate_standard, @class_econ, @loc_mississauga, 42.00, 240.00, '2024-01-01', NULL),
  (@rate_standard, @class_comp, @loc_mississauga, 52.00, 290.00, '2024-01-01', NULL),
  (@rate_standard, @class_mid, @loc_mississauga, 68.00, 390.00, '2024-01-01', NULL),
  (@rate_standard, @class_full, @loc_mississauga, 82.00, 490.00, '2024-01-01', NULL),
  (@rate_standard, @class_suv, @loc_mississauga, 92.00, 540.00, '2024-01-01', NULL),
  (@rate_standard, @class_lux, @loc_mississauga, 145.00, 870.00, '2024-01-01', NULL),
  (@rate_standard, @class_van, @loc_mississauga, 108.00, 640.00, '2024-01-01', NULL),
  (@rate_standard, @class_truck, @loc_mississauga, 118.00, 690.00, '2024-01-01', NULL),

  -- Brampton rates
  (@rate_standard, @class_econ, @loc_brampton, 40.00, 230.00, '2024-01-01', NULL),
  (@rate_standard, @class_comp, @loc_brampton, 50.00, 280.00, '2024-01-01', NULL),
  (@rate_standard, @class_mid, @loc_brampton, 65.00, 380.00, '2024-01-01', NULL),
  (@rate_standard, @class_full, @loc_brampton, 80.00, 480.00, '2024-01-01', NULL),
  (@rate_standard, @class_suv, @loc_brampton, 90.00, 530.00, '2024-01-01', NULL),
  (@rate_standard, @class_lux, @loc_brampton, 140.00, 850.00, '2024-01-01', NULL),
  (@rate_standard, @class_van, @loc_brampton, 105.00, 630.00, '2024-01-01', NULL),
  (@rate_standard, @class_truck, @loc_brampton, 115.00, 680.00, '2024-01-01', NULL);

-- ============================
-- ADD-ONS
-- ============================
INSERT INTO car_rental_add_on (business_id, name, pricing_unit, base_price, is_active)
VALUES
  (@business_id, 'GPS Navigation', 'per_day', 12.00, 1),
  (@business_id, 'Child Safety Seat', 'per_day', 10.00, 1),
  (@business_id, 'Booster Seat', 'per_day', 8.00, 1),
  (@business_id, 'Additional Driver', 'per_rental', 25.00, 1),
  (@business_id, 'Satellite Radio', 'per_day', 5.00, 1),
  (@business_id, 'Ski Rack', 'per_rental', 30.00, 1),
  (@business_id, 'Bike Rack', 'per_rental', 25.00, 1),
  (@business_id, 'Winter Tires', 'per_day', 15.00, 1);

-- ============================
-- INSURANCE OPTIONS
-- ============================
INSERT INTO car_rental_insurance_option (business_id, name, pricing_unit, base_price, is_active)
VALUES
  (@business_id, 'Collision Damage Waiver (CDW)', 'per_day', 25.00, 1),
  (@business_id, 'Loss Damage Waiver (LDW)', 'per_day', 30.00, 1),
  (@business_id, 'Personal Accident Insurance (PAI)', 'per_day', 12.00, 1),
  (@business_id, 'Personal Effects Coverage (PEC)', 'per_day', 8.00, 1),
  (@business_id, 'Supplemental Liability Insurance (SLI)', 'per_day', 15.00, 1),
  (@business_id, 'Premium Protection Package', 'per_day', 45.00, 1);

-- ============================
-- SUMMARY QUERIES
-- ============================

-- View vehicles by location
SELECT
  l.name as location_name,
  vc.class_name,
  COUNT(*) as vehicle_count
FROM car_rental_vehicle_inventory i
JOIN car_rental_location l ON i.location_id = l.location_id
JOIN car_rental_vehicle v ON i.vehicle_id = v.vehicle_id
JOIN car_rental_vehicle_class vc ON v.vehicle_class_id = vc.vehicle_class_id
GROUP BY l.name, vc.class_name
ORDER BY l.name, vc.class_name;

-- View all vehicles with their details
SELECT
  l.name as location,
  vc.class_name,
  m.make_name,
  mo.model_name,
  v.model_year,
  v.color,
  v.license_plate,
  i.operational_status,
  i.odometer_km
FROM car_rental_vehicle v
JOIN car_rental_vehicle_inventory i ON v.vehicle_id = i.vehicle_id
JOIN car_rental_location l ON i.location_id = l.location_id
JOIN car_rental_vehicle_class vc ON v.vehicle_class_id = vc.vehicle_class_id
JOIN car_rental_vehicle_model mo ON v.vehicle_model_id = mo.vehicle_model_id
JOIN car_rental_vehicle_make m ON mo.vehicle_make_id = m.vehicle_make_id
ORDER BY l.name, vc.class_name, m.make_name;