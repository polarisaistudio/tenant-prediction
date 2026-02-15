# Getting Started

Welcome to the Tenant Churn Prediction system! This guide will help you get up and running quickly.

## Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone https://github.com/polarisaistudio/tenant-churn-prediction.git
cd tenant-churn-prediction

# Copy environment template
cp .env.example .env
```

### 2. Start Services with Docker

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (~2 minutes)
docker-compose ps
```

### 3. Generate Sample Data

```bash
# Generate 1,000 sample properties in Denver
cd scripts/data-generation
python generate_denver_data.py

# Load data into MongoDB
cd ../../backend
npm run db:seed
```

### 4. Train Initial Model

```bash
cd ../ml-service
python -m src.models.train --data-source local
```

### 5. Access the Application

Open your browser:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:4000/api/docs
- **ML Service**: http://localhost:8000/docs

## Project Structure

```
tenant-churn-prediction/
├── ml-service/              # Python ML prediction service
│   ├── src/
│   │   ├── models/          # XGBoost model implementation
│   │   ├── features/        # Feature engineering pipeline
│   │   ├── api/             # FastAPI prediction endpoints
│   │   └── utils/           # Utilities and helpers
│   ├── tests/               # ML service tests
│   └── requirements.txt     # Python dependencies
│
├── backend/                 # Node.js/Express API gateway
│   ├── src/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # Mongoose schemas
│   │   ├── middleware/      # Auth, validation, errors
│   │   └── config/          # Configuration
│   ├── tests/               # Backend tests
│   └── package.json         # Node dependencies
│
├── frontend/                # React/Next.js 14 dashboard
│   ├── src/
│   │   ├── app/             # Next.js pages (app router)
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   ├── tests/               # Frontend tests
│   └── package.json         # Node dependencies
│
├── data/
│   ├── snowflake/           # Snowflake schemas & SQL
│   ├── informatica/         # ETL mappings & workflows
│   └── mongodb/             # MongoDB schemas
│
├── integrations/
│   ├── palantir/            # Foundry ontology & AIP
│   └── looker/              # LookML models & dashboards
│
├── infrastructure/
│   ├── docker/              # Dockerfiles
│   └── aws/                 # CloudFormation, Terraform
│
├── scripts/
│   ├── data-generation/     # Denver sample data generator
│   └── etl/                 # Data pipeline scripts
│
├── docs/
│   ├── architecture/        # System architecture
│   ├── api/                 # API documentation
│   └── deployment/          # Deployment guides
│
├── docker-compose.yml       # Local development setup
├── .env.example             # Environment template
├── README.md                # Project overview
└── DEVELOPMENT.md           # Development guide
```

## Key Concepts

### 1. Churn Prediction

The system predicts tenant churn **90 days before lease expiration** using:
- Payment behavior patterns
- Property characteristics
- Market conditions
- Tenant demographics
- Maintenance history

**Risk Levels:**
- **HIGH (80-100)**: Immediate intervention needed
- **MEDIUM (50-79)**: Email campaign + incentive
- **LOW (0-49)**: Standard renewal notice

### 2. Automated Retention Workflows

**High-Risk Workflow:**
1. Alert property manager
2. Schedule concierge call
3. Generate personalized retention offer
4. Monitor response (48-hour window)
5. Escalate if no response

**Medium-Risk Workflow:**
1. Send retention email campaign
2. Generate incentive offer
3. Monitor engagement
4. Send reminder after 7 days

### 3. Tech Stack Summary

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Next.js 14, TypeScript, Tailwind |
| **Backend** | Node.js 20, Express, MongoDB, Redis |
| **ML Service** | Python 3.11, FastAPI, XGBoost, scikit-learn |
| **Data Warehouse** | Snowflake (medallion architecture) |
| **ETL** | Informatica PowerCenter |
| **Ontology** | Palantir Foundry + AIP |
| **Analytics** | Looker + LookML |
| **Infrastructure** | Docker, AWS ECS, Terraform |

## Common Tasks

### Run Predictions

```bash
# Predict all leases in renewal window (90 days)
curl -X POST http://localhost:4000/api/v1/predictions/renewal-window

# Predict single tenant
curl -X POST http://localhost:4000/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"lease_id": "LEASE-000001"}'
```

### Trigger Retention Campaigns

```bash
# Auto-trigger campaigns for all high-risk tenants
curl -X POST http://localhost:4000/api/v1/retention/auto-trigger
```

### View Analytics

```bash
# Get risk summary
curl http://localhost:4000/api/v1/analytics/risk-summary

# Get campaign ROI
curl http://localhost:4000/api/v1/analytics/retention-roi
```

### Retrain Model

```bash
cd ml-service

# Train on latest data from Snowflake
python -m src.models.train \
  --data-source snowflake \
  --tune  # Optional: hyperparameter tuning
```

## Development Workflow

### 1. Local Development

