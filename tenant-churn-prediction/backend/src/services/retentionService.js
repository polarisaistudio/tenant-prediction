/**
 * Retention Service
 * Automated retention workflows based on risk levels
 */
const logger = require('../utils/logger');
const Lease = require('../models/Lease');
const emailService = require('./emailService');
const smsService = require('./smsService');
const palantirService = require('./palantirService');

class RetentionService {
  constructor() {
    this.riskThresholds = {
      HIGH: parseInt(process.env.HIGH_RISK_THRESHOLD) || 80,
      MEDIUM: parseInt(process.env.MEDIUM_RISK_THRESHOLD) || 50
    };
  }

  /**
   * Trigger retention workflows for high-risk tenants
   */
  async triggerAutomatedWorkflows() {
    try {
      logger.info('Starting automated retention workflows...');

      // Get all high-risk leases
      const highRiskLeases = await Lease.findHighRisk()
        .populate('tenantId propertyId');

      logger.info(`Found ${highRiskLeases.length} high-risk leases`);

      const results = {
        high_risk_processed: 0,
        medium_risk_processed: 0,
        actions_triggered: 0,
        errors: []
      };

      // Process high-risk leases
      for (const lease of highRiskLeases) {
        try {
          await this.processHighRiskLease(lease);
          results.high_risk_processed++;
          results.actions_triggered++;
        } catch (error) {
          logger.error(`Error processing lease ${lease.leaseId}:`, error);
          results.errors.push({
            leaseId: lease.leaseId,
            error: error.message
          });
        }
      }

      // Get medium-risk leases
      const mediumRiskLeases = await Lease.find({
        status: 'active',
        'churnPrediction.riskLevel': 'MEDIUM'
      }).populate('tenantId propertyId');

      logger.info(`Found ${mediumRiskLeases.length} medium-risk leases`);

      // Process medium-risk leases
      for (const lease of mediumRiskLeases) {
        try {
          await this.processMediumRiskLease(lease);
          results.medium_risk_processed++;
          results.actions_triggered++;
        } catch (error) {
          logger.error(`Error processing lease ${lease.leaseId}:`, error);
          results.errors.push({
            leaseId: lease.leaseId,
            error: error.message
          });
        }
      }

      logger.info('Automated workflows completed:', results);
      return results;

    } catch (error) {
      logger.error('Automated workflow error:', error);
      throw error;
    }
  }

  /**
   * Process high-risk lease (80-100 risk score)
   * Actions: Property manager alert + concierge call + email
   */
  async processHighRiskLease(lease) {
    const tenant = lease.tenantId;
    const property = lease.propertyId;

    logger.info(`Processing high-risk lease: ${lease.leaseId}`);

    // 1. Alert property manager
    await this.alertPropertyManager(lease, tenant, property);

    // 2. Schedule concierge call
    await this.scheduleConciergeCall(lease, tenant);

    // 3. Send retention email
    await this.sendRetentionEmail(lease, tenant, 'high-risk');

    // 4. Create Palantir AIP workflow
    if (process.env.FEATURE_PALANTIR_INTEGRATION === 'true') {
      await palantirService.createRetentionWorkflow(lease, 'HIGH');
    }

    // 5. Record retention action
    await lease.triggerRetentionAction(
      'property-manager-visit',
      'High risk - immediate intervention required'
    );

    return {
      leaseId: lease.leaseId,
      riskLevel: 'HIGH',
      actionsTaken: ['manager-alert', 'concierge-call', 'email', 'aip-workflow']
    };
  }

  /**
   * Process medium-risk lease (50-79 risk score)
   * Actions: Email campaign + renewal incentive offer
   */
  async processMediumRiskLease(lease) {
    const tenant = lease.tenantId;

    logger.info(`Processing medium-risk lease: ${lease.leaseId}`);

    // 1. Send email campaign
    await this.sendRetentionEmail(lease, tenant, 'medium-risk');

    // 2. Generate incentive offer
    const incentive = await this.generateIncentiveOffer(lease);

    // 3. Send incentive email
    await this.sendIncentiveOffer(tenant, incentive);

    // 4. Record retention action
    await lease.triggerRetentionAction(
      'email-campaign',
      `Sent renewal incentive: ${incentive.description}`
    );

    return {
      leaseId: lease.leaseId,
      riskLevel: 'MEDIUM',
      actionsTaken: ['email-campaign', 'incentive-offer'],
      incentive
    };
  }

  /**
   * Alert property manager about high-risk tenant
   */
  async alertPropertyManager(lease, tenant, property) {
    const managerEmail = property.propertyManagerEmail || process.env.DEFAULT_PM_EMAIL;

    if (!managerEmail) {
      logger.warn('No property manager email configured');
      return;
    }

    const emailContent = {
      to: managerEmail,
      subject: `⚠️ HIGH RISK: Tenant ${tenant.fullName} - ${property.address}`,
      template: 'property-manager-alert',
      data: {
        tenantName: tenant.fullName,
        propertyAddress: property.address,
        leaseEndDate: lease.endDate,
        daysToExpiration: lease.daysToExpiration,
        riskScore: lease.churnPrediction.riskScore,
        churnProbability: (lease.churnPrediction.churnProbability * 100).toFixed(1),
        tenantPhone: tenant.phone,
        tenantEmail: tenant.email,
        actionRequired: 'Schedule in-person visit within 48 hours'
      }
    };

    await emailService.send(emailContent);
    logger.info(`Property manager alert sent for lease ${lease.leaseId}`);
  }

