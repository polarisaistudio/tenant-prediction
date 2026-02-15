# ============================================================================
# Multi-stage Dockerfile for Frontend
# Next.js 14 + React 18
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
RUN npm ci

# ============================================================================
# Builder Stage
# ============================================================================
FROM base as builder

# Copy dependencies
COPY --from=dependencies /app/node_modules ./node_modules

# Copy application code
COPY . .

# Set Next.js environment variables
ENV NEXT_TELEMETRY_DISABLED 1

# Build Next.js application
RUN npm run build

# ============================================================================
# Production Stage
# ============================================================================
FROM base as production

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

CMD ["node", "server.js"]
