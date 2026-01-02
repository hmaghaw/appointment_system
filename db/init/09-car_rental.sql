-- ============================
-- CONSOLIDATED CAR RENTAL DDL
-- - car_rental_vehicle_schedule is the source of truth for time blocks
-- - Reuses existing: business(business_id), customer(customer_id)
-- - Renamed schedule linkage columns:
--     reservation_id -> car_rental_reservation_id
--     rental_contract_id -> car_rental_rental_contract_id
-- - Removed chk_vsch_one_source (MySQL FK/check constraint limitation)
-- ============================

create table car_rental_location (
  location_id int auto_increment primary key,
  business_id int not null,
  name varchar(120) not null,
  address_line1 varchar(160) not null,
  address_line2 varchar(160) null,
  city varchar(80) not null,
  province_state varchar(80) null,
  country varchar(80) not null,
  postal_code varchar(20) null,
  latitude decimal(10,7) null,
  longitude decimal(10,7) null,
  phone varchar(30) null,
  is_active tinyint(1) default 1 null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_car_rental_location_business
    foreign key (business_id) references business (business_id)
      on delete cascade
);

create table car_rental_customer_driver_license (
  customer_driver_license_id int auto_increment primary key,
  customer_id int not null,
  license_number varchar(60) not null,
  issuing_country varchar(80) not null,
  issuing_region varchar(80) null,
  expiry_date date not null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_cdl_customer
    foreign key (customer_id) references customer (customer_id)
      on delete cascade,
  unique key uq_license (license_number, issuing_country)
);

create table car_rental_vehicle_class (
  vehicle_class_id int auto_increment primary key,
  business_id int not null,
  class_code varchar(20) not null,
  class_name varchar(80) not null,
  description varchar(255) null,
  is_active tinyint(1) default 1 null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_vehicle_class_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  unique key uq_vehicle_class_code (business_id, class_code)
);

create table car_rental_vehicle_make (
  vehicle_make_id int auto_increment primary key,
  make_name varchar(80) not null,
  unique key uq_make (make_name)
);

create table car_rental_vehicle_model (
  vehicle_model_id int auto_increment primary key,
  vehicle_make_id int not null,
  model_name varchar(80) not null,
  body_type varchar(40) null,
  constraint fk_model_make
    foreign key (vehicle_make_id) references car_rental_vehicle_make (vehicle_make_id),
  unique key uq_make_model (vehicle_make_id, model_name)
);

create table car_rental_vehicle (
  vehicle_id int auto_increment primary key,
  business_id int not null,
  vin varchar(40) not null,
  license_plate varchar(20) not null,
  vehicle_model_id int not null,
  vehicle_class_id int not null,
  model_year int not null,
  color varchar(40) null,
  seats int not null,
  doors int null,
  transmission varchar(20) not null,
  fuel_type varchar(20) not null,
  daily_mileage_limit int null,
  is_active tinyint(1) default 1 null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_vehicle_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  constraint fk_vehicle_model
    foreign key (vehicle_model_id) references car_rental_vehicle_model (vehicle_model_id),
  constraint fk_vehicle_class
    foreign key (vehicle_class_id) references car_rental_vehicle_class (vehicle_class_id),
  unique key uq_vin (vin),
  unique key uq_plate (license_plate)
);

-- Inventory = current snapshot (location + operational status)
create table car_rental_vehicle_inventory (
  vehicle_inventory_id int auto_increment primary key,
  vehicle_id int not null,
  location_id int not null,
  operational_status varchar(30) not null, -- ready, cleaning, maintenance, inactive
  odometer_km int null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_inv_vehicle
    foreign key (vehicle_id) references car_rental_vehicle (vehicle_id)
      on delete cascade,
  constraint fk_inv_location
    foreign key (location_id) references car_rental_location (location_id)
      on delete cascade
);

create table car_rental_rate_plan (
  rate_plan_id int auto_increment primary key,
  business_id int not null,
  name varchar(80) not null,
  currency varchar(10) not null default 'CAD',
  is_active tinyint(1) default 1 null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_rate_plan_business
    foreign key (business_id) references business (business_id)
      on delete cascade
);

create table car_rental_rate_plan_price (
  rate_plan_price_id int auto_increment primary key,
  rate_plan_id int not null,
  vehicle_class_id int not null,
  location_id int not null,
  price_per_day decimal(10,2) not null,
  price_per_week decimal(10,2) null,
  effective_from date not null,
  effective_to date null,
  constraint fk_rpp_plan
    foreign key (rate_plan_id) references car_rental_rate_plan (rate_plan_id)
      on delete cascade,
  constraint fk_rpp_class
    foreign key (vehicle_class_id) references car_rental_vehicle_class (vehicle_class_id)
      on delete cascade,
  constraint fk_rpp_location
    foreign key (location_id) references car_rental_location (location_id)
      on delete cascade
);

