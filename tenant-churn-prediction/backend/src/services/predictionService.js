/**
 * Prediction Service
 * Integrates with ML service for churn predictions
 */
const axios = require('axios');
const logger = require('../utils/logger');
const Lease = require('../models/Lease');

class PredictionService {
  constructor() {
    this.mlServiceUrl = process.env.ML_SERVICE_URL || 'http://localhost:8000';
  }

  /**
   * Get churn prediction for a single tenant
   */
  async predictSingleTenant(tenantData) {
    try {
      const response = await axios.post(
        `${this.mlServiceUrl}/predict`,
        {
          tenants: [tenantData],
          include_explanation: true
        },
        {
          timeout: 30000,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      return response.data[0];
    } catch (error) {
      logger.error('ML service prediction error:', error.message);
      throw new Error(`Prediction failed: ${error.message}`);
    }
  }

  /**
   * Batch prediction for multiple tenants
   */
  async predictBatch(tenantsData) {
    try {
      const response = await axios.post(
        `${this.mlServiceUrl}/predict`,
        {
          tenants: tenantsData,
          include_explanation: false
        },
        {
          timeout: 60000,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      return response.data;
    } catch (error) {
      logger.error('Batch prediction error:', error.message);
      throw new Error(`Batch prediction failed: ${error.message}`);
    }
  }

  /**
   * Predict churn for all leases in renewal window (90 days)
   */
  async predictRenewalWindow() {
    try {
      logger.info('Starting renewal window predictions...');

      // Get all leases expiring in next 90 days
      const leases = await Lease.findInRenewalWindow()
        .populate('tenantId propertyId');

      logger.info(`Found ${leases.length} leases in renewal window`);

      if (leases.length === 0) {
        return { predictedCount: 0, results: [] };
      }

      // Prepare tenant data for prediction
      const tenantsData = leases.map(lease => this.prepareTenantData(lease));

      // Get predictions from ML service
      const predictions = await this.predictBatch(tenantsData);

      // Update leases with predictions
      const updatePromises = predictions.map((prediction, index) => {
        const lease = leases[index];
        return lease.updateChurnPrediction({
          churn_probability: prediction.churn_probability,
          risk_score: prediction.risk_score,
          risk_level: prediction.risk_level,
          predicted_churn: prediction.predicted_churn,
          model_version: prediction.model_version || '1.0.0'
        });
      });

      await Promise.all(updatePromises);

      logger.info(`Updated ${predictions.length} lease predictions`);

      return {
        predictedCount: predictions.length,
        results: predictions.map((pred, idx) => ({
          leaseId: leases[idx].leaseId,
          tenantId: leases[idx].tenantId.tenantId,
          ...pred
        }))
      };

    } catch (error) {
      logger.error('Renewal window prediction error:', error);
      throw error;
    }
  }

  /**
   * Prepare tenant data for ML model
   */
  prepareTenantData(lease) {
    const tenant = lease.tenantId;
    const property = lease.propertyId;

    return {
      tenant_id: tenant.tenantId,
      property_id: property.propertyId,
      lease_id: lease.leaseId,

      // Tenant behavior
      avg_days_late: lease.avgDaysLate || 0,
      max_days_late: lease.maxDaysLate || 0,
      payment_count: lease.paymentCount || lease.tenureMonths || 12,
      autopay_enabled: tenant.autopayEnabled || false,
      portal_login_count: tenant.portalLoginCount || 0,
      maintenance_count: lease.maintenanceCount || 0,
      complaint_count: tenant.complaintCount || 0,
      tenure_months: lease.tenureMonths || 12,

      // Property characteristics
      square_feet: property.squareFeet || 1500,
      bedrooms: property.bedrooms || 3,
      bathrooms: property.bathrooms || 2.0,
      year_built: property.yearBuilt || 2010,
      location_score: property.locationScore || 7,
      has_garage: property.hasGarage || false,
      property_condition: property.conditionRating || 4,

      // Financial
      monthly_rent: lease.monthlyRent || 2000,
      annual_income: tenant.annualIncome || null,
      last_rent_increase_pct: lease.lastRentIncreasePct || 0.03,
      payment_method: tenant.primaryPaymentMethod || 'ach',

      // Market data
      market_rent_median: property.marketRentMedian || 2100,
      vacancy_rate: property.neighborhoodVacancyRate || 0.05,
      rent_growth_1yr_pct: property.rentGrowth1YrPct || 0.03,

      // Temporal
      lease_end_date: lease.endDate.toISOString(),
      lease_term_months: lease.leaseTermMonths || 12
    };
  }

  /**
   * Get feature importance from ML model
   */
  async getFeatureImportance() {
    try {
      const response = await axios.get(`${this.mlServiceUrl}/model/features`);
      return response.data;
    } catch (error) {
      logger.error('Feature importance fetch error:', error.message);
      throw error;
    }
  }

  /**
   * Get model metadata and performance metrics
   */
  async getModelInfo() {
    try {
      const response = await axios.get(`${this.mlServiceUrl}/model/info`);
      return response.data;
    } catch (error) {
      logger.error('Model info fetch error:', error.message);
      throw error;
    }
  }

  /**
   * Trigger model reload after retraining
   */
  async reloadModel() {
    try {
      const response = await axios.post(`${this.mlServiceUrl}/model/reload`);
      logger.info('ML model reloaded successfully');
      return response.data;
    } catch (error) {
      logger.error('Model reload error:', error.message);
      throw error;
    }
  }

  /**
   * Health check for ML service
   */
  async checkMLServiceHealth() {
    try {
      const response = await axios.get(`${this.mlServiceUrl}/health/ready`, {
        timeout: 5000
      });
      return response.data;
    } catch (error) {
      logger.error('ML service health check failed:', error.message);
      return { status: 'unhealthy', error: error.message };
    }
  }

  /**
   * Get risk summary statistics
   */
  async getRiskSummary() {
    try {
      const [highRisk, mediumRisk, lowRisk, total] = await Promise.all([
        Lease.countDocuments({
          status: 'active',
          'churnPrediction.riskLevel': 'HIGH'
        }),
        Lease.countDocuments({
          status: 'active',
          'churnPrediction.riskLevel': 'MEDIUM'
        }),
        Lease.countDocuments({
          status: 'active',
          'churnPrediction.riskLevel': 'LOW'
        }),
        Lease.countDocuments({ status: 'active' })
      ]);

      return {
        total_active_leases: total,
        high_risk_count: highRisk,
        medium_risk_count: mediumRisk,
        low_risk_count: lowRisk,
        high_risk_percentage: total > 0 ? (highRisk / total) * 100 : 0,
        unpredicted_count: total - (highRisk + mediumRisk + lowRisk)
      };
    } catch (error) {
      logger.error('Risk summary error:', error);
      throw error;
    }
  }
}

module.exports = new PredictionService();
