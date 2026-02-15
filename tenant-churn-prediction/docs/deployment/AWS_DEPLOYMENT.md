# AWS Production Deployment Guide

Step-by-step guide for deploying the Tenant Churn Prediction system to AWS.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Deployment Steps](#deployment-steps)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)
- [Rollback Procedures](#rollback-procedures)

## Prerequisites

### Required Tools
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Install Terraform
brew install terraform

# Install Docker
brew install --cask docker

# Install kubectl (for EKS, if using)
brew install kubectl
```

### AWS Account Setup
- AWS account with admin access
- AWS CLI configured with credentials
- S3 bucket for Terraform state
- ECR repository for Docker images

## Infrastructure Setup

### 1. Configure Terraform Backend

```bash
cd infrastructure/aws/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
aws_region = "us-west-2"
environment = "production"
project_name = "tenant-churn"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-west-2a", "us-west-2b", "us-west-2c"]

# ECS Configuration
ecs_cluster_name = "tenant-churn-cluster"
ml_service_cpu = 2048
ml_service_memory = 4096
backend_service_cpu = 1024
backend_service_memory = 2048

# Database Configuration
mongodb_atlas_cluster_tier = "M30"
redis_node_type = "cache.r6g.large"

# Domain Configuration
domain_name = "churn.yourcompany.com"
certificate_arn = "arn:aws:acm:us-west-2:..."
EOF
```

### 2. Review Terraform Plan

```bash
# Preview infrastructure changes
terraform plan

# Expected resources:
# - VPC with public/private subnets
# - Application Load Balancer
# - ECS cluster with Fargate
# - ECR repositories
# - RDS (if using PostgreSQL)
# - ElastiCache Redis
# - S3 buckets for models/data
# - CloudWatch Log Groups
# - IAM roles and policies
```

### 3. Apply Infrastructure

```bash
# Create infrastructure
terraform apply

# Save outputs
terraform output > terraform-outputs.json
```

## Deployment Steps

### Step 1: Build and Push Docker Images

```bash
# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Build and tag images
export ECR_REGISTRY=<account-id>.dkr.ecr.us-west-2.amazonaws.com
export IMAGE_TAG=$(git rev-parse --short HEAD)

# ML Service
cd ml-service
docker build -t tenant-churn-ml:$IMAGE_TAG .
docker tag tenant-churn-ml:$IMAGE_TAG \
  $ECR_REGISTRY/tenant-churn-ml:$IMAGE_TAG
docker tag tenant-churn-ml:$IMAGE_TAG \
  $ECR_REGISTRY/tenant-churn-ml:latest
docker push $ECR_REGISTRY/tenant-churn-ml:$IMAGE_TAG
docker push $ECR_REGISTRY/tenant-churn-ml:latest

# Backend API
cd ../backend
docker build -t tenant-churn-backend:$IMAGE_TAG .
docker tag tenant-churn-backend:$IMAGE_TAG \
  $ECR_REGISTRY/tenant-churn-backend:$IMAGE_TAG
docker tag tenant-churn-backend:$IMAGE_TAG \
  $ECR_REGISTRY/tenant-churn-backend:latest
docker push $ECR_REGISTRY/tenant-churn-backend:$IMAGE_TAG
docker push $ECR_REGISTRY/tenant-churn-backend:latest

# Frontend
cd ../frontend
docker build -t tenant-churn-frontend:$IMAGE_TAG .
docker tag tenant-churn-frontend:$IMAGE_TAG \
  $ECR_REGISTRY/tenant-churn-frontend:$IMAGE_TAG
docker tag tenant-churn-frontend:$IMAGE_TAG \
  $ECR_REGISTRY/tenant-churn-frontend:latest
docker push $ECR_REGISTRY/tenant-churn-frontend:$IMAGE_TAG
docker push $ECR_REGISTRY/tenant-churn-frontend:latest
```

### Step 2: Configure Secrets Manager

```bash
# Store sensitive credentials
aws secretsmanager create-secret \
  --name tenant-churn/production/mongodb \
  --secret-string '{"uri":"mongodb+srv://...","password":"..."}'

aws secretsmanager create-secret \
  --name tenant-churn/production/snowflake \
  --secret-string '{"account":"...","user":"...","password":"..."}'

aws secretsmanager create-secret \
  --name tenant-churn/production/sendgrid \
  --secret-string '{"api_key":"SG...."}'

aws secretsmanager create-secret \
  --name tenant-churn/production/jwt \
  --secret-string '{"secret":"..."}'
```

### Step 3: Deploy ECS Services

```bash
# Update ECS task definitions
cd infrastructure/aws

# Deploy ML Service
aws ecs register-task-definition \
  --cli-input-json file://ecs/ml-service-task-def.json

aws ecs update-service \
  --cluster tenant-churn-cluster \
  --service ml-service \
  --task-definition ml-service:latest \
  --desired-count 2 \
  --force-new-deployment

# Deploy Backend API
aws ecs register-task-definition \
  --cli-input-json file://ecs/backend-task-def.json

aws ecs update-service \
  --cluster tenant-churn-cluster \
  --service backend-api \
  --task-definition backend-api:latest \
  --desired-count 3 \
  --force-new-deployment

# Deploy Frontend
aws ecs register-task-definition \
  --cli-input-json file://ecs/frontend-task-def.json

aws ecs update-service \
  --cluster tenant-churn-cluster \
  --service frontend \
  --task-definition frontend:latest \
  --desired-count 2 \
  --force-new-deployment
```

### Step 4: Configure Auto Scaling

```bash
# Backend API Auto Scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/tenant-churn-cluster/backend-api \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --policy-name backend-cpu-scaling \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/tenant-churn-cluster/backend-api \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json

# scaling-policy.json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

### Step 5: Configure Load Balancer

```bash
# Create target groups (if not created by Terraform)
aws elbv2 create-target-group \
  --name tenant-churn-backend-tg \
  --protocol HTTP \
  --port 4000 \
  --vpc-id vpc-... \
  --health-check-path /health \
  --health-check-interval-seconds 30

aws elbv2 create-target-group \
  --name tenant-churn-ml-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-... \
  --health-check-path /health

# Create ALB listeners
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=...
```

### Step 6: Set Up CloudWatch Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name tenant-churn-high-error-rate \
  --alarm-description "Alert when API error rate > 5%" \
  --metric-name 5XXError \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-west-2:...:alerts

# ML service high latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ml-service-high-latency \
  --alarm-description "Alert when prediction latency > 500ms" \
  --metric-name PredictionLatency \
  --namespace TenantChurn/ML \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 500 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-west-2:...:alerts
```

### Step 7: Deploy Snowflake Connection

```bash
# Create Snowflake external stage for S3
snowsql -c production <<EOF
CREATE STORAGE INTEGRATION aws_s3_integration
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = S3
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::...:role/snowflake-s3-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://tenant-churn-data/');

CREATE STAGE tenant_churn_stage
  STORAGE_INTEGRATION = aws_s3_integration
  URL = 's3://tenant-churn-data/';
EOF
```

### Step 8: Configure Informatica

```bash
# Deploy Informatica Cloud Agent (on EC2 or local)
# Configure connections in Informatica Cloud

# MongoDB Connection
Connection Type: MongoDB
Host: <mongodb-atlas-host>
Port: 27017
Database: tenant_churn
Authentication: Username/Password

# Snowflake Connection
Connection Type: Snowflake Data Cloud
Account: <account-name>
Warehouse: TENANT_CHURN_WH
Database: TENANT_ANALYTICS
Schema: RAW

# Schedule ETL workflows
# Run daily at 2 AM UTC
```

## Post-Deployment

### 1. Smoke Tests

```bash
# Test health endpoints
curl https://api.churn.yourcompany.com/health
curl https://ml.churn.yourcompany.com/health

# Test prediction API
curl -X POST https://api.churn.yourcompany.com/api/v1/predictions \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @test-prediction.json

# Expected response: 200 OK with prediction data
```

### 2. Load Testing

```bash
# Run k6 load test
k6 run --vus 100 --duration 5m tests/load/production-test.js

# Monitor CloudWatch during load test
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend-api \
  --statistics Average \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60
```

### 3. Database Migration

```bash
# Run MongoDB migrations
cd backend
npm run db:migrate -- --env production

# Verify Snowflake schema
snowsql -c production -f data/snowflake/migrations/verify.sql
```

### 4. Initial Model Deployment

```bash
# Train production model on full dataset
cd ml-service
python -m src.models.train \
  --data-source snowflake \
  --output-dir /tmp/models

# Upload model to S3
aws s3 cp /tmp/models/xgboost_churn_model.pkl \
  s3://tenant-churn-models/production/v1.0.0/

# Trigger model reload in ML service
curl -X POST https://ml.churn.yourcompany.com/model/reload \
  -H "X-API-Key: $ML_SERVICE_API_KEY"
```

### 5. Configure DNS

```bash
# Update Route 53 (if using)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z... \
  --change-batch file://dns-changes.json

# dns-changes.json
{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "churn.yourcompany.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "Z...",
        "DNSName": "alb-....us-west-2.elb.amazonaws.com",
        "EvaluateTargetHealth": true
      }
    }
  }]
}
```

## Monitoring

### CloudWatch Dashboards

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name TenantChurnProduction \
  --dashboard-body file://dashboards/production-dashboard.json
```

