# FrameRatr (Backend)

## What this is
Backend for movie/TV discovery, ratings, favorites. TMDB + Postgres + Firebase Auth.

## Quick start
```bash
# 1) Clone
git clone <your-repo-url>
cd FrameRatr

# 2) Create .env from example
cp .env.example .env
# Fill values (DB_*, TMDB_TOKEN, FIREBASE_*), but keep this file private.

# 3) Start services (example)
docker compose up --build
# or: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