  /**
   * Schedule concierge call for high-risk tenant
   */
  async scheduleConciergeCall(lease, tenant) {
    // In production, integrate with call scheduling system
    logger.info(`Scheduling concierge call for tenant ${tenant.tenantId}`);

    // Create task in CRM or scheduling system
    // For now, just log and send notification
    if (process.env.CAMPAIGN_SMS_ENABLED === 'true') {
      await smsService.send({
        to: tenant.phone,
        message: `Hi ${tenant.firstName}, we'd love to discuss your upcoming lease renewal. Our team will call you within 24 hours. Reply STOP to opt out.`
      });
    }
  }

  /**
   * Send retention email based on risk level
   */
  async sendRetentionEmail(lease, tenant, riskLevel) {
    if (process.env.CAMPAIGN_EMAIL_ENABLED !== 'true') {
      logger.info('Email campaigns disabled');
      return;
    }

    const templates = {
      'high-risk': 'retention-high-risk',
      'medium-risk': 'retention-medium-risk',
      'low-risk': 'retention-standard'
    };

    const emailContent = {
      to: tenant.email,
      subject: riskLevel === 'high-risk'
        ? "We'd Love to Keep You as a Resident!"
        : "Time to Renew Your Lease - Special Offers Inside",
      template: templates[riskLevel],
      data: {
        firstName: tenant.firstName,
        propertyAddress: lease.propertyId.address,
        leaseEndDate: lease.endDate.toLocaleDateString(),
        currentRent: lease.monthlyRent,
        tenureMonths: lease.tenureMonths
      }
    };

    await emailService.send(emailContent);
    logger.info(`Retention email sent to ${tenant.email}`);
  }

  /**
   * Generate personalized incentive offer
   */
  async generateIncentiveOffer(lease) {
    const riskScore = lease.churnPrediction.riskScore;
    const currentRent = lease.monthlyRent;

    // Calculate incentive based on risk score
    let incentiveType;
    let incentiveValue;
    let description;

    if (riskScore >= 70) {
      // High-medium risk: significant incentive
      incentiveType = 'rent-discount';
      incentiveValue = currentRent * 0.05; // 5% discount for 3 months
      description = '5% rent discount for first 3 months of renewal';
    } else if (riskScore >= 60) {
      // Medium risk: moderate incentive
      incentiveType = 'upgrade';
      incentiveValue = 500;
      description = '$500 credit for property upgrades or repairs';
    } else {
      // Lower-medium risk: small incentive
      incentiveType = 'gift-card';
      incentiveValue = 250;
      description = '$250 gift card upon lease renewal';
    }

    return {
      type: incentiveType,
      value: incentiveValue,
      description,
      expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
      riskScoreAtOffer: riskScore
    };
  }

  /**
   * Send incentive offer to tenant
   */
  async sendIncentiveOffer(tenant, incentive) {
    const emailContent = {
      to: tenant.email,
      subject: '🎁 Exclusive Renewal Offer Just For You!',
      template: 'incentive-offer',
      data: {
        firstName: tenant.firstName,
        incentiveDescription: incentive.description,
        incentiveValue: incentive.value,
        expiresAt: incentive.expiresAt.toLocaleDateString()
      }
    };

    await emailService.send(emailContent);
    logger.info(`Incentive offer sent to ${tenant.email}`);
  }

  /**
   * Get retention campaign metrics
   */
  async getCampaignMetrics(startDate, endDate) {
    const filter = {
      'retentionActions.triggeredAt': {
        $gte: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        $lte: endDate || new Date()
      }
    };

    const leases = await Lease.find(filter);

    const metrics = {
      total_campaigns: 0,
      by_action_type: {},
      by_risk_level: { HIGH: 0, MEDIUM: 0, LOW: 0 },
      renewal_rate: 0,
      avg_days_to_decision: 0
    };

    leases.forEach(lease => {
      lease.retentionActions.forEach(action => {
        metrics.total_campaigns++;

        // Count by action type
        metrics.by_action_type[action.actionType] =
          (metrics.by_action_type[action.actionType] || 0) + 1;
      });

      // Count by risk level
      if (lease.churnPrediction?.riskLevel) {
        metrics.by_risk_level[lease.churnPrediction.riskLevel]++;
      }
    });

    // Calculate renewal rate for leases with campaigns
    const renewedCount = leases.filter(l => l.renewalStatus === 'renewed').length;
    metrics.renewal_rate = leases.length > 0
      ? (renewedCount / leases.length) * 100
      : 0;

    return metrics;
  }

  /**
   * Calculate ROI of retention campaigns
   */
  async calculateROI(startDate, endDate) {
    const metrics = await this.getCampaignMetrics(startDate, endDate);

    const avgTurnoverCost = 4000; // $4,000 per turnover
    const avgCampaignCost = 200; // $200 per retention campaign

    const turnoversAvoided = metrics.total_campaigns * (metrics.renewal_rate / 100);
    const costSavings = turnoversAvoided * avgTurnoverCost;
    const campaignCosts = metrics.total_campaigns * avgCampaignCost;
    const netSavings = costSavings - campaignCosts;
    const roi = campaignCosts > 0 ? (netSavings / campaignCosts) * 100 : 0;

    return {
      total_campaigns: metrics.total_campaigns,
      turnovers_avoided: Math.round(turnoversAvoided),
      cost_savings: costSavings,
      campaign_costs: campaignCosts,
      net_savings: netSavings,
      roi_percentage: roi,
      renewal_rate: metrics.renewal_rate
    };
  }
}

module.exports = new RetentionService();
