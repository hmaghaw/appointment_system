-- ======================
-- ITEM CATEGORIES
-- ======================
INSERT INTO restaurant_item_category (item_category_id, business_id, name, description)
VALUES
(1, 73, 'Pizza', 'All pizza items'),
(2, 73, 'Drink', 'All beverages'),
(3, 73, 'Dessert', 'Cakes, ice cream, sweets');

-- ======================
-- MENUS
-- ======================
INSERT INTO restaurant_menu (menu_id, business_id, name, description, is_active)
VALUES
(1, 73, 'Breakfast Menu', 'Morning specials', TRUE),
(2, 73, 'Lunch Menu', 'Afternoon meals', TRUE),
(3, 73, 'Dinner Menu', 'Evening selections', TRUE);

-- ======================
-- MENU SECTIONS
-- ======================
INSERT INTO restaurant_menu_section (menu_section_id, menu_id, name, description, display_order)
VALUES
-- Breakfast
(1, 1, 'Morning Pizzas', 'Light pizzas for breakfast', 1),
(2, 1, 'Drinks', 'Morning beverages', 2),

-- Lunch
(3, 2, 'Pizzas', 'Classic pizzas', 1),
(4, 2, 'Drinks', 'Cold drinks', 2),
(5, 2, 'Combos', 'Meal deals', 3),

-- Dinner
(6, 3, 'Pizzas', 'Signature pizzas', 1),
(7, 3, 'Drinks', 'Evening beverages', 2),
(8, 3, 'Desserts', 'Sweet treats', 3);

-- ======================
-- MENU ITEMS
-- ======================
INSERT INTO restaurant_item (item_id, item_category_id, name, description, base_price, is_combo, is_active, image_url)
VALUES
(1, 1, 'Margherita Pizza', 'Classic cheese & tomato', 9.99, FALSE, TRUE, NULL),
(2, 1, 'Pepperoni Pizza', 'Spicy pepperoni & cheese', 11.99, FALSE, TRUE, NULL),
(3, 1, 'Veggie Pizza', 'Mixed vegetables with mozzarella', 10.99, FALSE, TRUE, NULL),
(4, 2, 'Coke', 'Chilled soft drink', 1.99, FALSE, TRUE, NULL),
(5, 2, 'Water', 'Mineral water bottle', 1.49, FALSE, TRUE, NULL),
(6, 2, 'Orange Juice', 'Freshly squeezed OJ', 2.49, FALSE, TRUE, NULL),
(7, 3, 'Cheesecake', 'Classic NY cheesecake slice', 4.99, FALSE, TRUE, NULL),
(8, 3, 'Chocolate Lava Cake', 'Rich chocolate cake with molten center', 5.99, FALSE, TRUE, NULL),
(9, 1, 'Breakfast Special Pizza', 'Eggs, bacon, and cheese on a pizza crust', 8.99, FALSE, TRUE, NULL),
(10, 1, 'Pizza Combo', '1 Pizza + 1 Drink', 12.99, TRUE, TRUE, NULL);

-- ======================
-- MAP ITEMS TO MENU SECTIONS
-- ======================
INSERT INTO restaurant_menu_section_item (item_id, menu_section_id)
VALUES
-- Breakfast Menu
(9, 1), (4, 2), (5, 2), (6, 2),

-- Lunch Menu
(1, 3), (2, 3), (3, 3),
(4, 4), (5, 4),
(10, 5),

-- Dinner Menu
(1, 6), (2, 6), (3, 6),
(4, 7), (5, 7), (6, 7),
(7, 8), (8, 8);

-- ======================
-- ITEM OPTIONS (Pizza sizes)
-- ======================
INSERT INTO restaurant_item_option_group (option_group_id, item_id, name, is_required, min_select, max_select, display_order)
VALUES
(1, 1, 'Size', TRUE, 1, 1, 1),
(2, 2, 'Size', TRUE, 1, 1, 1),
(3, 3, 'Size', TRUE, 1, 1, 1),
(4, 9, 'Size', TRUE, 1, 1, 1);

INSERT INTO restaurant_item_option (option_id, option_group_id, name, price_delta, is_default)
VALUES
-- Margherita Pizza
(1, 1, 'Small', 0.00, TRUE),
(2, 1, 'Medium', 2.00, FALSE),
(3, 1, 'Large', 4.00, FALSE),

-- Pepperoni Pizza
(4, 2, 'Small', 0.00, TRUE),
(5, 2, 'Medium', 2.00, FALSE),
(6, 2, 'Large', 4.00, FALSE),

-- Veggie Pizza
(7, 3, 'Small', 0.00, TRUE),
(8, 3, 'Medium', 2.00, FALSE),
(9, 3, 'Large', 4.00, FALSE),

