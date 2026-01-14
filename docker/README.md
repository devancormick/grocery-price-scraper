# Docker Configuration

This folder contains Docker configuration files for the grocery price scraper.

## Files

- **Dockerfile** - Container image definition
- **docker-compose.yml** - Docker Compose configuration for easy deployment
- **README.md** - This file

## Usage

All Docker commands should be run from the **project root**, not from this folder.

### Quick Start

```bash
# From project root
./docker-start.sh

# Or manually
docker-compose -f docker/docker-compose.yml up -d --build
```

### File Locations

- **Dockerfile**: `docker/Dockerfile`
- **docker-compose.yml**: `docker/docker-compose.yml`
- **.dockerignore**: Project root (required for build context)

## Build Context

The build context is the project root (`..`), so:
- All files are copied from the project root
- `.dockerignore` must be in the project root
- Volume mounts use relative paths from project root

## See Also

- [DOCKER_GUIDE.md](../DOCKER_GUIDE.md) - Complete Docker deployment guide
- [README_DEPLOYMENT.md](../README_DEPLOYMENT.md) - General deployment options