create table car_rental_add_on (
  add_on_id int auto_increment primary key,
  business_id int not null,
  name varchar(80) not null,
  pricing_unit varchar(20) not null,
  base_price decimal(10,2) not null,
  is_active tinyint(1) default 1 null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_add_on_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  unique key uq_add_on_name (business_id, name)
);

create table car_rental_insurance_option (
  insurance_option_id int auto_increment primary key,
  business_id int not null,
  name varchar(80) not null,
  pricing_unit varchar(20) not null,
  base_price decimal(10,2) not null,
  is_active tinyint(1) default 1 null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_insurance_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  unique key uq_insurance_name (business_id, name)
);

create table car_rental_rental_request (
  rental_request_id int auto_increment primary key,
  business_id int not null,
  customer_id int null,
  pickup_datetime datetime not null,
  dropoff_datetime datetime not null,
  pickup_location_id int not null,
  dropoff_location_id int not null,
  passengers int null,
  luggage_bags int null,
  preferred_body_type varchar(40) null,
  preferred_transmission varchar(20) null,
  preferred_fuel_type varchar(20) null,
  wants_luxury tinyint(1) null,
  wants_low_budget tinyint(1) null,
  needs_child_seat tinyint(1) null,
  trip_type varchar(30) null,
  notes varchar(500) null,
  priority_focus varchar(20) not null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_rr_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  constraint fk_rr_customer
    foreign key (customer_id) references customer (customer_id)
      on delete set null,
  constraint fk_rr_pickup_loc
    foreign key (pickup_location_id) references car_rental_location (location_id)
      on delete restrict,
  constraint fk_rr_dropoff_loc
    foreign key (dropoff_location_id) references car_rental_location (location_id)
      on delete restrict
);

-- Create schedule BEFORE reservation/contract.
-- It will get FKs to reservation/contract via ALTER after those tables exist.
create table car_rental_vehicle_schedule (
  vehicle_schedule_id int auto_increment primary key,
  business_id int not null,
  vehicle_id int not null,
  schedule_type varchar(30) not null, -- reservation, rental, maintenance, hold
  status varchar(30) not null,        -- tentative, confirmed, active, closed, cancelled
  start_datetime datetime not null,
  end_datetime datetime not null,
  car_rental_reservation_id int null,
  car_rental_rental_contract_id int null,
  notes varchar(255) null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_vsch_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  constraint fk_vsch_vehicle
    foreign key (vehicle_id) references car_rental_vehicle (vehicle_id)
      on delete cascade,
  constraint chk_vsch_time check (end_datetime > start_datetime)
);

create table car_rental_reservation (
  reservation_id int auto_increment primary key,
  business_id int not null,
  rental_request_id int null,
  customer_id int not null,
  reservation_status varchar(30) not null,
  pickup_datetime datetime not null,
  dropoff_datetime datetime not null,
  pickup_location_id int not null,
  dropoff_location_id int not null,
  vehicle_class_id int not null,
  vehicle_id int null,
  rate_plan_id int not null,
  vehicle_schedule_id int null,
  base_amount decimal(10,2) not null default 0,
  taxes_amount decimal(10,2) not null default 0,
  total_amount decimal(10,2) not null default 0,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_res_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  constraint fk_res_req
    foreign key (rental_request_id) references car_rental_rental_request (rental_request_id)
      on delete set null,
  constraint fk_res_customer
    foreign key (customer_id) references customer (customer_id)
      on delete restrict,
  constraint fk_res_pickup_loc
    foreign key (pickup_location_id) references car_rental_location (location_id)
      on delete restrict,
  constraint fk_res_dropoff_loc
    foreign key (dropoff_location_id) references car_rental_location (location_id)
      on delete restrict,
  constraint fk_res_class
    foreign key (vehicle_class_id) references car_rental_vehicle_class (vehicle_class_id)
      on delete restrict,
  constraint fk_res_vehicle
    foreign key (vehicle_id) references car_rental_vehicle (vehicle_id)
      on delete set null,
  constraint fk_res_rate_plan
    foreign key (rate_plan_id) references car_rental_rate_plan (rate_plan_id)
      on delete restrict,
  constraint fk_res_vehicle_schedule
    foreign key (vehicle_schedule_id) references car_rental_vehicle_schedule (vehicle_schedule_id)
      on delete set null
);