-- Breakfast Pizza
(10, 4, 'Small', 0.00, TRUE),
(11, 4, 'Medium', 1.50, FALSE),
(12, 4, 'Large', 3.00, FALSE);

-- ======================
-- AVAILABILITY
-- ======================
INSERT INTO restaurant_availability (availability_id, business_id, name)
VALUES
(1, 73, 'Breakfast Hours'),
(2, 73, 'Lunch Hours'),
(3, 73, 'Dinner Hours'),
(4, 73, 'Weekend Brunch');

-- Breakfast: daily
INSERT INTO restaurant_availability_detail (availability_id, day_of_week, start_time, end_time)
VALUES (1, 'All', '06:00:00', '11:00:00');

-- Lunch: weekdays
INSERT INTO restaurant_availability_detail (availability_id, day_of_week, start_time, end_time)
VALUES
(2, 'Monday', '11:00:00', '15:00:00'),
(2, 'Tuesday', '11:00:00', '15:00:00'),
(2, 'Wednesday', '11:00:00', '15:00:00'),
(2, 'Thursday', '11:00:00', '15:00:00'),
(2, 'Friday', '11:00:00', '15:00:00');

-- Dinner: different hours by day
INSERT INTO restaurant_availability_detail (availability_id, day_of_week, start_time, end_time)
VALUES
(3, 'Monday', '17:00:00', '22:00:00'),
(3, 'Friday', '17:00:00', '23:30:00'),
(3, 'Saturday', '17:00:00', '23:30:00'),
(3, 'Sunday', '17:00:00', '22:00:00');

-- Weekend Brunch
INSERT INTO restaurant_availability_detail (availability_id, day_of_week, start_time, end_time)
VALUES
(4, 'Saturday', '10:00:00', '14:00:00'),
(4, 'Sunday', '10:00:00', '14:00:00');


INSERT INTO restaurant_menu_availability (menu_id, availability_id)
VALUES
(1, 1), (2, 2), (3, 3);

-- ======================
-- COMBOS (Pizza Combo)
-- ======================
INSERT INTO restaurant_combo_group (combo_group_id, item_id, name, min_select, max_select, display_order)
VALUES
(1, 10, 'Choose a Pizza', 1, 1, 1),
(2, 10, 'Choose a Drink', 1, 1, 2);

INSERT INTO restaurant_combo_group_item (combo_group_item_id, combo_group_id, allowed_item_id, price_delta)
VALUES
-- Pizzas
(1, 1, 1, 0.00), -- Margherita
(2, 1, 2, 2.00), -- Pepperoni (+$2)
(3, 1, 3, 1.00), -- Veggie (+$1)

-- Drinks
(4, 2, 4, 0.00), -- Coke
(5, 2, 5, 0.00), -- Water
(6, 2, 6, 0.50); -- Orange Juice (+$0.5)

-- ======================
-- MODIFIERS (Extras)
-- ======================
INSERT INTO restaurant_modifier_group (modifier_group_id, business_id, name, is_required, min_select, max_select)
VALUES (1, 73, 'Extras', FALSE, 0, 3);

INSERT INTO restaurant_modifier (modifier_id, modifier_group_id, name, price_delta, is_active)
VALUES
(1, 1, 'Extra Cheese', 1.50, TRUE),
(2, 1, 'Gluten-Free Crust', 2.00, TRUE),
(3, 1, 'Chili Flakes', 0.50, TRUE);

INSERT INTO restaurant_item_modifier_group (item_id, modifier_group_id)
VALUES
(1, 1), (2, 1), (3, 1), (9, 1);

INSERT INTO restaurant_modifier_group (business_id, name, is_required, min_select, max_select)
VALUES
(73, 'Pizza Sizes', TRUE, 1, 1),        -- Must choose exactly one size
(73, 'Extra Toppings', FALSE, 0, 3),    -- Optional, up to 3 toppings
(73, 'Choose a Drink', TRUE, 1, 1);


INSERT INTO restaurant_option_group
(business_id, name, is_required, min_select, max_select, display_order)
VALUES
(73, 'Pizza Sizes', TRUE, 1, 1, 1),
(73, 'Crust Type', TRUE, 1, 1, 2);

INSERT INTO restaurant_option (option_group_id, name, price_delta, is_default, display_order)
VALUES
(1, 'Small', 0.00, TRUE, 1),
(1, 'Medium', 2.00, FALSE, 2),
(1, 'Large', 4.00, FALSE, 3);

INSERT INTO restaurant_item_option_group (item_id, option_group_id)
VALUES
-- Margherita Pizza
(1, 1), (1, 2),
-- Pepperoni Pizza
(2, 1), (2, 2),
-- Veggie Pizza
(3, 1), (3, 2);

