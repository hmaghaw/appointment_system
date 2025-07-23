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

-- Add French translations for all services
INSERT INTO service_translation (service_id, language_code, name, description) VALUES
-- Hair Salon Services
(1, 'fr', 'Coupe femme', 'Coupe et coiffure pour femmes'),
(2, 'fr', 'Coupe homme', 'Coupe et coiffure pour hommes'),
(3, 'fr', 'Coloration', 'Service complet de coloration capillaire'),
(4, 'fr', 'Brushing', 'Shampooing et brushing'),
(5, 'fr', 'Taille de barbe', 'Taille et mise en forme de la barbe'),

-- Tech Store Services
(6, 'fr', 'Suppression de virus', 'Suppression complète des virus et logiciels malveillants'),
(7, 'fr', 'Récupération de données', 'Récupération des fichiers perdus'),
(8, 'fr', 'Optimisation PC portable', 'Amélioration des performances de l\'ordinateur'),

-- Medical Services
(9, 'fr', 'Examen général', 'Examen de santé de routine'),
(10, 'fr', 'Vaccination', 'Injection de vaccins'),
(11, 'fr', 'Test d\'allergie', 'Test d\'allergie complet'),
(12, 'fr', 'Consultation dermatologique', 'Évaluation de l\'état de la peau'),
(13, 'fr', 'Analyses de sang', 'Analyses de sang de routine');

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

-- Insert days of the week in multiple languages
-- English (en)
INSERT INTO translations (phrase, language_code, translated_phrase) VALUES
-- Days of the week
('Monday', 'en', 'Monday'),
('Tuesday', 'en', 'Tuesday'),
('Wednesday', 'en', 'Wednesday'),
('Thursday', 'en', 'Thursday'),
('Friday', 'en', 'Friday'),
('Saturday', 'en', 'Saturday'),
('Sunday', 'en', 'Sunday'),

-- Arabic (ar)
('Monday', 'ar', 'الاثنين'),
('Tuesday', 'ar', 'الثلاثاء'),
('Wednesday', 'ar', 'الأربعاء'),
('Thursday', 'ar', 'الخميس'),
('Friday', 'ar', 'الجمعة'),
('Saturday', 'ar', 'السبت'),
('Sunday', 'ar', 'الأحد'),

-- French (fr)
('Monday', 'fr', 'Lundi'),
('Tuesday', 'fr', 'Mardi'),
('Wednesday', 'fr', 'Mercredi'),
('Thursday', 'fr', 'Jeudi'),
('Friday', 'fr', 'Vendredi'),
('Saturday', 'fr', 'Samedi'),
('Sunday', 'fr', 'Dimanche'),

-- Chinese (zh)
('Monday', 'zh', '星期一'),
('Tuesday', 'zh', '星期二'),
('Wednesday', 'zh', '星期三'),
('Thursday', 'zh', '星期四'),
('Friday', 'zh', '星期五'),
('Saturday', 'zh', '星期六'),
('Sunday', 'zh', '星期日');
('CURRENT DATE & TIME', 'en', 'Current Date & Time'),
('CUSTOMER INFORMATION', 'en', 'Customer Information'),
('BUSINESS INFORMATION', 'en', 'Business Information'),
('BUSINESS WORKING HOURS', 'en', 'Business Working Hours'),
('SERVICES', 'en', 'Services'),
('EXAMPLES OF CONCISE RESPONSES', 'en', 'Examples of Concise Responses'),
('FUNCTION INSTRUCTIONS', 'en', 'Function Instructions'),

-- Arabic (ar)
('CURRENT DATE & TIME', 'ar', 'التاريخ والوقت الحالي'),
('CUSTOMER INFORMATION', 'ar', 'معلومات العميل'),
('BUSINESS INFORMATION', 'ar', 'معلومات العمل'),
('BUSINESS WORKING HOURS', 'ar', 'ساعات العمل'),
('SERVICES', 'ar', 'الخدمات'),
('EXAMPLES OF CONCISE RESPONSES', 'ar', 'أمثلة على الردود المختصرة'),
('FUNCTION INSTRUCTIONS', 'ar', 'تعليمات الوظيفة'),

