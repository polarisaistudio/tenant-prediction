-- ============================================================================
-- Snowflake Database Setup for Tenant Churn Prediction
-- Medallion Architecture: RAW → STAGING → ANALYTICS
-- ============================================================================

-- Create database
CREATE DATABASE IF NOT EXISTS TENANT_ANALYTICS;

-- Create schemas for medallion architecture
CREATE SCHEMA IF NOT EXISTS TENANT_ANALYTICS.RAW;
CREATE SCHEMA IF NOT EXISTS TENANT_ANALYTICS.STAGING;
CREATE SCHEMA IF NOT EXISTS TENANT_ANALYTICS.ANALYTICS;

-- Create warehouse for compute
CREATE WAREHOUSE IF NOT EXISTS TENANT_CHURN_WH
  WITH WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for tenant churn analytics';

-- Set default context
USE WAREHOUSE TENANT_CHURN_WH;
USE DATABASE TENANT_ANALYTICS;

-- ============================================================================
-- RAW SCHEMA - Data as ingested from source systems
-- ============================================================================
USE SCHEMA RAW;

-- Raw Tenants Table
CREATE OR REPLACE TABLE RAW_TENANTS (
    tenant_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    date_of_birth DATE,
    household_size INTEGER,
    annual_income DECIMAL(12,2),
    employment_status VARCHAR(50),
    account_created_at TIMESTAMP,
    portal_login_count INTEGER,
    last_login_at TIMESTAMP,
    autopay_enabled BOOLEAN,
    primary_payment_method VARCHAR(50),
    avg_response_time_hours DECIMAL(10,2),
    complaint_count INTEGER,
    status VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50)
);

-- Raw Properties Table
CREATE OR REPLACE TABLE RAW_PROPERTIES (
    property_id VARCHAR(50) PRIMARY KEY,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    square_feet INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    year_built INTEGER,
    property_type VARCHAR(50),
    has_garage BOOLEAN,
    has_yard BOOLEAN,
    has_ac BOOLEAN,
    condition_rating INTEGER,
    location_score INTEGER,
    school_rating INTEGER,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50)
);

-- Raw Leases Table
CREATE OR REPLACE TABLE RAW_LEASES (
    lease_id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50),
    property_id VARCHAR(50),
    start_date DATE,
    end_date DATE,
    lease_term_months INTEGER,
    monthly_rent DECIMAL(10,2),
    security_deposit DECIMAL(10,2),
    renewal_status VARCHAR(50),
    renewal_count INTEGER,
    last_rent_increase_pct DECIMAL(5,2),
    status VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50)
);

-- Raw Payments Table
CREATE OR REPLACE TABLE RAW_PAYMENTS (
    payment_id VARCHAR(50) PRIMARY KEY,
    lease_id VARCHAR(50),
    payment_date DATE,
    amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    days_late INTEGER,
    late_fee DECIMAL(10,2),
    status VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50)
);

-- Raw Maintenance Requests Table
CREATE OR REPLACE TABLE RAW_MAINTENANCE (
    request_id VARCHAR(50) PRIMARY KEY,
    property_id VARCHAR(50),
    lease_id VARCHAR(50),
    request_date DATE,
    request_type VARCHAR(100),
    priority VARCHAR(20),
    status VARCHAR(50),
    resolution_date DATE,
    resolution_days INTEGER,
    cost DECIMAL(10,2),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_system VARCHAR(50)
);

-- Raw Market Data Table
CREATE OR REPLACE TABLE RAW_MARKET_DATA (
    zip_code VARCHAR(10),
    data_date DATE,
    market_rent_median DECIMAL(10,2),
    vacancy_rate DECIMAL(5,4),
    rent_growth_1yr_pct DECIMAL(5,4),
    rent_growth_3yr_pct DECIMAL(5,4),
    new_listings_30d INTEGER,
    avg_days_on_market INTEGER,
    median_hh_income DECIMAL(12,2),
    population_growth_rate DECIMAL(5,4),
    competitor_count_1mi INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (zip_code, data_date)
);

-- ============================================================================
-- STAGING SCHEMA - Cleaned and validated data
-- ============================================================================
USE SCHEMA STAGING;

-- Staging Tenants (cleaned)
CREATE OR REPLACE TABLE STG_TENANTS AS
SELECT * FROM TENANT_ANALYTICS.RAW.RAW_TENANTS WHERE 1=0;

-- Staging Properties (cleaned)
CREATE OR REPLACE TABLE STG_PROPERTIES AS
SELECT * FROM TENANT_ANALYTICS.RAW.RAW_PROPERTIES WHERE 1=0;

-- Staging Leases (cleaned)
CREATE OR REPLACE TABLE STG_LEASES AS
SELECT * FROM TENANT_ANALYTICS.RAW.RAW_LEASES WHERE 1=0;

-- Staging Payments (cleaned)
CREATE OR REPLACE TABLE STG_PAYMENTS AS
SELECT * FROM TENANT_ANALYTICS.RAW.RAW_PAYMENTS WHERE 1=0;

-- Staging Maintenance (cleaned)
CREATE OR REPLACE TABLE STG_MAINTENANCE AS
SELECT * FROM TENANT_ANALYTICS.RAW.RAW_MAINTENANCE WHERE 1=0;

-- Staging Market Data (cleaned)
CREATE OR REPLACE TABLE STG_MARKET_DATA AS
SELECT * FROM TENANT_ANALYTICS.RAW.RAW_MARKET_DATA WHERE 1=0;

-- ============================================================================
-- Grant permissions
-- ============================================================================
GRANT USAGE ON WAREHOUSE TENANT_CHURN_WH TO ROLE TENANT_ANALYST;
GRANT USAGE ON DATABASE TENANT_ANALYTICS TO ROLE TENANT_ANALYST;
GRANT USAGE ON ALL SCHEMAS IN DATABASE TENANT_ANALYTICS TO ROLE TENANT_ANALYST;
GRANT SELECT ON ALL TABLES IN SCHEMA TENANT_ANALYTICS.RAW TO ROLE TENANT_ANALYST;
GRANT SELECT ON ALL TABLES IN SCHEMA TENANT_ANALYTICS.STAGING TO ROLE TENANT_ANALYST;
GRANT SELECT ON ALL TABLES IN SCHEMA TENANT_ANALYTICS.ANALYTICS TO ROLE TENANT_ANALYST;

COMMENT ON DATABASE TENANT_ANALYTICS IS 'Tenant churn prediction data warehouse';
COMMENT ON SCHEMA RAW IS 'Raw data as ingested from source systems';
COMMENT ON SCHEMA STAGING IS 'Cleaned and validated data';
COMMENT ON SCHEMA ANALYTICS IS 'Business-ready analytics tables and views';
