-- Walks Tracker Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS walks_tracker;
USE walks_tracker;

-- Activities table: Individual walking activities
CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    external_activity_id BIGINT UNIQUE NOT NULL,
    activity_date DATE NOT NULL,
    activity_name VARCHAR(255),
    distance_miles DECIMAL(10, 2) DEFAULT 0,
    duration_seconds INT DEFAULT 0,
    start_lat DECIMAL(10, 7),
    start_lon DECIMAL(10, 7),
    end_lat DECIMAL(10, 7),
    end_lon DECIMAL(10, 7),
    average_speed_mph DECIMAL(5, 2),
    calories INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_activity_date (activity_date),
    INDEX idx_activity_year (activity_date)
);

-- Daily steps table: Daily step totals
CREATE TABLE IF NOT EXISTS daily_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    step_date DATE UNIQUE NOT NULL,
    steps INT DEFAULT 0,
    goal INT DEFAULT 10000,
    distance_miles DECIMAL(10, 2),
    floors_climbed INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_step_date (step_date)
);

-- Route progress table: Cached progress calculation
CREATE TABLE IF NOT EXISTS route_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT UNIQUE NOT NULL,
    total_distance_miles DECIMAL(10, 2) DEFAULT 0,
    total_walks INT DEFAULT 0,
    current_waypoint_index INT DEFAULT 0,
    current_lat DECIMAL(10, 7),
    current_lon DECIMAL(10, 7),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_progress_year (year)
);

-- Stats cache table: Full stats response caching with data-based invalidation
CREATE TABLE IF NOT EXISTS stats_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT UNIQUE NOT NULL,
    stats_json VARCHAR(4000) NOT NULL,
    data_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stats_year (year)
);
