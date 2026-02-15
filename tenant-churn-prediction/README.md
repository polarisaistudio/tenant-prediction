# Tenant Churn Prediction System

AI-powered tenant retention platform for single-family rental property management. Predicts tenant churn 90 days before lease expiration and auto-triggers targeted retention actions.

## Business Impact

- **80,000+ properties** under management
- **$3,000-$5,000** cost per turnover (vacancy + make-ready + re-leasing)
- **90-day** prediction window for proactive intervention
- **Risk-based** automated retention workflows

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    React/Next.js 14 Dashboard                    │
│           (Tenant Risk Scoring, Retention Campaigns)             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│              Node.js/Express API Gateway                         │
│        (Authentication, Business Logic, Orchestration)           │
└──────┬──────────┬──────────┬──────────┬────────────────────────┘
       │          │          │          │
   ┌───▼──┐   ┌──▼───┐  ┌───▼────┐ ┌──▼─────────┐
   │ ML   │   │Mongo │  │Palantir│ │ Snowflake  │
   │Service│   │  DB  │  │Foundry │ │    DW      │
   └──────┘   └──────┘  └────────┘ └────┬───────┘
                                         │
                                    ┌────▼────────┐
                                    │ Informatica │
                                    │     ETL     │
                                    └─────────────┘
```

### Component Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **ML Service** | Python 3.11, scikit-learn, XGBoost, FastAPI | Churn prediction models & feature engineering |
| **API Gateway** | Node.js 20, Express, Mongoose | Business logic & orchestration |
| **Frontend** | React 18, Next.js 14, TypeScript, Tailwind | Dashboard & retention workflows |
| **Operational DB** | MongoDB 7 | Transactional data & real-time state |
| **Data Warehouse** | Snowflake | Historical analytics & feature store |
| **ETL Pipeline** | Informatica PowerCenter | Data integration & transformation |
| **Ontology** | Palantir Foundry | Entity relationships & AIP workflows |
| **Analytics** | Looker, LookML | Business intelligence & reporting |
| **Infrastructure** | Docker, AWS ECS/Lambda, Terraform | Deployment & orchestration |

## Quick Start

### Prerequisites

- Docker 24+ & Docker Compose
- Node.js 20+ & Python 3.11+
- AWS CLI configured
- Snowflake account & credentials
- Palantir Foundry access (optional for full integration)

### Local Development

```bash
# Clone repository
git clone https://github.com/polarisaistudio/tenant-churn-prediction.git
cd tenant-churn-prediction

# Copy environment templates
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# Initialize databases
npm run db:seed

# Train initial model
cd ml-service && python -m src.models.train

# Access services
# Frontend: http://localhost:3000
# API: http://localhost:4000
# ML Service: http://localhost:8000
```

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to AWS ECS
cd infrastructure/aws
terraform init
terraform apply

# Configure Informatica mappings
# See docs/deployment/informatica-setup.md

# Set up Palantir Foundry integration
# See docs/deployment/foundry-integration.md
```

## Key Features

### 1. Predictive Analytics
- **XGBoost classification** with 85%+ accuracy
- **90-day prediction window** before lease expiration
- **Risk scoring** (0-100) with confidence intervals
- **Feature importance** analysis for interpretability

### 2. Data Integration
- **Snowflake** medallion architecture (RAW → STAGING → ANALYTICS)
- **Informatica** ETL pipelines for multi-source data ingestion
- **MongoDB** for real-time operational data
- **Palantir Ontology** for entity relationship mapping

### 3. Automated Retention Workflows
- **High Risk (80-100)**: Immediate property manager alert + concierge call
- **Medium Risk (50-79)**: Email campaign + renewal incentive offer
- **Low Risk (0-49)**: Standard renewal notice
- **Palantir AIP** automated decision workflows

### 4. Analytics Dashboard
- Real-time churn risk heatmap (Denver metro visualization)
- Cohort analysis by property type, neighborhood, lease term
- Campaign effectiveness tracking
- ROI calculator for retention investments

## Project Structure

```
tenant-churn-prediction/
├── ml-service/              # Python ML models & prediction API
│   ├── src/
│   │   ├── models/          # Model training & evaluation
│   │   ├── features/        # Feature engineering pipelines
│   │   ├── api/             # FastAPI prediction endpoints
│   │   └── utils/           # Shared utilities
│   └── tests/
├── backend/                 # Node.js/Express API gateway
│   ├── src/
│   │   ├── routes/          # REST API endpoints
│   │   ├── services/        # Business logic layer
│   │   ├── models/          # Mongoose schemas
│   │   └── middleware/      # Auth, validation, error handling
│   └── tests/
├── frontend/                # React/Next.js 14 dashboard
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── lib/             # Client utilities
│   └── tests/
├── data/
│   ├── snowflake/           # DW schemas & SQL scripts
│   ├── informatica/         # ETL mappings & workflows
│   └── mongodb/             # NoSQL schemas & migrations
├── integrations/
│   ├── palantir/            # Foundry ontology & AIP workflows
│   └── looker/              # LookML models & dashboards
├── infrastructure/
│   ├── docker/              # Multi-stage Dockerfiles
│   └── aws/                 # CloudFormation, ECS, Lambda configs
├── scripts/
│   ├── data-generation/     # Denver CO sample data generator
│   └── etl/                 # Data pipeline orchestration
└── docs/                    # Architecture & deployment guides
```

## Data Model

### Core Entities (Palantir Ontology)

- **Property**: Single-family home (address, sqft, beds/baths, AMI, built year)
- **Tenant**: Renter profile (demographics, payment history, maintenance requests)
- **Lease**: Contract (start/end dates, rent amount, terms, renewal status)
- **Payment**: Transaction (amount, date, method, late fees)
- **Maintenance**: Service request (type, priority, resolution time)
- **Market**: Neighborhood analytics (vacancy rates, rent trends, demographics)

### Feature Categories

1. **Tenant Behavior** (15 features): Payment timeliness, maintenance frequency, portal engagement
2. **Property Characteristics** (12 features): Age, condition, amenities, location score
3. **Financial** (8 features): Rent-to-income ratio, payment method, auto-pay status
4. **Market Conditions** (10 features): Neighborhood vacancy, rent trends, competitor analysis
5. **Temporal** (5 features): Lease duration, seasonality, tenure length

## Testing

```bash
# Run all tests
npm run test:all

# Component-specific tests
cd ml-service && pytest tests/ --cov
cd backend && npm test
cd frontend && npm test

# Integration tests
npm run test:integration

# Load testing
npm run test:load
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:4000/api/docs
- ML Service: http://localhost:8000/docs

See [docs/api/README.md](docs/api/README.md) for detailed endpoint specifications.

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for development setup, coding standards, and contribution guidelines.

## License

Proprietary - Polaris AI Studio

## Support

- Documentation: [docs/](docs/)
- Issues: https://github.com/polarisaistudio/tenant-churn-prediction/issues
- Email: support@polarisaistudio.com
