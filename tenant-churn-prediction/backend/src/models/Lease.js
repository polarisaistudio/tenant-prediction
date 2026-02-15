/**
 * Lease Mongoose Schema
 * Represents lease contracts and terms
 */
const mongoose = require('mongoose');

const leaseSchema = new mongoose.Schema({
  leaseId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },

  // References
  tenantId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Tenant',
    required: true,
    index: true
  },
  propertyId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Property',
    required: true,
    index: true
  },

  // Lease Terms
  startDate: {
    type: Date,
    required: true
  },
  endDate: {
    type: Date,
    required: true,
    index: true
  },
  leaseTermMonths: {
    type: Number,
    required: true,
    default: 12
  },

  // Financial Terms
  monthlyRent: {
    type: Number,
    required: true
  },
  securityDeposit: {
    type: Number,
    required: true
  },
  petDeposit: {
    type: Number,
    default: 0
  },

  // Rent Changes
  rentIncreaseHistory: [{
    effectiveDate: Date,
    previousRent: Number,
    newRent: Number,
    increasePercent: Number
  }],
  lastRentIncreasePct: {
    type: Number,
    default: 0
  },

  // Renewal Information
  renewalStatus: {
    type: String,
    enum: ['active', 'pending-renewal', 'renewed', 'not-renewed', 'expired'],
    default: 'active',
    index: true
  },
  renewalNoticeDate: Date,
  renewalDecisionDate: Date,
  renewalCount: {
    type: Number,
    default: 0
  },

  // Occupancy
  occupants: [{
    name: String,
    relationship: String,
    dateOfBirth: Date
  }],
  petsAllowed: {
    type: Boolean,
    default: false
  },
  pets: [{
    type: String,
    breed: String,
    weight: Number
  }],

  // Payment Terms
  rentDueDay: {
    type: Number,
    default: 1,
    min: 1,
    max: 31
  },
  lateFeeAmount: {
    type: Number,
    default: 50
  },
  lateFeeDaysGrace: {
    type: Number,
    default: 5
  },

  // Churn Prediction
  churnPrediction: {
    lastPredictionDate: Date,
    churnProbability: Number,
    riskScore: Number,
    riskLevel: {
      type: String,
      enum: ['LOW', 'MEDIUM', 'HIGH']
    },
    predictedChurn: Boolean,
    modelVersion: String
  },

  // Retention Actions
  retentionActions: [{
    actionType: {
      type: String,
      enum: ['email-campaign', 'phone-call', 'incentive-offer', 'property-manager-visit', 'rent-adjustment']
    },
    triggeredAt: Date,
    status: {
      type: String,
      enum: ['pending', 'completed', 'failed']
    },
    notes: String,
    outcome: String
  }],

  // Status
  status: {
    type: String,
    enum: ['active', 'expired', 'terminated', 'renewed'],
    default: 'active',
    index: true
  },
  terminationDate: Date,
  terminationReason: String,

  // Metadata
  notes: String,
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Indexes
leaseSchema.index({ startDate: 1, endDate: 1 });
leaseSchema.index({ renewalStatus: 1, endDate: 1 });
leaseSchema.index({ 'churnPrediction.riskLevel': 1 });
leaseSchema.index({ status: 1 });

// Virtual: Days until expiration
leaseSchema.virtual('daysToExpiration').get(function() {
  if (!this.endDate) return null;
  const today = new Date();
  const diff = this.endDate - today;
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
});

// Virtual: Tenure in months
leaseSchema.virtual('tenureMonths').get(function() {
  if (!this.startDate) return 0;
  const today = new Date();
  const months = (today.getFullYear() - this.startDate.getFullYear()) * 12;
  return months + (today.getMonth() - this.startDate.getMonth());
});

// Virtual: Is in renewal window (90 days before expiration)
leaseSchema.virtual('inRenewalWindow').get(function() {
  const daysToExp = this.daysToExpiration;
  return daysToExp !== null && daysToExp <= 90 && daysToExp > 0;
});

// Methods
leaseSchema.methods.updateChurnPrediction = function(prediction) {
  this.churnPrediction = {
    lastPredictionDate: new Date(),
    churnProbability: prediction.churn_probability,
    riskScore: prediction.risk_score,
    riskLevel: prediction.risk_level,
    predictedChurn: prediction.predicted_churn,
    modelVersion: prediction.model_version || '1.0.0'
  };
  return this.save();
};

leaseSchema.methods.triggerRetentionAction = function(actionType, notes = '') {
  this.retentionActions.push({
    actionType,
    triggeredAt: new Date(),
    status: 'pending',
    notes
  });
  return this.save();
};

leaseSchema.methods.recordRenewal = function(newEndDate, newRent) {
  const oldRent = this.monthlyRent;
  const increasePercent = ((newRent - oldRent) / oldRent) * 100;

  this.endDate = newEndDate;
  this.monthlyRent = newRent;
  this.renewalCount += 1;
  this.renewalStatus = 'renewed';
  this.lastRentIncreasePct = increasePercent;

  this.rentIncreaseHistory.push({
    effectiveDate: new Date(),
    previousRent: oldRent,
    newRent,
    increasePercent
  });

  return this.save();
};

// Statics
leaseSchema.statics.findExpiringInDays = function(days) {
  const futureDate = new Date();
  futureDate.setDate(futureDate.getDate() + days);

  return this.find({
    status: 'active',
    endDate: { $lte: futureDate, $gte: new Date() }
  });
};

leaseSchema.statics.findHighRisk = function() {
  return this.find({
    status: 'active',
    'churnPrediction.riskLevel': 'HIGH'
  }).populate('tenantId propertyId');
};

leaseSchema.statics.findInRenewalWindow = function() {
  const ninetyDaysFromNow = new Date();
  ninetyDaysFromNow.setDate(ninetyDaysFromNow.getDate() + 90);

  return this.find({
    status: 'active',
    endDate: { $lte: ninetyDaysFromNow, $gte: new Date() }
  });
};

module.exports = mongoose.model('Lease', leaseSchema);