**Key Metrics to Monitor:**
- API request latency (p50, p95, p99)
- Prediction latency
- Error rates (4xx, 5xx)
- ECS CPU/Memory utilization
- Database connection pool usage
- Cache hit rate (Redis)
- Model accuracy drift

### Log Aggregation

```bash
# Query CloudWatch Logs Insights
aws logs start-query \
  --log-group-name /ecs/tenant-churn-backend \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'
```

## Rollback Procedures

### Quick Rollback (Service Level)

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster tenant-churn-cluster \
  --service backend-api \
  --task-definition backend-api:PREVIOUS_VERSION \
  --force-new-deployment

# Monitor rollback
watch -n 5 'aws ecs describe-services \
  --cluster tenant-churn-cluster \
  --services backend-api \
  --query "services[0].deployments"'
```

### Full Rollback (Infrastructure)

```bash
cd infrastructure/aws/terraform

# Checkout previous infrastructure state
git checkout <previous-commit>

# Apply previous configuration
terraform apply

# Rollback database migrations if needed
cd ../../backend
npm run db:rollback -- --env production --steps 1
```

### Model Rollback

```bash
# Revert to previous model version
aws s3 cp \
  s3://tenant-churn-models/production/v0.9.0/xgboost_churn_model.pkl \
  s3://tenant-churn-models/production/current/

