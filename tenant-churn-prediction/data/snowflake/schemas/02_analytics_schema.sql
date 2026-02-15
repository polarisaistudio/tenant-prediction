-- ============================================================================
-- Analytics Schema - Star Schema for Churn Prediction
-- Fact tables and dimension tables for analytics
-- ============================================================================

USE SCHEMA TENANT_ANALYTICS.ANALYTICS;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Dimension: Tenants
CREATE OR REPLACE TABLE DIM_TENANTS (
    tenant_key INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    age INTEGER,
    household_size INTEGER,
    annual_income DECIMAL(12,2),
    income_bracket VARCHAR(20),
    employment_status VARCHAR(50),
    account_created_date DATE,
    account_tenure_days INTEGER,
    autopay_enabled BOOLEAN,
    primary_payment_method VARCHAR(50),
    tenant_segment VARCHAR(50),
    effective_date DATE,
    end_date DATE,
    is_current BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension: Properties
CREATE OR REPLACE TABLE DIM_PROPERTIES (
    property_key INTEGER AUTOINCREMENT PRIMARY KEY,
    property_id VARCHAR(50) UNIQUE NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    neighborhood VARCHAR(100),
    square_feet INTEGER,
    sqft_range VARCHAR(20),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    year_built INTEGER,
    property_age INTEGER,
    age_bracket VARCHAR(20),
    property_type VARCHAR(50),
    has_garage BOOLEAN,
    has_yard BOOLEAN,
    has_ac BOOLEAN,
    amenity_score INTEGER,
    condition_rating INTEGER,
    location_score INTEGER,
    school_rating INTEGER,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    effective_date DATE,
    end_date DATE,
    is_current BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension: Date
CREATE OR REPLACE TABLE DIM_DATE (
    date_key INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    day_of_week INTEGER,
    day_name VARCHAR(10),
    day_of_month INTEGER,
    day_of_year INTEGER,
    week_of_year INTEGER,
    month INTEGER,
    month_name VARCHAR(10),
    quarter INTEGER,
    year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER
);

-- Dimension: Market Conditions
CREATE OR REPLACE TABLE DIM_MARKET (
    market_key INTEGER AUTOINCREMENT PRIMARY KEY,
    zip_code VARCHAR(10),
    data_date DATE,
    market_rent_median DECIMAL(10,2),
    vacancy_rate DECIMAL(5,4),
    vacancy_tier VARCHAR(20),
    rent_growth_1yr_pct DECIMAL(5,4),
    rent_growth_tier VARCHAR(20),
    median_hh_income DECIMAL(12,2),
    income_tier VARCHAR(20),
    population_growth_rate DECIMAL(5,4),
    market_health_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Fact: Churn Predictions
CREATE OR REPLACE TABLE FACT_CHURN_PREDICTIONS (
    prediction_key INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_key INTEGER,
    property_key INTEGER,
    lease_id VARCHAR(50),
    prediction_date_key INTEGER,
    lease_end_date_key INTEGER,

    -- Prediction metrics
    churn_probability DECIMAL(5,4),
    risk_score INTEGER,
    risk_level VARCHAR(10),
    predicted_churn BOOLEAN,
    model_version VARCHAR(20),
    confidence_score DECIMAL(5,4),

    -- Lease context
    monthly_rent DECIMAL(10,2),
    lease_term_months INTEGER,
    tenure_months INTEGER,
    days_to_expiration INTEGER,
    renewal_count INTEGER,

    -- Feature values (top contributors)
    avg_days_late DECIMAL(10,2),
    payment_consistency DECIMAL(5,4),
    portal_engagement_score DECIMAL(5,2),
    maintenance_frequency DECIMAL(5,2),
    rent_to_market_ratio DECIMAL(5,4),

    -- Metadata
    predicted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

    FOREIGN KEY (tenant_key) REFERENCES DIM_TENANTS(tenant_key),
    FOREIGN KEY (property_key) REFERENCES DIM_PROPERTIES(property_key),
    FOREIGN KEY (prediction_date_key) REFERENCES DIM_DATE(date_key),
    FOREIGN KEY (lease_end_date_key) REFERENCES DIM_DATE(date_key)
);

-- Fact: Lease Events
CREATE OR REPLACE TABLE FACT_LEASE_EVENTS (
    event_key INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_key INTEGER,
    property_key INTEGER,
    lease_id VARCHAR(50),
    event_date_key INTEGER,

    event_type VARCHAR(50), -- 'NEW', 'RENEWAL', 'TERMINATION', 'EXPIRATION'
    event_reason VARCHAR(100),

    -- Lease metrics at event
    monthly_rent DECIMAL(10,2),
    security_deposit DECIMAL(10,2),
    lease_term_months INTEGER,

    -- Financial impact
    rent_change_amount DECIMAL(10,2),
    rent_change_pct DECIMAL(5,2),

    -- Churn context (if applicable)
    was_predicted_churn BOOLEAN,
    risk_score_at_event INTEGER,
    retention_campaign_sent BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

    FOREIGN KEY (tenant_key) REFERENCES DIM_TENANTS(tenant_key),
    FOREIGN KEY (property_key) REFERENCES DIM_PROPERTIES(property_key),
    FOREIGN KEY (event_date_key) REFERENCES DIM_DATE(date_key)
);

-- Fact: Retention Actions
CREATE OR REPLACE TABLE FACT_RETENTION_ACTIONS (
    action_key INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_key INTEGER,
    property_key INTEGER,
    lease_id VARCHAR(50),
    action_date_key INTEGER,

    action_type VARCHAR(50), -- 'EMAIL', 'CALL', 'INCENTIVE', 'VISIT'
    risk_level_at_action VARCHAR(10),
    risk_score_at_action INTEGER,

    -- Action details
    incentive_offered BOOLEAN,
    incentive_type VARCHAR(50),
    incentive_value DECIMAL(10,2),

    -- Outcome
    action_status VARCHAR(20),
    response_received BOOLEAN,
    response_date_key INTEGER,
    days_to_response INTEGER,

    -- Results
    resulted_in_renewal BOOLEAN,
    cost_of_action DECIMAL(10,2),
    estimated_value DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

    FOREIGN KEY (tenant_key) REFERENCES DIM_TENANTS(tenant_key),
    FOREIGN KEY (property_key) REFERENCES DIM_PROPERTIES(property_key),
    FOREIGN KEY (action_date_key) REFERENCES DIM_DATE(date_key),
    FOREIGN KEY (response_date_key) REFERENCES DIM_DATE(date_key)
);

-- Fact: Payment Behavior
CREATE OR REPLACE TABLE FACT_PAYMENT_BEHAVIOR (
    behavior_key INTEGER AUTOINCREMENT PRIMARY KEY,
    tenant_key INTEGER,
    lease_id VARCHAR(50),
    month_key INTEGER,

    -- Payment metrics
    total_payments INTEGER,
    total_amount DECIMAL(10,2),
    on_time_payments INTEGER,
    late_payments INTEGER,
    avg_days_late DECIMAL(10,2),
    max_days_late INTEGER,
    total_late_fees DECIMAL(10,2),

    -- Behavior indicators
    payment_consistency_score DECIMAL(5,4),
    payment_trend VARCHAR(20), -- 'IMPROVING', 'STABLE', 'DECLINING'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

    FOREIGN KEY (tenant_key) REFERENCES DIM_TENANTS(tenant_key),
    FOREIGN KEY (month_key) REFERENCES DIM_DATE(date_key)
);

-- ============================================================================
-- TRAINING DATA VIEW
-- ============================================================================

CREATE OR REPLACE VIEW CHURN_TRAINING_DATA AS
SELECT
    p.prediction_key,
    p.tenant_key,
    p.property_key,
    p.lease_id,

    -- Target variable
    CASE
        WHEN le.event_type = 'TERMINATION' OR le.event_type = 'EXPIRATION' THEN 1
        WHEN le.event_type = 'RENEWAL' THEN 0
        ELSE NULL
    END AS churned,

    -- Features from prediction
    p.monthly_rent,
    p.tenure_months,
    p.renewal_count,
    p.avg_days_late,
    p.payment_consistency,
    p.portal_engagement_score,
    p.maintenance_frequency,
    p.rent_to_market_ratio,

    -- Tenant features
    t.age,
    t.household_size,
    t.annual_income,
    t.autopay_enabled,

    -- Property features
    prop.square_feet,
    prop.bedrooms,
    prop.bathrooms,
    prop.property_age,
    prop.condition_rating,
    prop.location_score,

    -- Market features
    m.vacancy_rate,
    m.rent_growth_1yr_pct,
    m.market_health_score,

    -- Temporal features
    p.days_to_expiration,
    p.lease_term_months,

    -- Metadata
    p.predicted_at,
    le.event_date_key AS outcome_date_key,

    -- Training set flag (exclude future data)
    CASE WHEN le.event_date_key IS NOT NULL THEN TRUE ELSE FALSE END AS training_set

FROM FACT_CHURN_PREDICTIONS p
LEFT JOIN DIM_TENANTS t ON p.tenant_key = t.tenant_key
LEFT JOIN DIM_PROPERTIES prop ON p.property_key = prop.property_key
LEFT JOIN DIM_MARKET m ON prop.zip_code = m.zip_code
    AND p.prediction_date_key = m.data_date
LEFT JOIN FACT_LEASE_EVENTS le ON p.lease_id = le.lease_id
    AND le.event_type IN ('RENEWAL', 'TERMINATION', 'EXPIRATION')
WHERE t.is_current = TRUE
  AND prop.is_current = TRUE;

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Create clustering keys for performance
ALTER TABLE FACT_CHURN_PREDICTIONS CLUSTER BY (prediction_date_key, risk_level);
ALTER TABLE FACT_LEASE_EVENTS CLUSTER BY (event_date_key, event_type);
ALTER TABLE FACT_RETENTION_ACTIONS CLUSTER BY (action_date_key, action_type);

-- Create search optimization
ALTER TABLE DIM_TENANTS ADD SEARCH OPTIMIZATION ON EQUALITY(tenant_id, email);
ALTER TABLE DIM_PROPERTIES ADD SEARCH OPTIMIZATION ON EQUALITY(property_id, zip_code);

COMMENT ON TABLE FACT_CHURN_PREDICTIONS IS 'Churn prediction results and features';
COMMENT ON TABLE FACT_LEASE_EVENTS IS 'Lease lifecycle events (new, renewal, termination)';
COMMENT ON TABLE FACT_RETENTION_ACTIONS IS 'Retention campaign actions and outcomes';
COMMENT ON VIEW CHURN_TRAINING_DATA IS 'Training dataset for ML model with labeled outcomes';