-- French (fr)
('CURRENT DATE & TIME', 'fr', 'Date et heure actuelles'),
('CUSTOMER INFORMATION', 'fr', 'Informations client'),
('BUSINESS INFORMATION', 'fr', 'Informations sur l\'entreprise'),
('BUSINESS WORKING HOURS', 'fr', 'Heures d\'ouverture'),
('SERVICES', 'fr', 'Services'),
('EXAMPLES OF CONCISE RESPONSES', 'fr', 'Exemples de réponses concises'),
('FUNCTION INSTRUCTIONS', 'fr', 'Instructions de fonction'),

-- Chinese (zh)
('CURRENT DATE & TIME', 'zh', '当前日期和时间'),
('CUSTOMER INFORMATION', 'zh', '客户信息'),
('BUSINESS INFORMATION', 'zh', '商家信息'),
('BUSINESS WORKING HOURS', 'zh', '营业时间'),
('SERVICES', 'zh', '服务'),
('EXAMPLES OF CONCISE RESPONSES', 'zh', '简洁回复示例'),
('FUNCTION INSTRUCTIONS', 'zh', '功能说明'),

-- Time and Business Terms
-- English (en)
('AM', 'en', 'AM'),
('PM', 'en', 'PM'),
('Minute', 'en', 'Minute'),
('Business Name', 'en', 'Business Name'),
('Business Phone', 'en', 'Business Phone'),

-- Arabic (ar)
('AM', 'ar', 'ص'),
('PM', 'ar', 'م'),
('Minute', 'ar', 'دقيقة'),
('Business Name', 'ar', 'اسم النشاط التجاري'),
('Business Phone', 'ar', 'هاتف النشاط التجاري'),

-- French (fr)
('AM', 'fr', 'AM'),
('PM', 'fr', 'PM'),
('Minute', 'fr', 'Minute'),
('Business Name', 'fr', 'Nom de l\'entreprise'),
('Business Phone', 'fr', 'Téléphone de l\'entreprise'),

-- Chinese (zh)
('AM', 'zh', '上午'),
('PM', 'zh', '下午'),
('Minute', 'zh', '分钟'),
('Business Name', 'zh', '商家名称'),
('Business Phone', 'zh', '商家电话'),

-- Business Status
-- English (en)
('Closed', 'en', 'Closed'),

-- Arabic (ar)
('Closed', 'ar', 'مغلق'),

-- French (fr)
('Closed', 'fr', 'Fermé'),

-- Chinese (zh)
('Closed', 'zh', '已关闭'),

-- Appointments Section
-- English (en)
('APPOINTMENTS FOR CUSTOMER', 'en', 'Appointments for Customer'),

-- Arabic (ar)
('APPOINTMENTS FOR CUSTOMER', 'ar', 'مواعيد العميل'),

-- French (fr)
('APPOINTMENTS FOR CUSTOMER', 'fr', 'Rendez-vous du client'),

-- Chinese (zh)
('APPOINTMENTS FOR CUSTOMER', 'zh', '客户预约'),

-- Months of the Year
-- English (en)
('January', 'en', 'January'),
('February', 'en', 'February'),
('March', 'en', 'March'),
('April', 'en', 'April'),
('May', 'en', 'May'),
('June', 'en', 'June'),
('July', 'en', 'July'),
('August', 'en', 'August'),
('September', 'en', 'September'),
('October', 'en', 'October'),
('November', 'en', 'November'),
('December', 'en', 'December'),

-- Arabic (ar)
('January', 'ar', 'يناير'),
('February', 'ar', 'فبراير'),
('March', 'ar', 'مارس'),
('April', 'ar', 'أبريل'),
('May', 'ar', 'مايو'),
('June', 'ar', 'يونيو'),
('July', 'ar', 'يوليو'),
('August', 'ar', 'أغسطس'),
('September', 'ar', 'سبتمبر'),
('October', 'ar', 'أكتوبر'),
('November', 'ar', 'نوفمبر'),
('December', 'ar', 'ديسمبر'),

