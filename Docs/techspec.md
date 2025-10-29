# FrameRatr Backend - Complete Deployment Documentation

## Overview

This document explains the complete AWS infrastructure for the FrameRatr backend, why we chose each service, and how everything connects together.

---

## Architecture Diagram

## Live URLs

### API Endpoint
```
http://frameratr-dev-alb-1434013349.us-east-2.elb.amazonaws.com
```

### Database Endpoint
```
frameratr-dev-db.cpkugwuc4hp0.us-east-2.rds.amazonaws.com:5432
```

### Docker Registry
```
451904790164.dkr.ecr.us-east-2.amazonaws.com/frameratr-dev-backend
```

### ECS Cluster
```
frameratr-dev-cluster

## AWS Services Used

### 1. Application Load Balancer (ALB)

**What it is:** A traffic router that distributes incoming requests to your backend containers.

**Why we use it:**
- Gives you a stable public URL
- Performs health checks - if your app crashes, ALB stops sending traffic to it
- Enables HTTPS when you add a domain and SSL certificate
- Handles high traffic by routing to multiple containers

**How it works:**
1. User makes request: `GET http://your-alb-url.com/api/movies`
2. ALB receives it on port 80
3. ALB forwards to your ECS container on port 3000
4. Your Flask app responds
5. ALB sends response back to user

### 2. ECS (Elastic Container Service) with Fargate

**What it is:** A service that runs your Docker containers without managing servers.

**Why we use it:**
- Serverless - no EC2 servers to manage
- Auto-scaling - automatically adds more containers when traffic increases
- Pay only for what you use - charged per second
- Always running - restarts if it crashes

**How it works:**
1. You push Docker image to ECR
2. ECS pulls the image and runs it
3. Your Flask app starts on port 3000
4. ECS registers it with the load balancer
5. Health checks run every 30 seconds to `/health` endpoint

**Configuration:**
- CPU: 0.25 vCPU (256)
- Memory: 512 MB
- Scaling: 1-4 containers
- Network: Private subnet (not directly accessible from internet)

### 3. RDS (Relational Database Service) - PostgreSQL

**What it is:** A managed PostgreSQL database.

**Why we use it instead of Docker:**
- Data persistence - data survives container restarts
- Automatic backups - daily snapshots
- Security - in private subnet, encrypted
- Maintenance - AWS handles updates
- Scalability - easy to upgrade storage/compute

**Configuration:**
- Engine: PostgreSQL 16.10
- Instance: db.t3.micro (free tier eligible)
- Storage: 20 GB
- Database Name: frameratr
- Username: fr_user
- Password: fr_password (stored in Secrets Manager)

**Security:**
- In private subnet - not accessible from internet
- Only ECS containers can connect
- Security group only allows port 5432 from ECS

### 4. ECR (Elastic Container Registry)

**What it is:** A private Docker image storage.

**Why we use it:**
- Private - only your AWS account can access
- Fast - in same region as ECS
- Secure - integrated with AWS IAM
- Versioned - keeps multiple versions of your images

**How it works:**
1. Build Docker image locally: `docker build -t frameratr-backend .`
2. Tag it: `docker tag frameratr-backend:latest <ecr-url>:latest`
3. Push it: `docker push <ecr-url>:latest`
4. ECS pulls from ECR when deploying

### 5. Secrets Manager

**What it is:** Secure storage for sensitive data (passwords, API keys).

**Why we use it:**
- Never hardcode secrets in your code
- Encrypted at rest
- Rotation - can automatically rotate passwords
- Audit trail - logs who accessed what

**What's stored:**
```json
{
  "DB_HOST": "frameratr-dev-db.cpkugwuc4hp0.us-east-2.rds.amazonaws.com",
  "DB_PORT": "5432",
  "DB_NAME": "frameratr",
  "DB_USER": "fr_user",
  "DB_PASS": "fr_password",
  "TMDB_TOKEN": "eyJhbGci...",
  "TMDB_SLEEP_SEC": "0.25",
  "FLASK_PORT": "3000"
}
```

**How ECS uses it:**
- ECS task definition references secrets by ARN
- At runtime, ECS fetches secrets and injects as environment variables
- Your Flask app reads them: `os.getenv("DB_HOST")`

### 6. VPC (Virtual Private Cloud)

**What it is:** Your private network in AWS.

**Why we use it:**
- Network isolation - your resources are separate from others
- Security - control what can talk to what
- Subnets - public (for ALB) and private (for ECS/RDS)

**Configuration:**
- CIDR Block: 10.0.0.0/16
- Public Subnets: 10.0.1.0/24, 10.0.2.0/24 (for load balancer)
- Private Subnets: 10.0.10.0/24, 10.0.11.0/24 (for ECS & RDS)
- NAT Gateway: Allows private subnets to access internet (for pulling Docker images)

---

### 7. Security Groups (Firewalls)

**What they are:** Virtual firewalls controlling network access.

**Configuration:**

#### ALB Security Group:
- Inbound:
  - Port 80 (HTTP) from anywhere (0.0.0.0/0)
  - Port 443 (HTTPS) from anywhere (when you add SSL)
- Outbound: All traffic

#### ECS Security Group:
- Inbound:
  - Port 3000 from ALB security group only
- Outbound: All traffic

