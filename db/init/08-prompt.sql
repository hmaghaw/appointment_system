-- Standard template sections for restaurants
CREATE TABLE prompt_section_template (
    template_section_id INT AUTO_INCREMENT PRIMARY KEY,
    section_type ENUM(
        'role',
        'greeting',
        'business_info',
        'hours',
        'food_categories',
        'ordering_rules',
        'confirmation',
        'strict_rules'
    ) NOT NULL,
    default_content TEXT NOT NULL,
    language VARCHAR(5) NOT NULL DEFAULT 'en', -- base language
    section_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Business-specific prompt sections (overrides)
CREATE TABLE prompt_section_for_business (
    business_prompt_section_id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    template_section_id INT NOT NULL,
    custom_content TEXT NOT NULL,
    language VARCHAR(5) NOT NULL DEFAULT 'en', -- base language
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES business(business_id),
    FOREIGN KEY (template_section_id) REFERENCES prompt_section_template(template_section_id)
);

-- Translations for either templates or business-specific sections
CREATE TABLE prompt_section_translation (
    translation_id INT AUTO_INCREMENT PRIMARY KEY,
    section_type ENUM(
        'role',
        'greeting',
        'business_info',
        'hours',
        'food_categories',
        'ordering_rules',
        'confirmation',
        'strict_rules'
    ) NOT NULL,
    reference_id INT NOT NULL,          -- template_section_id OR business_prompt_section_id
    reference_type ENUM('template','business') NOT NULL,
    language_code VARCHAR(5) NOT NULL,  -- e.g. 'en', 'fr', 'ar', 'zh'
    translated_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
