-- Create the call_history database if it doesn't exist
CREATE DATABASE IF NOT EXISTS `call_history`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user for call history
CREATE USER IF NOT EXISTS 'call_user'@'%' IDENTIFIED BY 'call_password';

-- Grant all privileges on call_history to the dedicated user
GRANT ALL PRIVILEGES ON `call_history`.* TO 'call_user'@'%';

-- Make sure the user has the ability to create and modify tables
GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, INDEX ON `call_history`.* TO 'call_user'@'%';

-- Apply the changes
FLUSH PRIVILEGES;
