# 🐳 Docker Deployment Guide for K-Scan

This guide covers how to deploy K-Scan using Docker and Docker Compose in various environments.

## 📋 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Clone and Setup

```bash
git clone <repository-url>
cd k-backend
```

### 2. Configure Environment

Create your `.env` file from the template:

```bash
# Create environment file
cat > .env << 'EOF'
# Required: OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Browserless Configuration (for JavaScript rendering)
BROWSERLESS_TOKEN=your-browserless-token-here
BROWSERLESS_URL=https://chrome.browserless.io

# Application Settings
DEBUG=false
DATABASE_URL=sqlite:///data/k_scan.db
EOF
```

### 3. Launch K-Scan

```bash
# Build and start the application
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f k-scan
```

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Quick Scan**: http://localhost:8000/audit/quick?url=https://example.com

---

## 🏗️ Available Configurations

### Development Setup

For local development with hot reload:

```bash
# Uses docker-compose.override.yml automatically
docker-compose up -d

# The application will reload when you change source code
```

**Development Features:**
- ✅ Source code hot reload
- ✅ Debug mode enabled
- ✅ Local data directory (`./dev-data`)
- ✅ Detailed logging

### Production Setup

For production deployment with security hardening:

```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Production Features:**
- ✅ PostgreSQL database (instead of SQLite)
- ✅ Redis caching
- ✅ Security hardening
- ✅ Resource limits
- ✅ Health checks
- ✅ Ready for reverse proxy (Traefik)

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key for AI agents |
| `BROWSERLESS_TOKEN` | ❌ | - | Token for JavaScript rendering |
| `DEBUG` | ❌ | `false` | Enable debug mode |
| `API_PORT` | ❌ | `8000` | API server port |
| `MAX_SCAN_DEPTH` | ❌ | `3` | Maximum crawling depth |
| `DATABASE_URL` | ❌ | SQLite | Database connection string |

### Database Options

**SQLite (Default - Good for development):**
```env
DATABASE_URL=sqlite:///data/k_scan.db
```

**PostgreSQL (Recommended for production):**
```env
DATABASE_URL=postgresql://k_scan_user:password@postgres:5432/k_scan
POSTGRES_PASSWORD=secure_password_change_me
```

---

## 🚀 Deployment Scenarios

### 1. Local Development

```bash
# Quick development setup
docker-compose up -d

# Access with hot reload
curl -X GET "http://localhost:8000/audit/quick?url=https://example.com"
```

### 2. Production Server

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale the application
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale k-scan=3
```

### 3. Cloud Deployment (AWS/GCP/Azure)

```bash
# Set environment variables in your cloud provider
export OPENAI_API_KEY="sk-your-key"
export BROWSERLESS_TOKEN="your-token"
export POSTGRES_PASSWORD="secure-password"

# Deploy with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 📊 Monitoring and Maintenance

### Health Checks

The application includes built-in health checks:

```bash
# Check application health
curl http://localhost:8000/health

# Docker health status
docker-compose ps
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f k-scan

# View specific service logs
docker-compose logs postgres redis
```

### Data Persistence

Data is automatically persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep k-backend

# Backup database (SQLite)
docker-compose exec k-scan cp /app/data/k_scan.db /tmp/backup.db

# Backup database (PostgreSQL)
docker-compose exec postgres pg_dump -U k_scan_user k_scan > backup.sql
```

---

## 🔒 Security Considerations

### Production Security

1. **Environment Variables**: Never commit `.env` files
2. **Database Passwords**: Use strong, unique passwords
3. **API Keys**: Rotate keys regularly
4. **Network Security**: Use HTTPS in production
5. **Resource Limits**: Set appropriate CPU/memory limits

### Recommended Production Setup

```yaml
# In docker-compose.prod.yml
services:
  k-scan:
    security_opt:
      - no-new-privileges:true
    read_only: true
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

---

## 🛠️ Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different external port
```

**Database Connection Issues:**
```bash
# Reset volumes
docker-compose down -v
docker-compose up -d
```

**Memory Issues:**
```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
```

### Debugging Commands

```bash
# Enter container shell
docker-compose exec k-scan bash

# Check environment variables
docker-compose exec k-scan env | grep -E "(OPENAI|BROWSERLESS)"

# Test API directly
docker-compose exec k-scan curl http://localhost:8000/health
```

---

## 🔄 Updates and Maintenance

### Updating K-Scan

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Migrations

```bash
# If using PostgreSQL with migrations
docker-compose exec k-scan python -m alembic upgrade head
```

---

## 📞 Support

- **Documentation**: `/docs` endpoint
- **Health Status**: `/health` endpoint
- **Component Status**: `/components` endpoint

For production deployments, consider:
- Using managed databases (AWS RDS, Google Cloud SQL)
- Implementing proper logging aggregation
- Setting up monitoring and alerting
- Using container orchestration (Kubernetes)

---

## 🎯 Performance Tuning

### Resource Allocation

```yaml
# Recommended production resources
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Scaling

```bash
# Scale multiple instances
docker-compose up -d --scale k-scan=3

# Use load balancer (nginx/traefik) for multiple instances
```

Happy Scanning! 🔍🛡️ 