create table car_rental_reservation_add_on (
  reservation_add_on_id int auto_increment primary key,
  reservation_id int not null,
  add_on_id int not null,
  quantity int not null default 1,
  price decimal(10,2) not null,
  constraint fk_res_add_res
    foreign key (reservation_id) references car_rental_reservation (reservation_id)
      on delete cascade,
  constraint fk_res_add_addon
    foreign key (add_on_id) references car_rental_add_on (add_on_id)
      on delete restrict,
  unique key uq_res_add (reservation_id, add_on_id)
);

create table car_rental_reservation_insurance (
  reservation_insurance_id int auto_increment primary key,
  reservation_id int not null,
  insurance_option_id int not null,
  price decimal(10,2) not null,
  constraint fk_res_ins_res
    foreign key (reservation_id) references car_rental_reservation (reservation_id)
      on delete cascade,
  constraint fk_res_ins_opt
    foreign key (insurance_option_id) references car_rental_insurance_option (insurance_option_id)
      on delete restrict,
  unique key uq_res_ins (reservation_id, insurance_option_id)
);

create table car_rental_rental_contract (
  rental_contract_id int auto_increment primary key,
  business_id int not null,
  reservation_id int null,
  customer_id int not null,
  vehicle_id int not null,
  pickup_location_id int not null,
  dropoff_location_id int not null,
  pickup_datetime datetime not null,
  expected_dropoff_datetime datetime not null,
  actual_dropoff_datetime datetime null,
  status varchar(30) not null,
  vehicle_schedule_id int null,
  odometer_out_km int null,
  odometer_in_km int null,
  fuel_level_out varchar(20) null,
  fuel_level_in varchar(20) null,
  total_amount decimal(10,2) not null default 0,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_rc_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  constraint fk_rc_res
    foreign key (reservation_id) references car_rental_reservation (reservation_id)
      on delete set null,
  constraint fk_rc_customer
    foreign key (customer_id) references customer (customer_id)
      on delete restrict,
  constraint fk_rc_vehicle
    foreign key (vehicle_id) references car_rental_vehicle (vehicle_id)
      on delete restrict,
  constraint fk_rc_pickup_loc
    foreign key (pickup_location_id) references car_rental_location (location_id)
      on delete restrict,
  constraint fk_rc_dropoff_loc
    foreign key (dropoff_location_id) references car_rental_location (location_id)
      on delete restrict,
  constraint fk_rc_vehicle_schedule
    foreign key (vehicle_schedule_id) references car_rental_vehicle_schedule (vehicle_schedule_id)
      on delete set null
);

create table car_rental_payment (
  payment_id int auto_increment primary key,
  business_id int not null,
  reservation_id int null,
  rental_contract_id int null,
  amount decimal(10,2) not null,
  currency varchar(10) not null default 'CAD',
  method varchar(30) not null,
  status varchar(30) not null,
  provider_ref varchar(120) null,
  created_at timestamp default current_timestamp null,
  updated_at timestamp default current_timestamp null on update current_timestamp,
  constraint fk_pay_business
    foreign key (business_id) references business (business_id)
      on delete cascade,
  constraint fk_pay_res
    foreign key (reservation_id) references car_rental_reservation (reservation_id)
      on delete set null,
  constraint fk_pay_contract
    foreign key (rental_contract_id) references car_rental_rental_contract (rental_contract_id)
      on delete set null
);

-- Add FKs from schedule -> reservation/contract AFTER both tables exist
alter table car_rental_vehicle_schedule
  add constraint fk_vsch_reservation
    foreign key (car_rental_reservation_id) references car_rental_reservation (reservation_id)
      on delete set null;

alter table car_rental_vehicle_schedule
  add constraint fk_vsch_contract
    foreign key (car_rental_rental_contract_id) references car_rental_rental_contract (rental_contract_id)
      on delete set null;

-- INDEXES
create index idx_res_pickup_time
  on car_rental_reservation (pickup_location_id, pickup_datetime, dropoff_datetime);

create index idx_res_vehicle
  on car_rental_reservation (vehicle_id, reservation_status);

create index idx_contract_vehicle
  on car_rental_rental_contract (vehicle_id, status);

create index idx_request_business_time
  on car_rental_rental_request (business_id, pickup_datetime, dropoff_datetime);

create index idx_vsch_vehicle_time
  on car_rental_vehicle_schedule (vehicle_id, start_datetime, end_datetime);

create index idx_vsch_business_vehicle_time
  on car_rental_vehicle_schedule (business_id, vehicle_id, start_datetime, end_datetime);