```bash
# Terminal 1: ML Service
cd ml-service
pip install -r requirements.txt
python -m src.api.main

# Terminal 2: Backend
cd backend
npm install
npm run dev

# Terminal 3: Frontend
cd frontend
npm install
npm run dev
```

### 2. Testing

```bash
# Run all tests
npm run test:all

# Component tests
cd ml-service && pytest tests/ -v
cd backend && npm test
cd frontend && npm test
```

### 3. Code Quality

```bash
# Python formatting
cd ml-service
black src/
flake8 src/

# JavaScript linting
cd backend && npm run lint
cd frontend && npm run lint
```

## Data Pipeline

### ETL Flow

```
Source Systems → Informatica → Snowflake → MongoDB → ML Training
                                  ↓
                             Looker (BI)
```

### Snowflake Layers

1. **RAW**: Source data as ingested
2. **STAGING**: Cleaned and validated
3. **ANALYTICS**: Star schema for BI (fact & dimension tables)

### Key Tables

- `FACT_CHURN_PREDICTIONS` - Prediction results
- `FACT_LEASE_EVENTS` - Renewals/terminations
- `FACT_RETENTION_ACTIONS` - Campaign outcomes
- `DIM_TENANTS`, `DIM_PROPERTIES`, `DIM_DATE` - Dimensions

## API Endpoints

### Predictions
- `POST /api/v1/predictions` - Single prediction
- `POST /api/v1/predictions/batch` - Batch predictions
- `POST /api/v1/predictions/renewal-window` - 90-day window
- `GET /api/v1/predictions/:leaseId` - Get prediction by lease

### Retention
- `POST /api/v1/retention/auto-trigger` - Auto-trigger campaigns
- `GET /api/v1/retention/campaigns` - List campaigns
- `GET /api/v1/retention/roi` - Campaign ROI metrics

### Analytics
- `GET /api/v1/analytics/risk-summary` - Risk distribution
- `GET /api/v1/analytics/trends` - Churn trends over time
- `GET /api/v1/analytics/retention-roi` - Retention ROI

### ML Model
- `GET /health` - Health check
- `POST /predict` - Generate predictions
- `GET /model/info` - Model metadata
- `GET /model/features` - Feature importance
- `POST /model/reload` - Reload trained model

## Environment Variables

### Critical Variables

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017/tenant_churn

# Snowflake
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password

# AWS
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# ML Service
ML_SERVICE_URL=http://localhost:8000
MODEL_PATH=data/models/xgboost_churn_model.pkl

# Campaigns
SENDGRID_API_KEY=SG.your_api_key
CAMPAIGN_EMAIL_ENABLED=true
```

See `.env.example` for complete list.

## Monitoring

### Health Checks

```bash
# All services healthy?
curl http://localhost:4000/health
curl http://localhost:8000/health
curl http://localhost:3000

# MongoDB connected?
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Logs

```bash
# View all logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f ml-service
docker-compose logs -f frontend
```

### Metrics (if monitoring enabled)

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

## Troubleshooting

### Services won't start

```bash
# Check Docker
docker --version
docker-compose --version

# Check ports
lsof -i :3000  # Frontend
lsof -i :4000  # Backend
lsof -i :8000  # ML Service

# View detailed logs
docker-compose logs --tail=100 <service-name>
```

### Model training fails

```bash
# Ensure data exists
ls -lh data/raw/denver_sample/

# Check Python environment
cd ml-service
python --version  # Should be 3.11+
pip list | grep xgboost
```

### Database connection issues

```bash
# Test MongoDB connection
mongosh "mongodb://localhost:27017/tenant_churn"

# Check Snowflake
snowsql -a <account> -u <user>
```

## Next Steps

1. **Customize for your data**: Modify `generate_denver_data.py` for your market
2. **Integrate with your PMS**: Connect to your property management system
3. **Set up Snowflake**: Create data warehouse and run ETL pipelines
4. **Configure Palantir**: Set up Foundry ontology and AIP workflows
5. **Deploy to AWS**: Follow `docs/deployment/AWS_DEPLOYMENT.md`

## Additional Resources

- [Full Documentation](docs/)
- [Development Guide](DEVELOPMENT.md)
- [Architecture Overview](docs/architecture/ARCHITECTURE.md)
- [API Documentation](http://localhost:4000/api/docs)
- [Deployment Guide](docs/deployment/AWS_DEPLOYMENT.md)

## Support

- **Issues**: https://github.com/polarisaistudio/tenant-churn-prediction/issues
- **Email**: support@polarisaistudio.com
- **Slack**: #tenant-churn-dev

---

**Quick Links:**
- [README](README.md) - Project overview
- [DEVELOPMENT](DEVELOPMENT.md) - Detailed development guide
- [ARCHITECTURE](docs/architecture/ARCHITECTURE.md) - System design
- [AWS_DEPLOYMENT](docs/deployment/AWS_DEPLOYMENT.md) - Production deployment

Happy predicting! 🏠📊
