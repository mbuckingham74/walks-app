# Build stage - pinned to specific version
FROM node:20.10-alpine AS build

WORKDIR /app

# Copy package files (including lockfile)
COPY package.json package-lock.json ./

# Install dependencies using lockfile for reproducible builds
RUN npm ci --ignore-scripts

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage - using unprivileged nginx image
FROM nginxinc/nginx-unprivileged:1.25-alpine

# Create templates directory with correct permissions (requires root)
USER root
RUN mkdir -p /etc/nginx/templates && chmod 755 /etc/nginx/templates

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config as template for env substitution
COPY --chmod=644 nginx.conf /etc/nginx/templates/default.conf.template

# Switch back to unprivileged user
USER 101

# Default API upstream (can be overridden at runtime)
ENV API_UPSTREAM=http://walks-api:8000

EXPOSE 8080

# nginx-unprivileged runs on port 8080 by default
