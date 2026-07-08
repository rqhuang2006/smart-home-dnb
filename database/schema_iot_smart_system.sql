-- Smart Home DnB IoT database schema
-- Only project tables are included here. Do not export phpMyAdmin/system databases.

CREATE DATABASE IF NOT EXISTS `iot_smart_system`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `iot_smart_system`;

CREATE TABLE IF NOT EXISTS `device_info` (
  `device_id` varchar(32) NOT NULL COMMENT 'Unique device id',
  `device_type` enum('temperature','light','door_window') NOT NULL COMMENT 'Device type',
  `device_name` varchar(50) NOT NULL COMMENT 'Device name',
  `location` varchar(100) NOT NULL COMMENT 'Install location',
  `is_online` tinyint(4) DEFAULT 1 COMMENT '1 online, 0 offline',
  `create_time` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Device metadata';

CREATE TABLE IF NOT EXISTS `device_realtime` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(32) NOT NULL,
  `sensor_value` float NOT NULL COMMENT 'Temperature, light brightness 0-100, or door/window 0/1',
  `update_time` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_device` (`device_id`),
  CONSTRAINT `device_realtime_ibfk_1`
    FOREIGN KEY (`device_id`) REFERENCES `device_info` (`device_id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Latest device data';

CREATE TABLE IF NOT EXISTS `device_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(32) NOT NULL,
  `sensor_value` float NOT NULL,
  `report_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_dev_time` (`device_id`,`report_time`),
  CONSTRAINT `device_history_ibfk_1`
    FOREIGN KEY (`device_id`) REFERENCES `device_info` (`device_id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Device history data';

CREATE TABLE IF NOT EXISTS `control_log` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `device_id` varchar(32) NOT NULL,
  `operate_detail` varchar(200) NOT NULL,
  `operate_time` datetime DEFAULT current_timestamp(),
  `operator` varchar(50) DEFAULT 'frontend_gui',
  PRIMARY KEY (`log_id`),
  KEY `device_id` (`device_id`),
  CONSTRAINT `control_log_ibfk_1`
    FOREIGN KEY (`device_id`) REFERENCES `device_info` (`device_id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Device control log';

CREATE TABLE IF NOT EXISTS `ai_recording` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `ai_mode` enum('face','yolo') NOT NULL,
  `related_device` varchar(32) DEFAULT NULL,
  `rec_result` text NOT NULL,
  `trigger_action` varchar(100) DEFAULT NULL,
  `rec_time` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `related_device` (`related_device`),
  CONSTRAINT `ai_recording_ibfk_1`
    FOREIGN KEY (`related_device`) REFERENCES `device_info` (`device_id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI recognition event log';

CREATE TABLE IF NOT EXISTS `face_auth_user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(50) NOT NULL,
  `face_file_path` varchar(255) DEFAULT NULL COMMENT 'Face image file path',
  `auth_status` tinyint(4) DEFAULT 1 COMMENT '1 authorized, 0 unauthorized',
  `create_time` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_name` (`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Face authorization users';

INSERT INTO `device_info`
  (`device_id`, `device_type`, `device_name`, `location`, `is_online`)
VALUES
  ('temp_001', 'temperature', 'Living room temperature sensor', 'Living room', 1),
  ('light_001', 'light', 'Living room main light', 'Living room ceiling', 1),
  ('door_001', 'door_window', 'Entrance door', 'Entrance', 1),
  ('win_001', 'door_window', 'Bedroom window', 'Bedroom', 1)
ON DUPLICATE KEY UPDATE
  `device_name` = VALUES(`device_name`),
  `location` = VALUES(`location`),
  `is_online` = VALUES(`is_online`);

INSERT INTO `face_auth_user`
  (`user_name`, `face_file_path`, `auth_status`)
VALUES
  ('authorized_user_1', 'face/user1.jpg', 1),
  ('authorized_user_2', 'face/user2.jpg', 1),
  ('stranger', 'face/stranger.jpg', 0)
ON DUPLICATE KEY UPDATE
  `face_file_path` = VALUES(`face_file_path`),
  `auth_status` = VALUES(`auth_status`);
