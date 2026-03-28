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

# Production stage - pinned nginx version
FROM nginx:1.25-alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config as template for env substitution
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Default API upstream (can be overridden at runtime)
ENV API_UPSTREAM=http://walks-api:8000

EXPOSE 80
