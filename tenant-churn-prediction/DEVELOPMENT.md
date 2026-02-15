# Development Guide

Complete setup and development guide for the Tenant Churn Prediction system.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Running the Application](#running-the-application)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Docker** 24+ & Docker Compose
- **Node.js** 20+ & npm 10+
- **Python** 3.11+
- **Git**

### Required Accounts & Access
- **Snowflake** account with ACCOUNTADMIN role
- **AWS** account with appropriate IAM permissions
- **Palantir Foundry** access (optional, for full integration)
- **SendGrid** API key (for email campaigns)
- **MongoDB Atlas** account (or use local MongoDB via Docker)

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/polarisaistudio/tenant-churn-prediction.git
cd tenant-churn-prediction
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Critical environment variables:**
```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017/tenant_churn

# Snowflake (required for full functionality)
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password

# AWS (required for production deployment)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# ML Service
MODEL_PATH=data/models/xgboost_churn_model.pkl
```

### 3. Initialize Databases

#### MongoDB Setup
```bash
# Start MongoDB via Docker
docker-compose up -d mongodb

# Seed with sample data
npm run db:seed
```

#### Snowflake Setup
```bash
# Connect to Snowflake
snowsql -a <your-account> -u <username>

# Run schema setup
snowsql -f data/snowflake/schemas/01_database_setup.sql
snowsql -f data/snowflake/schemas/02_analytics_schema.sql
```

### 4. Generate Sample Data

```bash
cd scripts/data-generation

# Generate 1,000 sample Denver properties (for testing)
python generate_denver_data.py

# Generate full 80,000 property dataset (for production)
python generate_denver_data.py --full
```

Sample data will be saved to `data/raw/denver_sample/`

### 5. Train ML Model

```bash
cd ml-service

# Install Python dependencies
pip install -r requirements.txt

# Train initial model
python -m src.models.train --data-source local

# Verify model was created
ls data/models/xgboost_churn_model.pkl
```

## Running the Application

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Service URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:4000
- ML Service: http://localhost:8000
- API Documentation: http://localhost:4000/api/docs

### Option 2: Individual Services (for development)

#### Terminal 1: ML Service
```bash
cd ml-service
pip install -r requirements.txt
python -m src.api.main
# Runs on http://localhost:8000
```

#### Terminal 2: Backend API
```bash
cd backend
npm install
npm run dev
# Runs on http://localhost:4000
```

#### Terminal 3: Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

### Option 3: With Monitoring Stack

```bash
# Start with Prometheus and Grafana
docker-compose --profile monitoring up -d

# Access monitoring
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

## Development Workflow

### Making Changes

1. **Create feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes and test**
```bash
# Run tests
npm run test:all

# Run linting
npm run lint
```

3. **Commit and push**
```bash
git add .
git commit -m "feat: description of changes"
git push origin feature/your-feature-name
```

4. **Create pull request**
Follow the PR template and ensure all checks pass.

### Code Style

#### Python (ML Service)
```bash
# Format code
black src/
isort src/

# Lint
flake8 src/
mypy src/
```

#### JavaScript (Backend/Frontend)
```bash
# Format and lint
npm run lint:fix
```

### Database Migrations

#### MongoDB
```bash
cd backend
npm run db:migrate
```

#### Snowflake
```bash
snowsql -f data/snowflake/migrations/V001__migration_name.sql
```

## Testing

### Run All Tests
```bash
npm run test:all
```

### Component-Specific Tests

#### ML Service (Python/pytest)
```bash
cd ml-service
pytest tests/ -v --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

#### Backend API (Node.js/Jest)
```bash
cd backend
npm test -- --coverage
npm run test:watch  # Watch mode
```

#### Frontend (React/Jest)
```bash
cd frontend
npm test
npm run test:watch
```

### Integration Tests
```bash
# Start services first
docker-compose up -d

# Run integration tests
npm run test:integration
```

### Load Testing
```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io

# Run load tests
k6 run tests/load/prediction-load-test.js
```

## Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed
```bash
# Check if MongoDB is running
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb
```

#### 2. ML Model Not Found
```bash
# Train a new model
cd ml-service
python -m src.models.train

# Verify model file exists
ls -lh data/models/
```

#### 3. Port Already in Use
```bash
# Find process using port 4000
lsof -i :4000

# Kill process
kill -9 <PID>

# Or change port in .env
PORT=4001
```

#### 4. Snowflake Connection Timeout
```bash
# Test connection
snowsql -a <account> -u <user>

# Check firewall/network settings
# Ensure Snowflake account is accessible

# Verify credentials in .env
echo $SNOWFLAKE_ACCOUNT
```

#### 5. Docker Out of Memory
```bash
# Increase Docker memory
# Docker Desktop → Preferences → Resources → Memory: 8GB+

# Clean up Docker
docker system prune -a --volumes
```

#### 6. Frontend Build Errors
```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

### Debug Mode

#### Enable Debug Logging
```bash
# .env file
LOG_LEVEL=debug
DEBUG_MODE=true
```

#### ML Service Debug
```bash
cd ml-service
python -m pdb src/api/main.py
```

#### Backend Debug
```bash
cd backend
npm run dev  # Already includes nodemon for auto-reload
```

### Performance Profiling

#### Backend API
```bash
npm install -g clinic
clinic doctor -- node src/index.js
```

#### ML Service
```bash
pip install py-spy
py-spy record -o profile.svg -- python -m src.api.main
```

## Database Management

### Backup MongoDB
```bash
docker-compose exec mongodb mongodump --out /backup
docker cp tenant-churn-mongodb:/backup ./mongodb-backup
```

### Restore MongoDB
```bash
docker cp ./mongodb-backup tenant-churn-mongodb:/backup
docker-compose exec mongodb mongorestore /backup
```

### Snowflake Data Export
```sql
COPY INTO @my_stage/churn_data
FROM TENANT_ANALYTICS.ANALYTICS.FACT_CHURN_PREDICTIONS
FILE_FORMAT = (TYPE = CSV COMPRESSION = GZIP);
```

## Additional Resources

- [API Documentation](docs/api/README.md)
- [Architecture Guide](docs/architecture/ARCHITECTURE.md)
- [Palantir Foundry Integration](docs/deployment/foundry-integration.md)
- [Production Deployment](docs/deployment/DEPLOYMENT.md)

## Getting Help

- **GitHub Issues**: https://github.com/polarisaistudio/tenant-churn-prediction/issues
- **Internal Wiki**: [Link to internal documentation]
- **Team Slack**: #tenant-churn-dev
- **Email**: dev-team@polarisaistudio.com
