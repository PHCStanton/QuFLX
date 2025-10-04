# QuantumFlux Trading Platform - Deployment Guide

## Overview

This guide covers the production deployment of the QuantumFlux Trading Platform using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- At least 10GB free disk space
- Linux/Windows/Mac host system

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd quantumflux
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env.production
   # Edit .env.production with your production values
   ```

3. **Deploy**
   ```bash
   # For Linux/Mac
   ./scripts/deploy.sh

   # For Windows
   # Run the deployment commands manually or use WSL
   ```

## Environment Configuration

### Required Environment Variables

Copy `.env.example` to `.env.production` and configure:

```bash
# Required for production
API_KEY=your-production-api-key
SECRET_KEY=your-production-secret-key
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Database (future use)
# DATABASE_URL=postgresql://user:password@host:5432/db

# Redis (future use)
# REDIS_URL=redis://host:6379
```

### Security Considerations

- **API_KEY**: Use a strong, randomly generated key (32+ characters)
- **SECRET_KEY**: Use a cryptographically secure random key
- **SENTRY_DSN**: Configure error tracking for production monitoring
- **CORS_ORIGINS**: Restrict to your production domain only

## Deployment Options

### Option 1: Automated Deployment (Linux/Mac)

```bash
# Make script executable (Linux/Mac)
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

### Option 2: Manual Deployment

```bash
# 1. Pull latest images
docker-compose pull

# 2. Build and start services
docker-compose up -d --build

# 3. Check health
curl http://localhost:8000/health/live
```

### Option 3: Using Docker Compose Directly

```bash
# Development
docker-compose -f docker-compose.yml up -d

# Production with environment file
docker-compose --env-file .env.production up -d
```

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   NGINX         │    │   QuantumFlux   │
│   Frontend      │    │   Backend API   │
│   (Port 80)     │◄──►│   (Port 8000)   │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Chrome        │
                       │   Browser       │
                       │   (Headless)    │
                       └─────────────────┘
```

## Monitoring and Health Checks

### Health Endpoints

- **API Health**: `GET /health/live`
- **Readiness**: `GET /health/ready`
- **Full Health**: `GET /health`

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f quantumflux-backend

# View with timestamps
docker-compose logs -f --timestamps
```

### Metrics

The application exposes performance metrics that can be integrated with:
- Prometheus
- Grafana
- DataDog
- New Relic

## Backup and Recovery

### Automated Backups

The deployment script automatically creates backups of:
- Application data (`data/`)
- Logs (`logs/`)
- Chrome profiles (`Chrome_profile/`)

### Manual Backup

```bash
# Create backup directory
mkdir -p backups

# Backup data
tar -czf backups/data_$(date +%Y%m%d_%H%M%S).tar.gz data/

# Backup logs
tar -czf backups/logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

### Recovery

```bash
# Stop services
docker-compose down

# Restore from backup
tar -xzf backups/data_latest.tar.gz

# Restart services
docker-compose up -d
```

## Security Hardening

### Container Security

- Non-root user execution
- Minimal base images
- No privileged containers
- Read-only root filesystem where possible

### Network Security

- Restricted CORS origins
- API key authentication for sensitive endpoints
- Rate limiting on API endpoints
- Input validation and sanitization

### Monitoring

- Comprehensive logging with structured JSON
- Error tracking with Sentry
- Performance monitoring
- Security event logging

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process or change port in docker-compose.yml
   ```

2. **Chrome not starting**
   ```bash
   # Check Chrome logs
   docker-compose logs quantumflux-backend
   # Ensure sufficient memory (4GB+ recommended)
   ```

3. **Health check failures**
   ```bash
   # Check service status
   docker-compose ps
   # Check individual container
   docker-compose exec quantumflux-backend curl http://localhost:8000/health
   ```

### Debug Mode

For debugging production issues:

```bash
# Run with debug logging
LOG_LEVEL=DEBUG docker-compose up -d

# Access container shell
docker-compose exec quantumflux-backend /bin/bash

# Check application logs
docker-compose exec quantumflux-backend tail -f logs/quantumflux.log
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  quantumflux-backend:
    scale: 3  # Run 3 instances
    environment:
      - WORKERS=2
```

### Load Balancing

Use a reverse proxy like NGINX or Traefik for load balancing multiple instances.

## Maintenance

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d --build
```

### Log Rotation

Logs are automatically rotated:
- Max file size: 10MB (application), 50MB (performance), 20MB (security)
- Retention: 30 days (application/performance), 90 days (errors), 365 days (security)

### Cleanup

```bash
# Remove unused images
docker image prune -f

# Remove stopped containers
docker container prune -f

# Remove unused volumes
docker volume prune -f
```

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed (if HTTPS required)
- [ ] Domain configured
- [ ] Monitoring/alerting set up
- [ ] Backup strategy implemented
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Rollback plan documented

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Verify environment configuration
3. Test health endpoints
4. Review security settings
5. Check system resources

## Version History

- **v2.0.0**: Production-ready with comprehensive security, monitoring, and deployment automation
- **v1.0.0**: Initial MVP with core trading functionality