/**
 * Main Express Application Entry Point
 * Tenant Churn Prediction API Gateway
 */
require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

const logger = require('./utils/logger');
const errorHandler = require('./middleware/errorHandler');
const { notFound } = require('./middleware/notFound');

// Import routes
const healthRoutes = require('./routes/health');
const tenantRoutes = require('./routes/tenants');
const leaseRoutes = require('./routes/leases');
const predictionRoutes = require('./routes/predictions');
const retentionRoutes = require('./routes/retention');
const analyticsRoutes = require('./routes/analytics');

// Initialize Express app
const app = express();

// ============================================================================
// Middleware Configuration
// ============================================================================

// Security
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.API_RATE_LIMIT) || 100,
  message: 'Too many requests from this IP, please try again later'
});
app.use('/api/', limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Compression
app.use(compression());

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined', { stream: logger.stream }));
}

// Request ID tracking
app.use((req, res, next) => {
  req.id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  res.setHeader('X-Request-ID', req.id);
  next();
});

// ============================================================================
// Routes
// ============================================================================

app.get('/', (req, res) => {
  res.json({
    service: 'Tenant Churn Prediction API',
    version: '1.0.0',
    status: 'operational',
    documentation: '/api/docs'
  });
});

// Health checks
app.use('/health', healthRoutes);

// API v1 routes
app.use('/api/v1/tenants', tenantRoutes);
app.use('/api/v1/leases', leaseRoutes);
app.use('/api/v1/predictions', predictionRoutes);
app.use('/api/v1/retention', retentionRoutes);
app.use('/api/v1/analytics', analyticsRoutes);

// API documentation (Swagger)
if (process.env.NODE_ENV !== 'production') {
  const swaggerUi = require('swagger-ui-express');
  const swaggerSpec = require('./config/swagger');
  app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
}

// Prometheus metrics
if (process.env.PROMETHEUS_ENABLED === 'true') {
  const promClient = require('prom-client');
  const register = new promClient.Registry();
  promClient.collectDefaultMetrics({ register });

  app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  });
}

// ============================================================================
// Error Handling
// ============================================================================

app.use(notFound);
app.use(errorHandler);

// ============================================================================
// Database Connection
// ============================================================================

const connectDB = async () => {
  try {
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/tenant_churn';

    await mongoose.connect(mongoUri, {
      maxPoolSize: parseInt(process.env.MONGODB_MAX_POOL_SIZE) || 10,
      serverSelectionTimeoutMS: parseInt(process.env.MONGODB_TIMEOUT) || 5000,
    });

    logger.info('MongoDB connected successfully');

    // Handle connection events
    mongoose.connection.on('error', (err) => {
      logger.error('MongoDB connection error:', err);
    });

    mongoose.connection.on('disconnected', () => {
      logger.warn('MongoDB disconnected');
    });

  } catch (error) {
    logger.error('MongoDB connection failed:', error);
    process.exit(1);
  }
};

// ============================================================================
// Server Initialization
// ============================================================================

const PORT = process.env.PORT || 4000;

const startServer = async () => {
  try {
    // Connect to database
    await connectDB();

    // Start HTTP server
    const server = app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`API Documentation: http://localhost:${PORT}/api/docs`);
    });

    // Graceful shutdown
    const gracefulShutdown = async (signal) => {
      logger.info(`${signal} received. Starting graceful shutdown...`);

      server.close(async () => {
        logger.info('HTTP server closed');

        try {
          await mongoose.connection.close();
          logger.info('Database connections closed');
          process.exit(0);
        } catch (error) {
          logger.error('Error during shutdown:', error);
          process.exit(1);
        }
      });

      // Force shutdown after 30 seconds
      setTimeout(() => {
        logger.error('Forcing shutdown after timeout');
        process.exit(1);
      }, 30000);
    };

    // Handle shutdown signals
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => gracefulShutdown('SIGINT'));

  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

// Start server if not in test environment
if (process.env.NODE_ENV !== 'test') {
  startServer();
}

module.exports = app;
