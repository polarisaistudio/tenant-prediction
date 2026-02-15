# ============================================================================
# Multi-stage Dockerfile for Backend API
# Node.js 20 + Express
# ============================================================================

FROM node:20-alpine as base

WORKDIR /app

# ============================================================================
# Dependencies Stage
# ============================================================================
FROM base as dependencies

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# ============================================================================
# Development Stage
# ============================================================================
FROM base as development

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies)
RUN npm install

# Copy application code
COPY . .

EXPOSE 4000

CMD ["npm", "run", "dev"]

# ============================================================================
# Build Stage
# ============================================================================
FROM base as build

# Copy dependencies
COPY --from=dependencies /app/node_modules ./node_modules

# Copy application code
COPY . .

# Run any build steps if needed
# RUN npm run build

# ============================================================================
# Production Stage
# ============================================================================
FROM base as production

ENV NODE_ENV=production

# Copy production dependencies
COPY --from=dependencies /app/node_modules ./node_modules

# Copy application code
COPY --from=build /app/src ./src
COPY --from=build /app/package*.json ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:4000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

CMD ["node", "src/index.js"]
