/**
 * Tenant Mongoose Schema
 * Represents tenant demographic and behavioral data
 */
const mongoose = require('mongoose');

const tenantSchema = new mongoose.Schema({
  tenantId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },

  // Personal Information
  firstName: {
    type: String,
    required: true
  },
  lastName: {
    type: String,
    required: true
  },
  email: {
    type: String,
    required: true,
    lowercase: true
  },
  phone: {
    type: String,
    required: true
  },

  // Demographics
  dateOfBirth: Date,
  householdSize: {
    type: Number,
    default: 1
  },
  annualIncome: Number,
  employmentStatus: {
    type: String,
    enum: ['employed', 'self-employed', 'unemployed', 'retired', 'student'],
    default: 'employed'
  },
  employer: String,

  // Account Information
  accountCreatedAt: {
    type: Date,
    default: Date.now
  },
  portalLoginCount: {
    type: Number,
    default: 0
  },
  lastLoginAt: Date,
  autopayEnabled: {
    type: Boolean,
    default: false
  },
  primaryPaymentMethod: {
    type: String,
    enum: ['ach', 'credit-card', 'debit-card', 'check', 'money-order'],
    default: 'ach'
  },

  // Behavioral Metrics
  avgResponseTimeHours: {
    type: Number,
    default: 24
  },
  missedCommunicationCount: {
    type: Number,
    default: 0
  },
  complaintCount: {
    type: Number,
    default: 0
  },
  escalationCount: {
    type: Number,
    default: 0
  },

  // Preferences
  preferredContactMethod: {
    type: String,
    enum: ['email', 'phone', 'sms', 'portal'],
    default: 'email'
  },
  communicationOptIn: {
    type: Boolean,
    default: true
  },

  // Current Lease Reference
  currentLeaseId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Lease'
  },

  // Status
  status: {
    type: String,
    enum: ['active', 'former', 'applicant', 'banned'],
    default: 'active'
  },

  // Metadata
  notes: String,
  tags: [String],
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
tenantSchema.index({ email: 1 });
tenantSchema.index({ status: 1 });
tenantSchema.index({ currentLeaseId: 1 });

// Virtual for full name
tenantSchema.virtual('fullName').get(function() {
  return `${this.firstName} ${this.lastName}`;
});

// Methods
tenantSchema.methods.incrementLoginCount = function() {
  this.portalLoginCount += 1;
  this.lastLoginAt = new Date();
  return this.save();
};

tenantSchema.methods.recordComplaint = function() {
  this.complaintCount += 1;
  return this.save();
};

// Statics
tenantSchema.statics.findActive = function() {
  return this.find({ status: 'active' });
};

tenantSchema.statics.findByEmail = function(email) {
  return this.findOne({ email: email.toLowerCase() });
};

module.exports = mongoose.model('Tenant', tenantSchema);
