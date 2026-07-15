-- Create a table for incoming, untrusted source data
CREATE TABLE IF NOT EXISTS raw_records (
    raw_id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL, -- e.g., 'CRM', 'ERP', 'HRMS'
    external_id VARCHAR(100) NOT NULL, -- The ID from the original system
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create a table for the deduplicated, single source of truth
CREATE TABLE IF NOT EXISTS golden_records (
    golden_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(150),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create a lineage mapping table to connect raw data to golden data
CREATE TABLE IF NOT EXISTS source_mapping (
    mapping_id SERIAL PRIMARY KEY,
    golden_id INT REFERENCES golden_records(golden_id) ON DELETE CASCADE,
    raw_id INT REFERENCES raw_records(raw_id) ON DELETE CASCADE,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score NUMERIC(3, 2) -- How sure our AI engine was (e.g., 0.95)
);