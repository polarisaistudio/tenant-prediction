# API Reference

Complete API documentation for the Tenant Churn Prediction system.

## Base URLs

- **Production**: `https://api.churn.yourcompany.com/api/v1`
- **Staging**: `https://staging-api.churn.yourcompany.com/api/v1`
- **Local**: `http://localhost:4000/api/v1`

## Authentication

All API requests require authentication using JWT tokens.

```bash
# Request token
curl -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@company.com","password":"password"}'

# Response
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "24h"
}

# Use token in requests
curl -H "Authorization: Bearer <token>" /api/v1/predictions
```

## Endpoints

### Predictions

#### POST /predictions

Generate churn prediction for one or more tenants.

**Request:**
```json
{
  "leases": ["LEASE-000001", "LEASE-000002"],
  "includeExplanation": true
}
```

**Response:**
```json
{
  "predictions": [
    {
      "leaseId": "LEASE-000001",
      "tenantId": "TENANT-000001",
      "propertyId": "PROP-000001",
      "churnProbability": 0.85,
      "riskScore": 85,
      "riskLevel": "HIGH",
      "predictedChurn": true,
      "confidence": 0.92,
      "explanation": {
        "topFeatures": [
          {
            "feature": "avg_days_late",
            "importance": 0.25,
            "value": 12.5
          },
          {
            "feature": "complaint_count",
            "importance": 0.18,
            "value": 3
          }
        ]
      },
      "predictedAt": "2024-02-13T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### POST /predictions/renewal-window

Predict all leases expiring in the next 90 days.

**Response:**
```json
{
  "predictedCount": 1250,
  "highRiskCount": 150,
  "mediumRiskCount": 400,
  "lowRiskCount": 700,
  "predictions": [...]
}
```

#### GET /predictions/:leaseId

Get existing prediction for a lease.

**Response:**
```json
{
  "leaseId": "LEASE-000001",
  "churnProbability": 0.85,
  "riskScore": 85,
  "riskLevel": "HIGH",
  "predictedAt": "2024-02-13T10:30:00Z",
  "modelVersion": "1.0.0"
}
```

### Retention Campaigns

#### POST /retention/auto-trigger

Automatically trigger retention campaigns based on risk levels.

**Request:**
```json
{
  "riskThresholds": {
    "high": 80,
    "medium": 50
  },
  "dryRun": false
}
```

**Response:**
```json
{
  "highRiskProcessed": 150,
  "mediumRiskProcessed": 400,
  "actionsTrigger": 550,
  "campaigns": [
    {
      "leaseId": "LEASE-000001",
      "actionType": "property-manager-visit",
      "triggeredAt": "2024-02-13T10:30:00Z",
      "status": "pending"
    }
  ]
}
```

#### GET /retention/campaigns

List all retention campaigns.

**Query Parameters:**
- `status` (optional): Filter by status (pending|completed|failed)
- `riskLevel` (optional): Filter by risk level (HIGH|MEDIUM|LOW)
- `startDate` (optional): Filter campaigns after date (ISO 8601)
- `endDate` (optional): Filter campaigns before date
- `limit` (optional): Number of results (default: 50, max: 100)
- `page` (optional): Page number (default: 1)

**Response:**
```json
{
  "campaigns": [
    {
      "campaignId": "CAMP-000001",
      "leaseId": "LEASE-000001",
      "actionType": "email-campaign",
      "riskLevel": "HIGH",
      "triggeredAt": "2024-02-13T10:00:00Z",
      "status": "completed",
      "outcome": "renewal_completed",
      "costOfAction": 50.00,
      "estimatedValue": 4000.00
    }
  ],
  "total": 550,
  "page": 1,
  "totalPages": 11
}
```

#### GET /retention/roi

Get return on investment metrics for retention campaigns.

**Query Parameters:**
- `startDate` (optional): Start date for analysis
- `endDate` (optional): End date for analysis

**Response:**
```json
{
  "totalCampaigns": 550,
  "turnoversAvoided": 440,
  "costSavings": 1760000.00,
  "campaignCosts": 27500.00,
  "netSavings": 1732500.00,
  "roiPercentage": 6300.00,
  "renewalRate": 80.0
}
```

### Analytics

#### GET /analytics/risk-summary

Get distribution of risk levels across active leases.

**Response:**
```json
{
  "totalActiveLeases": 75000,
  "highRiskCount": 3750,
  "highRiskPercentage": 5.0,
  "mediumRiskCount": 15000,
  "mediumRiskPercentage": 20.0,
  "lowRiskCount": 56250,
  "lowRiskPercentage": 75.0,
  "unpredictedCount": 0,
  "estimatedTurnoverCost": 15000000.00
}
```

#### GET /analytics/trends

Get churn prediction trends over time.

**Query Parameters:**
- `timeRange` (optional): 7d|30d|90d|1y (default: 30d)
- `groupBy` (optional): day|week|month (default: day)

**Response:**
```json
{
  "timeRange": "30d",
  "dataPoints": [
    {
      "date": "2024-01-15",
      "averageRiskScore": 45.2,
      "highRiskCount": 120,
      "mediumRiskCount": 380,
      "lowRiskCount": 1500,
      "predictedChurnRate": 0.15
    }
  ]
}
```

#### GET /analytics/feature-importance

Get current model feature importance rankings.

**Response:**
```json
{
  "modelVersion": "1.0.0",
  "features": [
    {
      "feature": "avg_days_late",
      "importance": 0.25,
      "category": "payment_behavior"
    },
    {
      "feature": "complaint_count",
      "importance": 0.18,
      "category": "tenant_behavior"
    },
    {
      "feature": "property_condition",
      "importance": 0.15,
      "category": "property"
    }
  ]
}
```

### Tenants

#### GET /tenants

List all tenants with filtering and pagination.

**Query Parameters:**
- `status` (optional): active|former|applicant
- `search` (optional): Search by name or email
- `limit` (optional): Results per page (default: 50, max: 100)
- `page` (optional): Page number (default: 1)

**Response:**
```json
{
  "tenants": [
    {
      "tenantId": "TENANT-000001",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@email.com",
      "phone": "+1-555-0123",
      "status": "active",
      "currentLeaseId": "LEASE-000001",
      "autopayEnabled": true,
      "portalLoginCount": 45
    }
  ],
  "total": 75000,
  "page": 1,
  "totalPages": 1500
}
```

#### GET /tenants/:tenantId

Get detailed tenant information.

**Response:**
```json
{
  "tenantId": "TENANT-000001",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@email.com",
  "phone": "+1-555-0123",
  "dateOfBirth": "1985-06-15",
  "householdSize": 3,
  "annualIncome": 85000,
  "employmentStatus": "employed",
  "autopayEnabled": true,
  "currentLease": {
    "leaseId": "LEASE-000001",
    "propertyId": "PROP-000001",
    "monthlyRent": 2500,
    "endDate": "2024-12-31",
    "churnPrediction": {
      "riskScore": 85,
      "riskLevel": "HIGH"
    }
  },
  "paymentHistory": {
    "totalPayments": 24,
    "onTimePayments": 18,
    "avgDaysLate": 5.2
  }
}
```

### Leases

#### GET /leases

List all leases with filtering.

**Query Parameters:**
- `status` (optional): active|expired|terminated|renewed
- `renewalStatus` (optional): pending-renewal|renewed|not-renewed
- `riskLevel` (optional): HIGH|MEDIUM|LOW
- `expiringInDays` (optional): Filter leases expiring in N days
- `limit` (optional): Results per page
- `page` (optional): Page number

**Response:**
```json
{
  "leases": [
    {
      "leaseId": "LEASE-000001",
      "tenantId": "TENANT-000001",
      "propertyId": "PROP-000001",
      "startDate": "2023-01-01",
      "endDate": "2024-12-31",
      "monthlyRent": 2500,
      "status": "active",
      "renewalStatus": "pending-renewal",
      "daysToExpiration": 45,
      "churnPrediction": {
        "riskScore": 85,
        "riskLevel": "HIGH",
        "predictedAt": "2024-02-13T10:00:00Z"
      }
    }
  ],
  "total": 75000,
  "page": 1,
  "totalPages": 1500
}
```

#### GET /leases/:leaseId

Get detailed lease information.

**Response:**
```json
{
  "leaseId": "LEASE-000001",
  "tenant": {
    "tenantId": "TENANT-000001",
    "fullName": "John Doe",
    "email": "john.doe@email.com"
  },
  "property": {
    "propertyId": "PROP-000001",
    "address": "123 Main St, Denver, CO 80202",
    "bedrooms": 3,
    "bathrooms": 2.0
  },
  "startDate": "2023-01-01",
  "endDate": "2024-12-31",
  "leaseTermMonths": 24,
  "monthlyRent": 2500,
  "securityDeposit": 5000,
  "renewalCount": 1,
  "status": "active",
  "churnPrediction": {
    "riskScore": 85,
    "riskLevel": "HIGH",
    "churnProbability": 0.85,
    "predictedChurn": true,
    "modelVersion": "1.0.0",
    "predictedAt": "2024-02-13T10:00:00Z"
  },
  "retentionActions": [
    {
      "actionType": "property-manager-visit",
      "triggeredAt": "2024-02-13T10:30:00Z",
      "status": "pending"
    }
  ]
}
```

### Properties

#### GET /properties

List all properties.

**Query Parameters:**
- `city` (optional): Filter by city
- `zipCode` (optional): Filter by ZIP code
- `bedrooms` (optional): Filter by number of bedrooms
- `limit` (optional): Results per page
- `page` (optional): Page number

**Response:**
```json
{
  "properties": [
    {
      "propertyId": "PROP-000001",
      "address": "123 Main St",
      "city": "Denver",
      "state": "CO",
      "zipCode": "80202",
      "neighborhood": "Downtown Denver",
      "squareFeet": 1800,
      "bedrooms": 3,
      "bathrooms": 2.0,
      "yearBuilt": 2010,
      "conditionRating": 4,
      "locationScore": 8,
      "currentLease": {
        "leaseId": "LEASE-000001",
        "tenantName": "John Doe",
        "monthlyRent": 2500
      }
    }
  ],
  "total": 80000,
  "page": 1,
  "totalPages": 1600
}
```

### Model Management

#### GET /model/info

Get ML model metadata and performance metrics.

**Response:**
```json
{
  "modelVersion": "1.0.0",
  "modelType": "XGBoostChurnModel",
  "trainingMetadata": {
    "trainingSamples": 50000,
    "trainingTimeSeconds": 120.5,
    "cvMeanAuc": 0.87,
    "cvStdAuc": 0.02,
    "nFeatures": 50,
    "trainedAt": "2024-02-01T00:00:00Z"
  },
  "performanceMetrics": {
    "accuracy": 0.85,
    "precision": 0.82,
    "recall": 0.88,
    "f1Score": 0.85,
    "rocAuc": 0.90
  }
}
```

#### POST /model/reload

Reload the ML model from disk (after retraining).

**Response:**
```json
{
  "status": "success",
  "message": "Model reloaded",
  "modelVersion": "1.1.0",
  "reloadedAt": "2024-02-13T12:00:00Z"
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "statusCode": 400,
  "timestamp": "2024-02-13T10:00:00Z",
  "path": "/api/v1/predictions"
}
```

### Common Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server issue |
| 503 | Service Unavailable - ML service down |

## Rate Limiting

API requests are rate-limited to prevent abuse:
- **Default**: 100 requests per 15 minutes per IP
- **Authenticated**: 1000 requests per 15 minutes per user

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1707825600
```

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `limit`: Number of results (default: 50, max: 100)
- `page`: Page number (default: 1)

**Response:**
```json
{
  "data": [...],
  "total": 75000,
  "page": 1,
  "totalPages": 1500,
  "limit": 50
}
```

## Webhooks (Coming Soon)

Subscribe to events for real-time notifications:
- `prediction.completed` - New prediction generated
- `campaign.triggered` - Retention campaign started
- `lease.renewed` - Lease renewal completed
- `lease.terminated` - Lease terminated

## Interactive Documentation

Visit the interactive API documentation:
- **Swagger UI**: http://localhost:4000/api/docs
- **ReDoc**: http://localhost:4000/api/redoc

---

**API Version:** 1.0  
**Last Updated:** 2024-02-13
