# Docker Deployment Guide

This guide explains how to deploy the grocery price scraper using Docker for production environments.

## Why Docker?

✅ **Consistent environment** - Same behavior across dev/staging/production  
✅ **Easy deployment** - One command to start everything  
✅ **Isolated dependencies** - No conflicts with system Python  
✅ **Portable** - Works on any system with Docker  
✅ **Production-ready** - Industry standard for containerized apps  

## Prerequisites

- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose (usually included with Docker Desktop)
- `.env` file configured (see Configuration section)
- `service_account.json` file for Google Sheets API

## Quick Start

### 1. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

### 2. Start the Container

```bash
# Using the helper script (recommended)
./docker-start.sh

# Or manually (from project root)
docker-compose -f docker/docker-compose.yml up -d --build
```

**Note**: Docker files are organized in the `docker/` folder, but commands should be run from the project root.

### 3. View Logs

```bash
# Follow logs in real-time
docker-compose logs -f scraper

# View last 100 lines
docker-compose logs --tail=100 scraper
```

## Configuration

### Environment Variables

Edit `.env` file with your settings:

```env
# Scheduler Mode
MODE=production  # or "test" for testing

# Production schedule (UTC)
PRODUCTION_CRON_HOUR=2
PRODUCTION_CRON_MINUTE=0

# Google Sheets
GOOGLE_SHEET_ID=your_sheet_id_here

# Email (optional)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com
```

### Service Account File

Place `service_account.json` in the project root. This file is mounted as read-only in the container.

**Important**: Make sure the Google Sheet is shared with the service account email.

## Management Commands

### Start Container
```bash
./docker-start.sh
# or
docker-compose -f docker/docker-compose.yml up -d
```

### Stop Container
```bash
./docker-stop.sh
# or
docker-compose -f docker/docker-compose.yml down
```

### Restart Container
```bash
docker-compose -f docker/docker-compose.yml restart scraper
```

### View Status
```bash
docker-compose -f docker/docker-compose.yml ps
```

### View Logs
```bash
# Follow logs
docker-compose -f docker/docker-compose.yml logs -f scraper

# Last 50 lines
docker-compose -f docker/docker-compose.yml logs --tail=50 scraper

# Specific time range
docker-compose -f docker/docker-compose.yml logs --since 1h scraper
```

### Execute Commands in Container
```bash
# Run a one-time command
docker-compose -f docker/docker-compose.yml exec scraper python3 run_project.py --run-once

# Access shell
docker-compose -f docker/docker-compose.yml exec scraper /bin/bash
```

### Rebuild Container
```bash
# Rebuild after code changes
docker-compose -f docker/docker-compose.yml up -d --build
```

## Data Persistence

The following directories are mounted as volumes and persist data:

- `./data` → `/app/data` - Store data (stores.json, etc.)
- `./logs` → `/app/logs` - Application logs
- `./output` → `/app/output` - Generated CSV files

**Important**: These directories are created automatically and persist even if the container is removed.

## Health Check

The container includes a health check that verifies the Python environment. Check health status:

```bash
docker-compose ps
# Look for "healthy" status
```

## Troubleshooting

### Container Won't Start

1. **Check Docker is running:**
   ```bash
   docker ps
   ```

2. **Check logs:**
   ```bash
   docker-compose logs scraper
   ```

3. **Verify .env file:**
   ```bash
   cat .env
   ```

4. **Check service_account.json:**
   ```bash
   ls -la service_account.json
   ```

### Container Keeps Restarting

1. **Check logs for errors:**
   ```bash
   docker-compose logs --tail=100 scraper
   ```

2. **Check container status:**
   ```bash
   docker-compose ps
   ```

3. **Verify environment variables:**
   ```bash
   docker-compose exec scraper env | grep -E "(MODE|GOOGLE|SMTP)"
   ```

### Permission Issues

If you see permission errors:

```bash
# Fix ownership (Linux/macOS)
sudo chown -R $USER:$USER data logs output

# Or run with specific user (edit docker-compose.yml)
```

### Out of Disk Space

Docker images and containers can use significant space:

```bash
# Clean up unused resources
docker system prune -a

# Remove old logs
docker-compose logs --no-log-prefix scraper > /dev/null
```

### Network Issues

If the container can't reach external APIs:

```bash
# Check network connectivity
docker-compose exec scraper ping -c 3 google.com

# Check DNS
docker-compose exec scraper nslookup services.publix.com
```

## Production Deployment

### 1. Build Production Image

```bash
docker build -t grocery-price-scraper:latest .
```

### 2. Run with Production Settings

```bash
# Set production mode in .env
MODE=production
PRODUCTION_CRON_HOUR=2
PRODUCTION_CRON_MINUTE=0

# Start container
docker-compose up -d
```

### 3. Set Up Auto-Restart

The `docker-compose.yml` includes `restart: unless-stopped`, which means:
- Container automatically restarts on failure
- Container starts on system boot (if Docker is configured to start on boot)

### 4. Monitor Logs

Set up log rotation and monitoring:

```bash
# View logs
docker-compose logs -f scraper | tee scraper.log

# Or use a log aggregation service
```

## Development vs Production

### Development Mode

```env
MODE=test
TEST_INTERVAL_SECONDS=300  # Run every 5 minutes
```

### Production Mode

```env
MODE=production
PRODUCTION_CRON_HOUR=2      # 2 AM UTC
PRODUCTION_CRON_MINUTE=0
```

## Updating the Application

1. **Pull latest code:**
   ```bash
   git pull
   ```

2. **Rebuild and restart:**
   ```bash
   docker-compose up -d --build
   ```

3. **Verify it's running:**
   ```bash
   docker-compose logs -f scraper
   ```

## Backup

Important data is stored in mounted volumes:

```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/ output/

# Restore
tar -xzf backup-YYYYMMDD.tar.gz
```

## Security Considerations

1. **Never commit sensitive files:**
   - `.env` (already in .gitignore)
   - `service_account.json` (already in .gitignore)

2. **Use secrets management in production:**
   - Docker Secrets
   - AWS Secrets Manager
   - HashiCorp Vault

3. **Limit container resources:**
   ```yaml
   # Add to docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '1'
         memory: 2G
   ```

## Comparison: Docker vs Other Methods

| Feature | Docker | Cron | PM2 |
|---------|--------|------|-----|
| **Environment Isolation** | ✅ Yes | ❌ No | ❌ No |
| **Easy Deployment** | ✅ Yes | ⚠️ Manual | ⚠️ Manual |
| **Dependency Management** | ✅ Automatic | ❌ Manual | ❌ Manual |
| **Portability** | ✅ High | ⚠️ Medium | ⚠️ Medium |
| **Resource Limits** | ✅ Yes | ❌ No | ⚠️ Limited |
| **Best For** | Production | Simple servers | Node.js stacks |

## Next Steps

1. ✅ Configure `.env` file
2. ✅ Place `service_account.json` in project root
3. ✅ Run `./docker-start.sh`
4. ✅ Monitor logs: `docker-compose logs -f scraper`
5. ✅ Verify first run completes successfully

For questions or issues, check the logs in `logs/` directory or container logs.