# Reload model in ML service
curl -X POST https://ml.churn.yourcompany.com/model/reload
```

## Cost Optimization

### Reserved Capacity
- **ECS Fargate:** Savings Plans (1-year commitment)
- **RDS/ElastiCache:** Reserved Instances
- **Snowflake:** Pre-purchased capacity

### Auto-Scaling Policies
- Scale down non-peak hours (nights/weekends)
- Use Spot instances for batch processing
- Lifecycle policies for S3 (transition to Glacier after 90 days)

### Estimated Monthly Costs (80K properties)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS Fargate | 10 tasks (avg) | $300 |
| ALB | 1 ALB | $25 |
| MongoDB Atlas | M30 cluster | $580 |
| ElastiCache | r6g.large | $180 |
| Snowflake | Small warehouse | $400 |
| S3 | Models + data | $50 |
| CloudWatch | Logs + metrics | $100 |
| Data Transfer | 1TB/month | $90 |
| **Total** | | **~$1,725/month** |

## Security Checklist

- [ ] All secrets stored in AWS Secrets Manager
- [ ] TLS 1.3 enforced on all endpoints
- [ ] VPC security groups restrict traffic
- [ ] IAM roles follow least privilege
- [ ] CloudTrail enabled for audit logs
- [ ] WAF rules configured for DDoS protection
- [ ] Database encryption at rest enabled
- [ ] Automated backups configured
- [ ] MFA required for AWS console access
- [ ] Rotate credentials every 90 days

## Troubleshooting

### Service won't start
```bash
# Check ECS service events
aws ecs describe-services \
  --cluster tenant-churn-cluster \
  --services backend-api

# Check task logs
aws logs tail /ecs/tenant-churn-backend --follow
```

### High latency
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# Review CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --statistics Average \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300
```

---

**Document Version:** 1.0  
**Last Updated:** 2024-02-13  
**Maintained By:** DevOps Team
