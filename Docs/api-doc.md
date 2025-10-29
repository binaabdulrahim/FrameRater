# FrameRatr Backend API

## Base URL
```
http://localhost:3000
```

## Authentication
Some endpoints require Firebase JWT token:
```bash
Authorization: Bearer <firebase-id-token>
```

## Endpoints

### Health Check
```http
GET /health
```
Response:
```json
{"ok": true}
```

### Search Movies
```http
GET /api/tmdb/search/movies?q=batman
```

### Get Movie Details
```http
GET /api/tmdb/movie/155
```

### User Endpoints (Auth Required)
```http
GET /api/me
POST /api/ratings
POST /api/reviews
GET /api/favorites/movies
```

Full endpoint list: Run `python test_api.py` to see all available endpoints.