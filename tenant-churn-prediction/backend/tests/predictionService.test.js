/**
 * Unit Tests for Prediction Service
 */
const predictionService = require('../src/services/predictionService');
const Lease = require('../src/models/Lease');
const axios = require('axios');

jest.mock('axios');
jest.mock('../src/models/Lease');

describe('PredictionService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('predictSingleTenant', () => {
    it('should return prediction for single tenant', async () => {
      const mockTenantData = {
        tenant_id: 'TENANT-001',
        property_id: 'PROP-001',
        monthly_rent: 2500
      };

      const mockResponse = {
        data: [{
          tenant_id: 'TENANT-001',
          churn_probability: 0.75,
          risk_score: 75,
          risk_level: 'MEDIUM',
          predicted_churn: true
        }]
      };

      axios.post.mockResolvedValue(mockResponse);

      const result = await predictionService.predictSingleTenant(mockTenantData);

      expect(result).toBeDefined();
      expect(result.churn_probability).toBe(0.75);
      expect(result.risk_level).toBe('MEDIUM');
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/predict'),
        expect.objectContaining({
          tenants: [mockTenantData],
          include_explanation: true
        }),
        expect.any(Object)
      );
    });

    it('should handle ML service errors', async () => {
      axios.post.mockRejectedValue(new Error('ML service unavailable'));

      await expect(
        predictionService.predictSingleTenant({})
      ).rejects.toThrow('Prediction failed');
    });
  });

  describe('predictBatch', () => {
    it('should handle batch predictions', async () => {
      const mockTenantsData = [
        { tenant_id: 'TENANT-001', monthly_rent: 2500 },
        { tenant_id: 'TENANT-002', monthly_rent: 2000 }
      ];

      const mockResponse = {
        data: [
          { tenant_id: 'TENANT-001', risk_score: 75 },
          { tenant_id: 'TENANT-002', risk_score: 45 }
        ]
      };

      axios.post.mockResolvedValue(mockResponse);

      const result = await predictionService.predictBatch(mockTenantsData);

      expect(result).toHaveLength(2);
      expect(result[0].tenant_id).toBe('TENANT-001');
    });
  });

  describe('prepareTenantData', () => {
    it('should prepare tenant data correctly', () => {
      const mockLease = {
        leaseId: 'LEASE-001',
        monthlyRent: 2500,
        endDate: new Date('2024-12-31'),
        tenureMonths: 24,
        tenantId: {
          tenantId: 'TENANT-001',
          autopayEnabled: true,
          portalLoginCount: 50,
          complaintCount: 0
        },
        propertyId: {
          propertyId: 'PROP-001',
          squareFeet: 1800,
          bedrooms: 3,
          bathrooms: 2.0,
          yearBuilt: 2010
        }
      };

      const result = predictionService.prepareTenantData(mockLease);

      expect(result.tenant_id).toBe('TENANT-001');
      expect(result.monthly_rent).toBe(2500);
      expect(result.autopay_enabled).toBe(true);
      expect(result.square_feet).toBe(1800);
    });
  });

  describe('getRiskSummary', () => {
    it('should return risk summary statistics', async () => {
      Lease.countDocuments
        .mockResolvedValueOnce(150)  // high risk
        .mockResolvedValueOnce(300)  // medium risk
        .mockResolvedValueOnce(550)  // low risk
        .mockResolvedValueOnce(1000); // total

      const result = await predictionService.getRiskSummary();

      expect(result.total_active_leases).toBe(1000);
      expect(result.high_risk_count).toBe(150);
      expect(result.medium_risk_count).toBe(300);
      expect(result.low_risk_count).toBe(550);
      expect(result.high_risk_percentage).toBe(15);
    });
  });

  describe('checkMLServiceHealth', () => {
    it('should return healthy status when ML service is up', async () => {
      const mockHealthResponse = {
        data: {
          status: 'ready',
          model_version: '1.0.0'
        }
      };

      axios.get.mockResolvedValue(mockHealthResponse);

      const result = await predictionService.checkMLServiceHealth();

      expect(result.status).toBe('ready');
      expect(result.model_version).toBe('1.0.0');
    });

    it('should return unhealthy status on error', async () => {
      axios.get.mockRejectedValue(new Error('Connection refused'));

      const result = await predictionService.checkMLServiceHealth();

      expect(result.status).toBe('unhealthy');
      expect(result.error).toBeDefined();
    });
  });
});
