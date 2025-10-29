# FrameRatr

> Movie discovery platform with ratings, reviews, and personalized recommendations

## Features

- Search 1M+ movies & TV shows (TMDb API)
- Rate and review content
- Save favorites
- Secure authentication (Firebase)
- Production-ready AWS deployment
- Enterprise security (AWS Secrets Manager)

## Quick Start
```bash
# 1. Clone
git clone https://github.com/your-username/FrameRatr.git
cd FrameRatr

# 2. Set up secrets (AWS)
cd backend
python setup_secrets.py

# 3. Start services
docker compose up --build
```

## Architecture

- **Backend**: Flask + PostgreSQL + TMDb API
- **Auth**: Firebase Authentication
- **Deployment**: AWS ECS + RDS + ALB
- **Secrets**: AWS Secrets Manager

## Documentation

- [Setup Guide](Docs/README.md)
- [Tech Spec](Docs/techspec.md)
- [API Documentation](backend/README.md)

## Team

Built by FrameRatr 