-- French (fr)
('January', 'fr', 'Janvier'),
('February', 'fr', 'Février'),
('March', 'fr', 'Mars'),
('April', 'fr', 'Avril'),
('May', 'fr', 'Mai'),
('June', 'fr', 'Juin'),
('July', 'fr', 'Juillet'),
('August', 'fr', 'Août'),
('September', 'fr', 'Septembre'),
('October', 'fr', 'Octobre'),
('November', 'fr', 'Novembre'),
('December', 'fr', 'Décembre'),

-- Chinese (zh)
('January', 'zh', '一月'),
('February', 'zh', '二月'),
('March', 'zh', '三月'),
('April', 'zh', '四月'),
('May', 'zh', '五月'),
('June', 'zh', '六月'),
('July', 'zh', '七月'),
('August', 'zh', '八月'),
('September', 'zh', '九月'),
('October', 'zh', '十月'),
('November', 'zh', '十一月'),
('December', 'zh', '十二月'),

-- Assistant Introduction
-- English (en)
('you_are', 'en', 'You are a friendly phone assistant for'),

-- Arabic (ar)
('you_are', 'ar', 'أنت مساعد هاتف ودود لـ'),

-- French (fr)
('you_are', 'fr', 'Vous êtes un assistant téléphonique sympathique pour'),

-- Chinese (zh)
('you_are', 'zh', '您是一个友好的电话助手，为'),

-- Assistant Introduction Instructions
-- English (en)
('intro', 'en', 'Greet callers warmly. Answer questions clearly and briefly. Offer the service name, price, and duration only when asked. Help with bookings by asking what service and time they prefer. \n'),

-- Arabic (ar)
('intro', 'ar', 'رحب بالمتصلين بحرارة. أجب على الأسئلة بوضوح وإيجاز. قدم اسم الخدمة والسعر والمدة فقط عند الطلب. ساعد في الحجوزات بالسؤال عن الخدمة والوقت المفضلين. \n'),

-- French (fr)
('intro', 'fr', 'Accueillez les appelants chaleureusement. Répondez aux questions clairement et brièvement. Proposez le nom du service, le prix et la durée uniquement lorsqu\'on vous le demande. Aidez aux réservations en demandant quel service et à quelle heure ils préfèrent. \n'),

-- Chinese (zh)
('intro', 'zh', '热情地问候来电者。 清晰简洁地回答问题。 仅在被问到时提供服务名称、价格和持续时间。 通过询问他们喜欢什么服务和时间来帮助预订。 \n'),

-- Current Date and Time Instructions
-- English (en)
('current_date_and_time', 'en', 'Use this information to provide time-aware responses, such as suggesting availability later today or referencing specific days (e.g., ''tomorrow'', ''Friday afternoon'').\n'),

-- Arabic (ar)
('current_date_and_time', 'ar', 'استخدم هذه المعلومات لتقديم ردود واعية بالوقت، مثل اقتراح أوقات متاحة لاحقًا اليوم أو الإشارة إلى أيام محددة (مثل ''غدًا''، ''بعد ظهر الجمعة'').\n'),

-- French (fr)
('current_date_and_time', 'fr', 'Utilisez ces informations pour fournir des réponses tenant compte du temps, comme suggérer des disponibilités plus tard dans la journée ou faire référence à des jours spécifiques (par exemple, ''demain'', ''vendredi après-midi'').\n'),

-- Chinese (zh)
('current_date_and_time', 'zh', '使用此信息提供时间感知的响应，例如建议今天晚些时候的空闲时间或参考特定日期（例如“明天”、“周五下午”）。\n'),

-- Unknown Customer Instructions
-- English (en)
('unknown_customer', 'en', 'Name not yet known.\nOnly ask for the customer''s name if they are making a booking.\nWhen the name is provided, call the `update_customer` function as defined in the'),

-- Arabic (ar)
('unknown_customer', 'ar', 'الاسم غير معروف بعد.\nاطلب اسم العميل فقط إذا كان يقوم بحجز.\nعند تقديم الاسم، استدعِ الدالة `update_customer` كما هي معرفة في'),