INSERT INTO restaurant_tag (business_id, name) VALUES
(73, 'Vegetarian'),
(73, 'Vegan'),
(73, 'Gluten Free'),
(73, 'Low Carb'),
(73, 'Halal'),
(73, 'Kosher'),
(73, 'Keto'),
(73, 'Dairy Free'),
(73, 'Nut Free'),
(73, 'Organic');

-- Margherita Pizza: Vegetarian, Halal
INSERT INTO restaurant_item_tag (item_id, tag_id) VALUES
(1, 1),  -- Vegetarian
(1, 5);  -- Halal

-- Pepperoni Pizza: Halal only
INSERT INTO restaurant_item_tag (item_id, tag_id) VALUES
(2, 5);  -- Halal

-- Veggie Pizza: Vegetarian, Vegan, Halal
INSERT INTO restaurant_item_tag (item_id, tag_id) VALUES
(3, 1),  -- Vegetarian
(3, 2),  -- Vegan
(3, 5);  -- Halal

-- Chicken Shawarma: Gluten Free, Halal, Low Carb
INSERT INTO restaurant_item_tag (item_id, tag_id) VALUES
(4, 3),  -- Gluten Free
(4, 4),  -- Low Carb
(4, 5);  -- Halal


-- Margherita Pizza: Pizzas, Vegetarian Dishes, Halal Specials
INSERT INTO restaurant_item_category_map (item_id, item_category_id) VALUES
(1, 1),
(2, 1),
(3, 1);

-- Pepperoni Pizza: Pizzas, Halal Specials
INSERT INTO restaurant_item_category_map (item_id, item_category_id) VALUES
(4, 3),
(8, 3),
(7, 3);

-- Veggie Pizza: Pizzas, Vegetarian Dishes
INSERT INTO restaurant_item_category_map (item_id, item_category_id) VALUES
(4, 2),
(5, 2),
(6, 2);

-- French Fries: Sides, Kids Menu
INSERT INTO restaurant_item_category_map (item_id, item_category_id) VALUES
(4, 3),
(4, 4);

-- Chicken Shawarma: Halal Specials, Main Dish (if you had that category)
INSERT INTO restaurant_item_category_map (item_id, item_category_id) VALUES
(5, 5);

-- 1. Create Order
INSERT INTO restaurant_order (customer_id, business_id, order_status, total_price, notes)
VALUES (21, 73, 'pending', 80.45, 'Customer prefers large size for item 39, extra cheese on item 45.');

-- Assume order_id = 7001

-- 2. Order Items
-- Item 45 (base 9.99 + modifier)
INSERT INTO restaurant_order_item (order_id, item_id, quantity, base_price, total_price)
VALUES (1, 45, 1, 9.99, 11.49);

-- Item 46 (base 11.50 ×2 + free modifier)
INSERT INTO restaurant_order_item (order_id, item_id, quantity, base_price, total_price)
VALUES (1, 46, 2, 11.50, 23.00);

-- Item 73 (base 12.99 + modifier)
INSERT INTO restaurant_order_item (order_id, item_id, quantity, base_price, total_price)
VALUES (1, 73, 1, 12.99, 13.99);

-- Item 39 (base 8.99 + option Large Size)
INSERT INTO restaurant_order_item (order_id, item_id, quantity, base_price, total_price)
VALUES (1, 39, 1, 8.99, 12.99);

-- Item 44 (base 9.99 ×2 + option Stuffed Crust)
INSERT INTO restaurant_order_item (order_id, item_id, quantity, base_price, total_price)
VALUES (1, 44, 2, 9.99, 18.98);

-- Assume order_item_ids: 8001=45, 8002=46, 8003=73, 8004=39, 8005=44

-- 3. Order Item Modifiers
-- Item 45 → Extra Cheese (+1.50)
INSERT INTO restaurant_order_item_modifier (order_item_id, modifier_id, price_delta)
VALUES (1, 101, 1.50);  -- modifier_id=101 = Extra Cheese

-- Item 46 → Chili Flakes (free)
INSERT INTO restaurant_order_item_modifier (order_item_id, modifier_id, price_delta)
VALUES (2, 102, 0.00);  -- modifier_id=102 = Chili Flakes

-- Item 73 → Garlic Dip (+1.00)
INSERT INTO restaurant_order_item_modifier (order_item_id, modifier_id, price_delta)
VALUES (3, 201, 1.00);  -- modifier_id=201 = Garlic Dip

-- 4. Order Item Options
-- Item 39 → Large Size (+4.00)
INSERT INTO restaurant_order_item_option (order_item_id, option_id, price_delta)
VALUES (4, 301, 4.00);  -- option_id=301 = Large Size

-- Item 44 → Stuffed Crust (+1.00 each)
INSERT INTO restaurant_order_item_option (order_item_id, option_id, price_delta)
VALUES (5, 401, 1.00);  -- option_id=401 = Stuffed Crust
