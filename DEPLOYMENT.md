# Maximus.ai Production Deployment Guide

## Overview

This guide covers deploying Maximus in a production environment using Docker Compose.

## Prerequisites

- Docker Engine 24.x or later
- Docker Compose V2
- At least 8GB RAM (16GB recommended)
- 20GB disk space for models

## Quick Start

```bash
# Clone the repository
git clone https://github.com/11vated/maximus.ai.git
cd maximus.ai

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Pull a model
docker exec maximus-ollama ollama pull qwen2.5-coder:7b

# Verify deployment
curl http://localhost:8000/health
```

## Architecture

```
                    ┌─────────────────┐
                    │    Nginx        │
                    │  (Load Balancer)│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌──────────────────┐         ┌──────────────────┐
    │    Backend       │         │    Frontend      │
    │  (FastAPI/gRPC)  │         │   (React/Vite)   │
    └────────┬─────────┘         └──────────────────┘
             │
             ▼
    ┌──────────────────┐
    │     Ollama       │
    │  (LLM Runtime)   │
    └──────────────────┘
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80/443 | Load balancer, SSL termination |
| backend | 8000 | Core API, tool execution |
| frontend | 5173 | Web terminal interface |
| ollama | 11434 | LLM inference engine |

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Ollama connection
OLLAMA_HOST=http://ollama:11434

# Security
MAXIMUS_SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:5173

# Resource limits
MAX_MEMORY_GB=8
MODEL_CACHE_SIZE=10GB
```

### Model Selection

```bash
# Default model for new sessions
docker exec maximus-ollama ollama pull qwen2.5-coder:7b

# For larger systems
docker exec maximus-ollama ollama pull qwen2.5-coder:14b

# For reasoning tasks
docker exec maximus-ollama ollama pull deepseek-r1:7b
```

## SSL/TLS Setup

```bash
# Using Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d maximus.yourdomain.com

# Copy certificates
mkdir -p certs
cp /etc/letsencrypt/live/maximus.yourdomain.com/* certs/

# Start with SSL
docker-compose -f docker-compose.prod.yml up -d
```

## Backup & Restore

```bash
# Backup sessions
docker run --rm -v maximus-sessions:/data -v $(pwd):/backup \
  alpine tar czf /backup/sessions.tar.gz -C /data .

# Restore sessions
docker run --rm -v maximus-sessions:/data -v $(pwd):/backup \
  alpine tar xzf /backup/sessions.tar.gz -C /data
```

## Monitoring

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service health
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats
```

## Scaling

For multi-GPU systems:

```yaml
# docker-compose.overrides.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

## Troubleshooting

### Ollama won't start
```bash
docker logs maximus-ollama
# Check for GPU/memory issues
```

### Model download fails
```bash
# Manual pull
docker exec maximus-ollama ollama pull qwen2.5-coder:7b
```

### Session not persisting
```bash
# Check volume
docker volume ls | grep maximus
docker run --rm -v maximus-sessions:/data alpine ls /data
```

## Resource Requirements

| Configuration | RAM | Disk | GPU |
|---------------|-----|------|-----|
| Min (7b model) | 8GB | 10GB | Optional |
| Recommended (14b) | 16GB | 20GB | 8GB VRAM |
| Large (32b+) | 32GB | 50GB | 16GB VRAM |

## Upgrading

```bash
# Pull latest changes
git pull origin master

# Rebuild containers
docker-compose -f docker-compose.prod.yml build

# Restart with zero-downtime
docker-compose -f docker-compose.prod.yml up -d
```

---

**END OF DEPLOYMENT GUIDE**