-- French (fr)
('unknown_customer', 'fr', 'Nom pas encore connu.\nNe demandez le nom du client que s''il effectue une réservation.\nLorsque le nom est fourni, appelez la fonction `update_customer` telle que définie dans le'),

-- Chinese (zh)
('unknown_customer', 'zh', '姓名尚未知。\n仅当客户进行预订时才询问其姓名。\n提供姓名后，调用`update_customer`函数，如'),

-- Appointments for Customer
-- English (en)
('APPOINTMENTS FOR CUSTOMER', 'en', 'APPOINTMENTS FOR CUSTOMER'),

-- Arabic (ar)
('APPOINTMENTS FOR CUSTOMER', 'ar', 'مواعيد العميل'),

-- French (fr)
('APPOINTMENTS FOR CUSTOMER', 'fr', 'RENDEZ-VOUS DU CLIENT'),

-- Chinese (zh)
('APPOINTMENTS FOR CUSTOMER', 'zh', '客户预约'),

-- New translations from translation_script.txt
-- English (en)
('known_customer', 'en', 'When greeting, say: Hi'),
('thanks_for_calling', 'en', 'Thanks for calling'),
('how_can_i_help', 'en', 'How can I help you today?'),

-- Arabic (ar)
('known_customer', 'ar', 'عند التحية، قل: مرحباً'),
('thanks_for_calling', 'ar', 'شكراً لتواصلكم معنا'),
('how_can_i_help', 'ar', 'كيف يمكنني مساعدتك اليوم؟'),

-- French (fr)
('known_customer', 'fr', 'Lors de l''accueil, dites: Bonjour'),
('thanks_for_calling', 'fr', 'Merci d''avoir appelé'),
('how_can_i_help', 'fr', 'Comment puis-je vous aider aujourd''hui?'),

-- Chinese (zh)
('known_customer', 'zh', '问候时说：您好'),
('thanks_for_calling', 'zh', '感谢您的来电'),
('how_can_i_help', 'zh', '今天有什么可以帮您？'),

-- No Appointments Message
-- English (en)
('no_appointments', 'en', 'The Customer Does NOT have any appointments'),

-- Arabic (ar)
('no_appointments', 'ar', 'لا توجد مواعيد حجز للعميل'),

-- French (fr)
('no_appointments', 'fr', 'Le client n''a pas de rendez-vous'),

-- Chinese (zh)
('no_appointments', 'zh', '该客户没有任何预约'),

-- Functions Calling Instructions
-- English (en)
('functions_calling_instructions', 'en', 'Always confirm with the customer before performing any appointment-related action (booking, rescheduling, or canceling).\nOnly proceed if the customer explicitly agrees after you confirm the details.\nThe only exception is `update_customer`, which should be called immediately after the customer provides their name.'),

-- Arabic (ar)
('functions_calling_instructions', 'ar', 'يجب التأكيد مع العميل دائمًا قبل تنفيذ أي إجراء متعلق بالمواعيد (الحجز أو إعادة الجدولة أو الإلغاء).\nتابع فقط إذا وافق العميل صراحة بعد تأكيد التفاصيل.\nالاستثناء الوحيد هو `update_customer`، الذي يجب استدعاؤه فورًا بعد أن يقدم العميل اسمه.'),

-- French (fr)
('functions_calling_instructions', 'fr', 'Confirmez toujours avec le client avant d''effectuer toute action liée à un rendez-vous (réservation, report ou annulation).\nNe procédez que si le client donne son accord explicite après confirmation des détails.\nLa seule exception est `update_customer`, qui doit être appelé immédiatement après que le client a fourni son nom.'),

-- Chinese (zh)
('functions_calling_instructions', 'zh', '在执行任何与预约相关的操作（预订、重新安排或取消）之前，请务必与客户确认。\n只有在您确认详细信息后客户明确同意的情况下才能继续。\n唯一的例外是`update_customer`，它应在客户提供姓名后立即调用。');
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
