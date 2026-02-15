# System Architecture

Comprehensive architecture documentation for the Tenant Churn Prediction system.

## Table of Contents
- [Overview](#overview)
- [System Components](#system-components)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)
- [Scalability](#scalability)
- [Security](#security)

## Overview

The Tenant Churn Prediction system is a microservices-based ML platform that predicts tenant churn 90 days before lease expiration and automatically triggers retention workflows.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │ Property Mgr │  │  Analytics   │          │
│  │   (React)    │  │    Portal    │  │    Team      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────────┐
│                    API Gateway Layer                             │
│              Node.js/Express REST API                            │
│         (Authentication, Rate Limiting, Routing)                 │
└─────┬──────────┬──────────┬──────────┬────────────────────┬─────┘
      │          │          │          │                    │
┌─────▼────┐ ┌──▼───┐  ┌───▼────┐ ┌──▼─────────┐  ┌──────▼──────┐
│   ML     │ │Mongo │  │Palantir│ │ Snowflake  │  │   Redis     │
│ Service  │ │  DB  │  │Foundry │ │    DW      │  │   Cache     │
│(FastAPI) │ │      │  │  AIP   │ │            │  │             │
└──────────┘ └──────┘  └────────┘ └────┬───────┘  └─────────────┘
                                        │
                                   ┌────▼────────┐
                                   │ Informatica │
                                   │     ETL     │
                                   └─────────────┘
```

## System Components

### 1. Frontend Layer (React/Next.js 14)

**Technology:** React 18, Next.js 14, TypeScript, Tailwind CSS

**Responsibilities:**
- Render dashboard with real-time churn predictions
- Visualize risk heatmaps (Denver metro)
- Display retention campaign performance
- Provide tenant/lease management interface

**Key Features:**
- Server-side rendering (SSR) for SEO
- Real-time updates via SWR
- Responsive design for mobile property managers
- Interactive maps using Leaflet

**Files:**
- `/frontend/src/app/page.tsx` - Main dashboard
- `/frontend/src/components/` - Reusable React components
- `/frontend/src/hooks/` - Custom hooks for data fetching

### 2. API Gateway (Node.js/Express)

**Technology:** Node.js 20, Express, Mongoose

**Responsibilities:**
- Route requests to appropriate services
- Handle authentication (JWT/Okta)
- Implement rate limiting and security
- Orchestrate retention workflows
- Manage operational database (MongoDB)

**API Structure:**
```
/api/v1/
  ├── /tenants          # Tenant CRUD operations
  ├── /leases           # Lease management
  ├── /predictions      # Churn predictions
  ├── /retention        # Retention campaigns
  └── /analytics        # Analytics queries
```

**Files:**
- `/backend/src/index.js` - Express app initialization
- `/backend/src/routes/` - API route handlers
- `/backend/src/services/` - Business logic layer
- `/backend/src/models/` - Mongoose schemas

### 3. ML Service (Python/FastAPI)

**Technology:** Python 3.11, FastAPI, XGBoost, scikit-learn

**Responsibilities:**
- Train churn prediction models
- Serve real-time predictions via REST API
- Feature engineering pipeline
- Model versioning and A/B testing

**ML Pipeline:**
```
Raw Data → Feature Engineering → Model Training → Prediction API
                                       ↓
                                  Model Registry
                                  (S3 + MLflow)
```

**Key Models:**
- **XGBoost Classifier**: Primary production model (85%+ AUC)
- **Feature Importance**: SHAP values for interpretability

**Files:**
- `/ml-service/src/models/xgboost_model.py` - Model implementation
- `/ml-service/src/features/feature_engineer.py` - Feature pipeline
- `/ml-service/src/api/main.py` - FastAPI application

### 4. Data Layer

#### MongoDB (Operational Database)

**Purpose:** Real-time transactional data

**Collections:**
- `tenants` - Tenant profiles and behavior
- `leases` - Lease contracts and status
- `properties` - Property characteristics
- `payments` - Payment history
- `maintenance` - Maintenance requests
- `retention_actions` - Campaign tracking

**Indexing Strategy:**
```javascript
// High-cardinality indexes
tenants: { tenantId: 1 }, { email: 1 }
leases: { leaseId: 1 }, { endDate: 1, status: 1 }
leases: { 'churnPrediction.riskLevel': 1 }
```

#### Snowflake (Data Warehouse)

**Purpose:** Historical analytics and ML training data

**Architecture:** Medallion Pattern
```
RAW Layer          → Source data as ingested
STAGING Layer      → Cleaned and validated
ANALYTICS Layer    → Business-ready star schema
```

**Star Schema:**
- **Fact Tables:**
  - `FACT_CHURN_PREDICTIONS` - Prediction results
  - `FACT_LEASE_EVENTS` - Lease lifecycle events
  - `FACT_RETENTION_ACTIONS` - Campaign outcomes
  - `FACT_PAYMENT_BEHAVIOR` - Payment patterns

- **Dimension Tables:**
  - `DIM_TENANTS` - Tenant profiles (SCD Type 2)
  - `DIM_PROPERTIES` - Property attributes
  - `DIM_DATE` - Date dimension
  - `DIM_MARKET` - Market conditions

**Files:**
- `/data/snowflake/schemas/01_database_setup.sql`
- `/data/snowflake/schemas/02_analytics_schema.sql`

### 5. Palantir Foundry Integration

**Purpose:** Enterprise data ontology and AIP workflows

**Ontology Objects:**
- `Tenant` - Tenant entity with relationships
- `Property` - Property entity
- `Lease` - Lease contract
- `ChurnPrediction` - Prediction results
- `RetentionAction` - Automated actions

**AIP Workflows:**
1. **High-Risk Workflow:**
   - Alert property manager
   - Schedule concierge call
   - Generate personalized offer
   - Monitor response (48-hour window)
   - Escalate if no response

2. **Medium-Risk Workflow:**
   - Send email campaign
   - Generate incentive offer
   - Monitor engagement
   - Send reminder after 7 days

**Files:**
- `/integrations/palantir/ontology/tenant_churn_ontology.yaml`
- `/integrations/palantir/workflows/retention_workflow.py`

### 6. Informatica PowerCenter (ETL)

**Purpose:** Data integration from multiple sources

**ETL Workflows:**
1. **Property Management System → Snowflake**
   - Extract: Property, tenant, lease data
   - Transform: Data cleansing, standardization
   - Load: RAW → STAGING → ANALYTICS

2. **Market Data API → Snowflake**
   - Extract: Zillow, Rentometer API
   - Transform: Zip code aggregation
   - Load: Market trend data

3. **MongoDB → Snowflake Sync**
   - Extract: Real-time operational data
   - Transform: Denormalization for analytics
   - Load: Incremental updates

**Files:**
- `/data/informatica/mappings/` - ETL mappings
- `/data/informatica/workflows/` - Workflow definitions

### 7. Looker (Business Intelligence)

**Purpose:** Self-service analytics and reporting

**LookML Models:**
- `tenant_churn.model` - Primary analytics model
- Explores: churn_predictions, lease_events, retention_campaigns

**Dashboards:**
- Executive Summary - High-level KPIs
- Risk Analysis - Tenant risk distribution
- Campaign Performance - Retention ROI
- Property Manager - Property-level insights

**Files:**
- `/integrations/looker/models/tenant_churn.model.lkml`
- `/integrations/looker/views/churn_predictions.view.lkml`

## Data Flow

### Prediction Flow

```
1. Scheduled Job (Cron) triggers prediction workflow
   ↓
2. Backend API fetches leases expiring in 90 days from MongoDB
   ↓
3. API calls ML Service with tenant/property/lease data
   ↓
4. ML Service:
   - Loads trained XGBoost model
   - Engineers features from raw data
   - Generates predictions with confidence scores
   ↓
5. Backend API:
   - Updates lease documents with predictions
   - Triggers retention workflows for high-risk
   - Logs predictions to Snowflake
   ↓
6. Palantir AIP (if enabled):
   - Creates automated retention workflows
   - Triggers actions based on risk level
   ↓
7. Frontend Dashboard:
   - Displays updated risk scores
   - Shows campaign actions in progress
```

### Retention Workflow Flow

```
High-Risk Tenant Detected (Risk Score ≥ 80)
   ↓
┌─────────────────────────────────────────┐
│ Palantir AIP Workflow Initiated         │
├─────────────────────────────────────────┤
│ Step 1: Alert Property Manager (Email)  │
│ Step 2: Schedule Concierge Call         │
│ Step 3: Generate Personalized Offer     │
│ Step 4: Send Retention Email (SendGrid) │
│ Step 5: Monitor Response (48 hours)     │
└────────┬───────────┬────────────────────┘
         │           │
    [Response]  [No Response]
         │           │
    ┌────▼────┐  ┌───▼──────────────┐
    │ Process │  │ Escalate to      │
    │ Renewal │  │ Regional Manager │
    └─────────┘  └──────────────────┘
```

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2 | UI framework |
| Next.js | 14.1 | SSR framework |
| TypeScript | 5.3 | Type safety |
| Tailwind CSS | 3.4 | Styling |
| Leaflet | 1.9 | Map visualization |
| Recharts | 2.12 | Data visualization |
| SWR | 2.2 | Data fetching |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | 20 | Runtime |
| Express | 4.18 | Web framework |
| Mongoose | 8.2 | MongoDB ODM |
| JWT | 9.0 | Authentication |
| Bull | 4.12 | Job queue |
| Redis | 4.6 | Caching |

### ML Service
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Language |
| FastAPI | 0.110 | API framework |
| XGBoost | 2.0 | ML model |
| scikit-learn | 1.4 | ML utilities |
| Pandas | 2.2 | Data manipulation |
| MLflow | 2.11 | Model tracking |

### Data & Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| MongoDB | 7 | Operational DB |
| Snowflake | Latest | Data warehouse |
| Palantir Foundry | Latest | Ontology & AIP |
| Informatica | PowerCenter | ETL |
| Looker | Latest | BI platform |
| Docker | 24+ | Containerization |
| AWS ECS | - | Container orchestration |
| Terraform | 1.7 | Infrastructure as code |

## Design Decisions

### 1. Microservices Architecture

**Decision:** Separate ML service from backend API

**Rationale:**
- Independent scaling (ML service requires more compute)
- Different tech stacks (Python for ML, Node.js for API)
- Isolated deployments and updates
- Clear separation of concerns

### 2. XGBoost as Primary Model

**Decision:** Use XGBoost over deep learning

**Rationale:**
- Excellent performance on tabular data (85%+ AUC)
- Fast inference (<50ms per prediction)
- Interpretable feature importance
- Lower compute requirements
- Proven in production at scale

### 3. MongoDB for Operational Data

**Decision:** Use MongoDB instead of PostgreSQL

**Rationale:**
- Flexible schema for evolving data models
- Native JSON support for API responses
- Horizontal scaling via sharding
- Fast writes for real-time predictions
- Geospatial indexing for property locations

### 4. Snowflake for Analytics

**Decision:** Snowflake over Redshift/BigQuery

**Rationale:**
- Zero-maintenance warehouse
- Automatic scaling (storage separate from compute)
- Time travel for data versioning
- Native semi-structured data support
- Easy integration with Looker

### 5. Palantir AIP for Workflows

**Decision:** Use Palantir AIP for retention automation

**Rationale:**
- Ontology-driven data model
- Built-in workflow engine
- AI-powered decision making
- Enterprise-grade audit trails
- Seamless integration with Foundry

## Scalability

### Current Capacity
- **80,000+ properties** managed
- **~10,000 predictions/day** (leases in 90-day window)
- **<100ms** prediction latency (p95)
- **99.9%** API uptime SLA

### Scaling Strategy

#### Horizontal Scaling
```
┌─────────────────┐
│ Load Balancer   │
│   (AWS ALB)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│ API  │  │ API  │  (Auto-scaling group)
│ Pod  │  │ Pod  │  (2-10 instances)
└──────┘  └──────┘
```

#### Database Scaling
- **MongoDB:** Sharding by `property_id` (geographic distribution)
- **Snowflake:** Warehouse auto-scaling (Small → 2XL)
- **Redis:** Cluster mode for caching

#### ML Service Scaling
- **Batch Predictions:** Asynchronous job queue (Bull + Redis)
- **Real-time:** Multiple model replicas behind load balancer
- **Model Serving:** A/B testing with traffic splitting

### Performance Optimization

#### Caching Strategy
```
┌─────────────┐
│   Browser   │  (1 hour cache for dashboard data)
└──────┬──────┘
       │
┌──────▼──────┐
│    Redis    │  (15 min cache for predictions)
└──────┬──────┘
       │
┌──────▼──────┐
│   MongoDB   │  (Indexed queries <10ms)
└─────────────┘
```

#### Database Indexes
- Compound indexes on frequent query patterns
- Partial indexes for active leases
- TTL indexes for expired sessions

## Security

### Authentication & Authorization

#### API Authentication
- **JWT tokens** with 24-hour expiration
- **Okta SSO** integration for enterprise users
- **API keys** for service-to-service communication

#### Role-Based Access Control (RBAC)
```
Roles:
- Admin: Full system access
- Property Manager: View/edit assigned properties
- Analyst: Read-only analytics access
- System: Service account for automated jobs
```

### Data Security

#### Encryption
- **At Rest:** AES-256 encryption (MongoDB, Snowflake, S3)
- **In Transit:** TLS 1.3 for all API communications
- **PII Data:** Field-level encryption for sensitive fields

#### Compliance
- **GDPR:** Tenant data retention policies (7 years)
- **SOC 2:** Audit logging of all data access
- **Data Residency:** US-based infrastructure only

### Network Security

```
┌────────────────────────────────────┐
│         Internet Gateway           │
└────────────┬───────────────────────┘
             │
┌────────────▼───────────────────────┐
│  AWS WAF + Shield (DDoS Protection)│
└────────────┬───────────────────────┘
             │
┌────────────▼───────────────────────┐
│     Application Load Balancer      │
└────────────┬───────────────────────┘
             │
        ┌────┴────┐
        │         │
┌───────▼──┐  ┌──▼────────┐
│ Public   │  │  Private  │
│ Subnet   │  │  Subnet   │
│          │  │           │
│ Frontend │  │ Backend   │
│          │  │ MongoDB   │
│          │  │ ML Service│
└──────────┘  └───────────┘
```

### Security Best Practices

1. **Secrets Management:** AWS Secrets Manager for credentials
2. **API Rate Limiting:** 100 requests/15min per IP
3. **Input Validation:** Joi schemas for all API inputs
4. **SQL Injection Prevention:** Parameterized queries
5. **XSS Prevention:** Content Security Policy headers
6. **Dependency Scanning:** Snyk for vulnerability detection

## Monitoring & Observability

### Metrics (Prometheus + Grafana)
- **API Performance:** Request latency, throughput, error rate
- **ML Service:** Prediction latency, model accuracy drift
- **Database:** Query performance, connection pool usage
- **Business:** Churn rate, campaign ROI, retention rate

### Logging (CloudWatch)
- **Structured Logging:** JSON format with correlation IDs
- **Log Levels:** ERROR, WARN, INFO, DEBUG
- **Retention:** 90 days standard, 1 year for audit logs

### Alerting
- **PagerDuty** integration for critical alerts
- **Slack** notifications for warnings
- **Email** for daily digest reports

---

**Document Version:** 1.0  
**Last Updated:** 2024-02-13  
**Maintained By:** Engineering Team
