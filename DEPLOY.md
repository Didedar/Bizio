# Deployment Guide

## Production Deployment Checklist

### 1. Environment Configuration

Create production `.env` file:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/bizio_prod

# Security
SECRET_KEY=<generate-secure-random-key-32-chars-minimum>
DEBUG=false

# Redis
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# CORS (specify allowed origins)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Logging
LOG_LEVEL=WARNING

# Feature flags
CREATE_TABLES_ON_STARTUP=false  # Use migrations instead
RATE_LIMIT_ENABLED=true
```

### 2. Database Setup

**Run migrations:**
```bash
cd backend
alembic upgrade head
```

**Backup strategy:**
- Set up automated daily backups
- Test restore procedures
- Keep backups for 30+ days

### 3. Security

- [ ] Generate strong SECRET_KEY (32+ random characters)
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall (allow only necessary ports)
- [ ] Set up rate limiting
- [ ] Enable CORS with specific origins only
- [ ] Use environment variables for all secrets
- [ ] Rotate credentials regularly
- [ ] Enable database SSL connections

### 4. Docker Production Setup

**docker-compose.prod.yml:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    
  redis:
    image: redis:7-alpine
    restart: always
    
  backend:
    image: your-registry/bizio-backend:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
      - DEBUG=false
      - CREATE_TABLES_ON_STARTUP=false
    depends_on:
      - postgres
      - redis
    restart: always
    
  worker:
    image: your-registry/bizio-backend:latest
    command: celery -A worker.worker worker --loglevel=warning
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: always
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
```

### 5. Monitoring & Logging

**Recommended tools:**
- Application monitoring: Sentry, New Relic
- Log aggregation: ELK Stack, Datadog
- Uptime monitoring: UptimeRobot, Pingdom
- Performance: Prometheus + Grafana

**Enable structured logging:**
```python
# Add to app/main.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        })
```

### 6. CI/CD Pipeline

**Example GitHub Actions:**

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to production
        run: |
          # Add your deployment commands here
```

### 7. Cloud Provider Specific

#### AWS

**Services:**
- ECS/Fargate for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- S3 for file storage
- CloudWatch for logs
- ALB for load balancing

**Deployment:**
```bash
# Build and push Docker image
docker build -t bizio-backend backend/
docker tag bizio-backend:latest <aws-account>.dkr.ecr.region.amazonaws.com/bizio:latest
docker push <aws-account>.dkr.ecr.region.amazonaws.com/bizio:latest

# Update ECS service
aws ecs update-service --cluster bizio-cluster --service bizio-backend --force-new-deployment
```

#### Google Cloud

**Services:**
- Cloud Run for containers
- Cloud SQL for PostgreSQL
- Memorystore for Redis
- Cloud Storage for files
- Cloud Logging

**Deployment:**
```bash
# Deploy to Cloud Run
gcloud run deploy bizio-backend \
  --source backend/ \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL
```

#### Heroku

```bash
# Add Heroku remote
heroku git:remote -a bizio-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Deploy
git subtree push --prefix backend heroku main

# Run migrations
heroku run alembic upgrade head

# Scale workers
heroku ps:scale worker=1
```

### 8. Performance Optimization

- [ ] Enable database connection pooling
- [ ] Add database indexes for frequent queries
- [ ] Enable Redis caching for expensive queries
- [ ] Use CDN for static assets
- [ ] Enable gzip compression
- [ ] Set up database read replicas
- [ ] Implement query optimization

### 9. Backup & Disaster Recovery

**Automated backups:**
```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
pg_dump -h localhost -U bizio bizio_db | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

**Test restore regularly:**
```bash
# Restore from backup
gunzip -c backup_20250127_120000.sql.gz | psql -h localhost -U bizio bizio_db
```

### 10. Scaling Strategy

**Horizontal scaling:**
- Add more backend instances behind load balancer
- Scale Celery workers independently
- Use read replicas for database

**Vertical scaling:**
- Increase container resources (CPU/RAM)
- Upgrade database instance size
- Increase Redis memory

### 11. Health Checks

Add health check endpoints:

```python
# app/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 12. Post-Deployment

- [ ] Verify all services are running
- [ ] Check logs for errors
- [ ] Test critical user flows
- [ ] Monitor performance metrics
- [ ] Set up alerts for errors
- [ ] Update documentation
- [ ] Notify team of deployment

### Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Verify environment variables
- Test database connectivity
- Review security groups/firewall rules