#### RDS Security Group:
- Inbound:
  - Port 5432 from ECS security group only
- Outbound: All traffic

**Why this matters:**
- Internet can access ALB: Yes
- Internet cannot access ECS directly: Correct
- Internet cannot access RDS directly: Correct
- ALB can access ECS: Yes
- ECS can access RDS: Yes

---

### 8. CloudWatch Logs

**What it is:** Log storage and monitoring.

**Why we use it:**
- Debug issues - see what your app is logging
- Monitor errors - set up alerts
- Audit trail - compliance

**How to view logs:**
```bash
aws logs tail /ecs/frameratr-dev-backend --follow
```

## How Everything Connects

### Request Flow (Step by Step):

```
1. User makes request
   ↓
2. DNS resolves to ALB (frameratr-dev-alb-xxx.amazonaws.com)
   ↓
3. ALB receives request on port 80
   ↓
4. ALB forwards to ECS container on port 3000
   ↓
5. ECS container (Flask app) receives request
   ↓
6. Flask app needs database connection
   ↓
7. Flask reads DB_HOST from environment (injected by Secrets Manager)
   ↓
8. Flask connects to RDS on port 5432
   ↓
9. RDS returns data
   ↓
10. Flask processes and returns response
    ↓
11. Response goes back through ALB to user
```

## Security Architecture

### Layers of Security:

1. **Network Layer (VPC)**
   - Private subnets isolate database and app
   - NAT Gateway for outbound internet access only
   - No direct internet access to backend or database

2. **Firewall Layer (Security Groups)**
   - ALB: Open to internet on port 80
   - ECS: Only accepts traffic from ALB
   - RDS: Only accepts traffic from ECS

3. **Authentication Layer (IAM)**
   - ECS execution role: Can pull images from ECR
   - ECS task role: Can read from Secrets Manager
   - Least privilege principle

4. **Application Layer (Firebase)**
   - User authentication handled by Firebase
   - JWT tokens validated on each request
   - Backend verifies tokens before processing

5. **Data Layer (Encryption)**
   - RDS: Encrypted at rest
   - Secrets Manager: Encrypted at rest
   - SSL/TLS: Can add for data in transit

### Current Setup (Manual):

1. Make code changes locally
2. Build Docker image:
   ```bash
   docker buildx build --platform linux/amd64 -t frameratr-backend .
   ```
3. Tag image:
   ```bash
   docker tag frameratr-backend:latest 451904790164.dkr.ecr.us-east-2.amazonaws.com/frameratr-dev-backend:latest
   ```
4. Push to ECR:
   ```bash
   docker push 451904790164.dkr.ecr.us-east-2.amazonaws.com/frameratr-dev-backend:latest
   ```
5. Force new deployment:
   ```bash
   aws ecs update-service --cluster frameratr-dev-cluster --service frameratr-dev-backend-service --force-new-deployment --region us-east-2
   ```

## Infrastructure Management (Terraform)

### What is Terraform?

Terraform is "Infrastructure as Code" - you describe your infrastructure in config files, and Terraform creates it.

**Benefits:**
- Version control - infrastructure changes tracked in Git
- Reproducible - can recreate entire setup with one command
- Documentation - config files are self-documenting
- Collaboration - teammates can see and modify infrastructure

### Files Created:

```
backend/terraform/
├── main.tf           # VPC, ALB, RDS, Security Groups
├── ecs.tf            # ECS cluster, task definition, service
└── terraform.tfvars  # Variables (database password)
```
### Common Commands:

```bash
# See what will be created/changed
terraform plan

# Apply changes
terraform apply

# Destroy everything (careful!)
terraform destroy

# Show current state
terraform show
```

---

## Testing Deployment

### 1. Health Check
```bash
curl http://frameratr-dev-alb-1434013349.us-east-2.elb.amazonaws.com/health
# Expected: {"ok": true}
```

### 2. Search Movies (TMDb API)
```bash
curl "http://frameratr-dev-alb-1434013349.us-east-2.elb.amazonaws.com/api/tmdb/search/movies?q=batman"
# Expected: JSON with movie results
```

### 3. Trending Movies
```bash
curl http://frameratr-dev-alb-1434013349.us-east-2.elb.amazonaws.com/api/tmdb/trending/movies
# Expected: JSON with trending movies
```

### 4. Check Logs
```bash
aws logs tail /ecs/frameratr-dev-backend --follow --region us-east-2
```

### 5. Check ECS Service Status
```bash
aws ecs describe-services \
  --cluster frameratr-dev-cluster \
  --services frameratr-dev-backend-service \
  --region us-east-2 \
  --query 'services[0].runningCount'
# Expected: 1
```

---

### Endpoints That Need Database (Not Working Yet)

These will return errors until we set up database tables:
- `GET /api/movies` - List movies from database
- `GET /api/movies/123` - Get movie details from database
- `POST /api/ratings` - Add user rating
- `POST /api/reviews` - Add user review
- `GET /api/favorites/movies` - Get user favorites

---

## Next Steps

### Immediate (Required for User Features):

1. Set up database tables
   - Run `schema.sql` to create tables
   - Options: Connect via ECS task or temporarily open security group

2. Test authenticated endpoints
   - Create test user in Firebase (done)
   - Test rating/review/favorite features
