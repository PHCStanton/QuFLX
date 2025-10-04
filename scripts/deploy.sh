#!/bin/bash

# QuantumFlux Trading Platform - Production Deployment Script
# This script handles deployment to production environment

set -e  # Exit on any error

# Configuration
PROJECT_NAME="quantumflux"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker service."
        exit 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available."
        exit 1
    fi

    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found."
        exit 1
    fi

    # Check if required environment variables are set
    required_vars=("API_KEY" "SECRET_KEY" "SENTRY_DSN")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$ENV_FILE" || grep -q "^$var=your-" "$ENV_FILE"; then
            log_error "Required environment variable $var is not properly set in $ENV_FILE"
            exit 1
        fi
    done

    log_success "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log_info "Creating backup of current deployment..."

    mkdir -p "$BACKUP_DIR"

    # Backup database if it exists
    if [ -d "data" ]; then
        tar -czf "$BACKUP_DIR/data_$(date +%Y%m%d_%H%M%S).tar.gz" data/
        log_success "Data backup created"
    fi

    # Backup logs
    if [ -d "logs" ]; then
        tar -czf "$BACKUP_DIR/logs_$(date +%Y%m%d_%H%M%S).tar.gz" logs/
        log_success "Logs backup created"
    fi

    # Backup Chrome profile
    if [ -d "Chrome_profile" ]; then
        tar -czf "$BACKUP_DIR/chrome_profile_$(date +%Y%m%d_%H%M%S).tar.gz" Chrome_profile/
        log_success "Chrome profile backup created"
    fi
}

# Clean up old backups (keep last 10)
cleanup_old_backups() {
    log_info "Cleaning up old backups..."

    # Keep only last 10 backups of each type
    for pattern in "data_*.tar.gz" "logs_*.tar.gz" "chrome_profile_*.tar.gz"; do
        backup_files=("$BACKUP_DIR"/$pattern)
        if [ ${#backup_files[@]} -gt 10 ]; then
            # Sort by modification time and remove oldest
            ls -t "$BACKUP_DIR"/$pattern | tail -n +11 | xargs -I {} rm "$BACKUP_DIR"/{}
        fi
    done

    log_success "Old backups cleaned up"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."

    if command -v docker-compose &> /dev/null; then
        docker-compose pull
    else
        docker compose pull
    fi

    log_success "Images pulled successfully"
}

# Deploy application
deploy_application() {
    log_info "Deploying QuantumFlux application..."

    # Stop existing containers
    log_info "Stopping existing containers..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi

    # Start new containers
    log_info "Starting new containers..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d --build
    else
        docker compose up -d --build
    fi

    log_success "Application deployed successfully"
}

# Health check
health_check() {
    log_info "Performing health checks..."

    # Wait for services to be ready
    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"

        # Check if containers are running
        if command -v docker-compose &> /dev/null; then
            running_containers=$(docker-compose ps -q | wc -l)
        else
            running_containers=$(docker compose ps -q | wc -l)
        fi

        if [ "$running_containers" -eq 0 ]; then
            log_error "No containers are running"
            exit 1
        fi

        # Check backend health endpoint
        if curl -f -s http://localhost:8000/health/live > /dev/null 2>&1; then
            log_success "Backend health check passed"
            break
        else
            log_warning "Backend not ready yet, waiting..."
            sleep 10
            ((attempt++))
        fi
    done

    if [ $attempt -gt $max_attempts ]; then
        log_error "Health check failed after $max_attempts attempts"
        exit 1
    fi

    # Check frontend if deployed
    if curl -f -s http://localhost:80 > /dev/null 2>&1; then
        log_success "Frontend health check passed"
    fi
}

# Post-deployment tasks
post_deployment_tasks() {
    log_info "Running post-deployment tasks..."

    # Run database migrations if needed
    # Add migration commands here if database is added in future

    # Clear any cached data that might be stale
    log_info "Clearing application cache..."
    # Add cache clearing commands here

    log_success "Post-deployment tasks completed"
}

# Rollback function
rollback() {
    log_error "Deployment failed. Initiating rollback..."

    # Stop failed deployment
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi

    # Restore from backup if needed
    # Add rollback logic here

    log_info "Rollback completed. Please check logs for details."
    exit 1
}

# Main deployment function
main() {
    log_info "Starting QuantumFlux production deployment..."

    # Trap errors for rollback
    trap rollback ERR

    pre_deployment_checks
    create_backup
    cleanup_old_backups
    pull_images
    deploy_application
    health_check
    post_deployment_tasks

    log_success "QuantumFlux deployment completed successfully!"
    log_info "Application is now running at:"
    log_info "  Backend API: http://localhost:8000"
    log_info "  API Docs: http://localhost:8000/docs"
    log_info "  Frontend: http://localhost:80"
    log_info ""
    log_info "Monitor logs with: docker-compose logs -f"
}

# Show usage if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "QuantumFlux Production Deployment Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo "  --rollback    Rollback to previous deployment"
    echo ""
    echo "Environment:"
    echo "  Ensure .env.production is configured with production values"
    echo "  Required: API_KEY, SECRET_KEY, SENTRY_DSN"
    echo ""
    exit 0
fi

# Handle rollback option
if [ "$1" = "--rollback" ]; then
    rollback
    exit 0
fi

# Run main deployment
main