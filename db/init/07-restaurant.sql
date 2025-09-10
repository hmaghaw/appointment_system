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
    allowed_item_id INT NOT NULL,
    price_delta DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (combo_group_id) REFERENCES restaurant_combo_group(combo_group_id),
    FOREIGN KEY (allowed_item_id) REFERENCES restaurant_item(item_id)
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
    max_select INT DEFAULT 3,
    FOREIGN KEY (business_id) REFERENCES business(business_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_modifier (
    modifier_id INT AUTO_INCREMENT PRIMARY KEY,
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
    order_status ENUM('pending','confirmed','preparing','ready','out_for_delivery','delivered','cancelled') DEFAULT 'pending',
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
    price_delta DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_item_id) REFERENCES restaurant_order_item(order_item_id),

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE restaurant_order_item_modifier (
    order_item_modifier_id INT AUTO_INCREMENT PRIMARY KEY,
    order_item_id INT NOT NULL,
    modifier_id INT NOT NULL,
    price_delta DECIMAL(10,2) NOT NULL,
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

ALTER TABLE restaurant_item DROP COLUMN item_category_id;