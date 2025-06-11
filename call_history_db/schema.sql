-- Call History Database Schema
-- This file contains the complete schema for call history functionality

-- Make sure we're using the call_history database
USE `call_history`;

-- Drop existing tables if they exist (for clean initialization)
DROP TABLE IF EXISTS `call_meta`;

-- Table to store call metadata
CREATE TABLE IF NOT EXISTS `call_meta` (
    `call_sid` VARCHAR(50) NOT NULL COMMENT 'Unique identifier for the call from the telephony provider',
    `meta` JSON NOT NULL COMMENT 'JSON object containing call metadata',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'When the call record was first created',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'When the call record was last updated',
    PRIMARY KEY (`call_sid`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Stores call metadata with call_sid as primary key';

-- Add comments to explain the JSON structure
-- The meta JSON typically includes:
-- {
--     "from": "+1234567890",
--     "to": "+1987654321",
--     "status": "completed",
--     "duration": "120",
--     "direction": "inbound|outbound",
--     "recording_url": "https://example.com/recording.mp3",
--     "caller_name": "Caller Name",
--     "start_time": "2023-01-01T12:00:00Z",
--     "end_time": "2023-01-01T12:02:00Z",
--     "price": "0.0100",
--     "price_unit": "USD",
--     "error_code": null,
--     "error_message": null,
--     "custom_data": {}
-- }
