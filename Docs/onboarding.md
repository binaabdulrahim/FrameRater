# FrameRatr Team Onboarding

Welcome to the team! Here's how to get started.

## Prerequisites

- Python 3.11+
- Docker Desktop
- AWS CLI
- Git

## Setup Steps

### 1. Clone Repository
```bash
git clone https://github.com/your-org/FrameRatr.git
cd FrameRatr
```

### 2. Get AWS Credentials
- AWS Access Key ID
- AWS Secret Access Key

### 3. Configure AWS CLI
```bash
aws configure
# Enter the credentials from step 2
# Region: us-east-2
# Format: json
```

### 4. Fetch Secrets
```bash
cd backend
pip install boto3
python setup_secrets.py
```

This creates:
- `.env` file with environment variables
- `firebase-service-account.json` with Firebase credentials

### 5. Start Backend
```bash
cd ..
docker compose up --build
```

### 6. Test API
```bash
curl http://localhost:3000/health
# Expected: {"ok": true}
```

### 7. Run Tests
```bash
cd backend
python test_api.py
```

## Common Issues

**Issue:** `setup_secrets.py` fails with "Access Denied"
**Fix:** Make sure you ran `aws configure` with correct credentials

**Issue:** Docker won't start
**Fix:** Make sure Docker Desktop is running

**Issue:** Database connection fails
**Fix:** Wait 10 seconds after `docker compose up` for DB to initialize
