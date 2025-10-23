-- ======================
-- ITEM CATEGORIES (GLOBAL CLASSIFICATION)
-- ======================
CREATE TABLE restaurant_item_category (
    item_category_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,          -- e.g., Pizza, Drink, Dessert
    description TEXT,
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ======================
-- MENUS
-- ======================
CREATE TABLE restaurant_menu (
    menu_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,          -- Breakfast, Lunch, Dinner
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ======================
-- MENU ITEMS
-- ======================
CREATE TABLE restaurant_item (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,   -- global classification
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2) NOT NULL,
    calories INT,                         -- in kcal
    preparation_time INT,                 -- in minutes
    is_combo BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    image_url VARCHAR(255),
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ======================
-- AVAILABILITY (Menus can have multiple time slots)
-- ======================
CREATE TABLE restaurant_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,           -- e.g., Breakfast Hours
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_availability_detail (
    availability_detail_id INT AUTO_INCREMENT PRIMARY KEY,
    availability_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    open_time TIME,
    close_time TIME,
    is_closed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (availability_id) REFERENCES restaurant_availability(availability_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_menu_availability (
    menu_id INT NOT NULL,
    availability_id INT NOT NULL,
    PRIMARY KEY (menu_id, availability_id),
    FOREIGN KEY (menu_id) REFERENCES restaurant_menu(menu_id),
    FOREIGN KEY (availability_id) REFERENCES restaurant_availability(availability_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ======================
-- COMBOS
-- ======================
CREATE TABLE restaurant_combo_group (
    combo_group_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,                 -- the combo meal
    name VARCHAR(100) NOT NULL,           -- e.g., Choose Pizza, Choose Drink
    min_select INT DEFAULT 1,
    max_select INT DEFAULT 1,
    display_order INT,
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_combo_group_item (
    combo_group_item_id INT AUTO_INCREMENT PRIMARY KEY,
    combo_group_id INT NOT NULL,
    item_id INT NOT NULL,
    price_delta DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (combo_group_id) REFERENCES restaurant_combo_group(combo_group_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ======================
-- BUSINESS-WIDE MODIFIERS
-- ======================
CREATE TABLE restaurant_modifier_group (
    modifier_group_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,           -- e.g., Extras
    is_required BOOLEAN DEFAULT FALSE,
    min_select INT DEFAULT 0,
    max_select INT DEFAULT 99,
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_modifier (
    modifier_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    modifier_group_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,           -- e.g., Extra Cheese
    price_delta DECIMAL(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0,
    FOREIGN KEY (modifier_group_id) REFERENCES restaurant_modifier_group(modifier_group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_item_modifier_group (
    item_id INT NOT NULL,
    modifier_group_id INT NOT NULL,
    PRIMARY KEY (item_id, modifier_group_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id),
    FOREIGN KEY (modifier_group_id) REFERENCES restaurant_modifier_group(modifier_group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ======================
-- ORDERS
-- ======================
CREATE TABLE restaurant_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    business_id INT NOT NULL,
    order_status ENUM('pending','confirmed','preparing','ready','out_for_delivery','delivered','cancelled') DEFAULT 'confirmed',
    order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    scheduled_time DATETIME NULL,
    total_price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id),
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_order_item (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    base_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES restaurant_order(order_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_order_item_option (
    order_item_option_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL,
    option_id INT NOT NULL,
    name varchar(100),
    price_delta DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_item_id) REFERENCES restaurant_order_item(order_item_id),

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_order_item_modifier (
    order_item_modifier_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL,
    modifier_id INT NOT NULL,
    name varchar(100),
    price_delta DECIMAL(10,2) NOT NULL,
    quantity INT default 1,
    FOREIGN KEY (order_item_id) REFERENCES restaurant_order_item(order_item_id),
    FOREIGN KEY (modifier_id) REFERENCES restaurant_modifier(modifier_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_order_combo_selection (
    order_combo_selection_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL,
    combo_group_id INT NOT NULL,
    selected_item_id INT NOT NULL,
    FOREIGN KEY (order_item_id) REFERENCES restaurant_order_item(order_item_id),
    FOREIGN KEY (combo_group_id) REFERENCES restaurant_combo_group(combo_group_id),
    FOREIGN KEY (selected_item_id) REFERENCES restaurant_item(item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_menu_section (
    menu_section_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    menu_id INT NOT NULL,                     -- the menu it belongs to (Breakfast, Lunch, etc.)
    name VARCHAR(100) NOT NULL,               -- e.g., "Pizzas", "Drinks", "Desserts"
    description TEXT,                         -- optional text
    display_order INT,                        -- controls ordering on the screen
    FOREIGN KEY (business_id) REFERENCES business(business_id),
    FOREIGN KEY (menu_id) REFERENCES restaurant_menu(menu_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_menu_section_item (
    item_id INT NOT NULL,
    menu_section_id INT NOT NULL,
    display_order INT,
    PRIMARY KEY (item_id, menu_section_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id),
    FOREIGN KEY (menu_section_id) REFERENCES restaurant_menu_section(menu_section_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_option_group (
    option_group_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,          -- e.g., Size, Crust
    is_required BOOLEAN DEFAULT FALSE,
    min_select INT DEFAULT 0,
    max_select INT DEFAULT 1,
    display_order INT DEFAULT 0,
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_option (
    option_id INT AUTO_INCREMENT PRIMARY KEY,
    option_group_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,          -- e.g., Small, Medium, Large
    price_delta DECIMAL(10,2) DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    display_order INT DEFAULT 0,
    FOREIGN KEY (option_group_id) REFERENCES restaurant_option_group(option_group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_item_option_group (
    item_id INT NOT NULL,
    option_group_id INT NOT NULL,
    PRIMARY KEY (item_id, option_group_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id),
    FOREIGN KEY (option_group_id) REFERENCES restaurant_option_group(option_group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_tag (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    name VARCHAR(100) NOT NULL UNIQUE,  -- e.g., 'Vegetarian', 'Vegan', 'Halal'
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_item_tag (
    item_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (item_id, tag_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id),
    FOREIGN KEY (tag_id) REFERENCES restaurant_tag(tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_item_category_map (
    item_id INT NOT NULL,
    item_category_id INT NOT NULL,
    PRIMARY KEY (item_id, item_category_id),
    FOREIGN KEY (item_id) REFERENCES restaurant_item(item_id),
    FOREIGN KEY (item_category_id) REFERENCES restaurant_item_category(item_category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_integration (
    integration_id INT AUTO_INCREMENT PRIMARY KEY,

    -- What type of entity is being mapped
    entity_type VARCHAR(50) ,
    -- Local entity reference (points to the corresponding table in your schema)
    entity_id INT NOT NULL,
    name VARCHAR(255) ,
    -- External system (POS provider)
    provider ENUM('clover','square','toast') NOT NULL,

    -- External IDs
    external_id VARCHAR(255) NOT NULL,
    external_parent_id VARCHAR(255) DEFAULT NULL, -- e.g. modifier_group_id for modifiers
    external_location_id VARCHAR(255) DEFAULT NULL,

    -- Business context (multi-tenant safety)
    business_id INT NOT NULL,

    -- Uniqueness guarantee: one mapping per provider + business + external_id
    UNIQUE KEY uniq_entity_provider (entity_type, provider, business_id, external_id),

    -- Indexes for lookup
    INDEX idx_entity_lookup (entity_type, entity_id, provider, business_id),
    INDEX idx_external_parent (external_parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE restaurant_clover_app (
    clover_app_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT UNIQUE,
    app_id VARCHAR(100),
    app_secret VARCHAR(100),
    clover_url VARCHAR(100)
);

CREATE TABLE restaurant_translation (
  translation_id INT AUTO_INCREMENT PRIMARY KEY,
  business_id int NOT NULL,
  table_name VARCHAR(100) NOT NULL,
  record_id INT NOT NULL,
  field_name VARCHAR(100) NOT NULL,
  language_code CHAR(5) NOT NULL,
  value TEXT NOT NULL,
  translation TEXT NOT NULL,
  UNIQUE KEY uq_translation (table_name, record_id, field_name, language_code),
  INDEX idx_table_record_lang (table_name, record_id, language_code)
);
