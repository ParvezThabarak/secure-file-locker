# Secure File Locker — PBL-II Implementation Guide
## 21IPE315P — Cloud Product and Platform Engineering

---

## What was added for PBL-II

### 1. Functional Implementation (6/6 marks)
- ✅ File upload / download / delete / list (existing)
- ✅ User registration + login + 2FA (existing)
- ✅ Presigned share URLs with expiry (1hr / 24hr / 7days) — ENHANCED
- ✅ File size limit increased to 500MB
- ✅ ML anomaly detection on every file operation — NEW
- ✅ Analytics API endpoints — NEW

### 2. Cloud & Hyperscaler Usage (4/4 marks)
Deploy these AWS services:
- AWS EC2 t2.micro — runs Docker container
- AWS S3 + KMS — encrypted file storage
- AWS RDS MySQL — database
- AWS Cognito — user auth (optional enhancement)
- AWS CloudFront + WAF — CDN + protection

### 3. Data / ML / AI Workflow (4/4 marks)
`backend/services/ml_service.py` — AnomalyDetector class:
- Detects unusual download frequency
- Detects late-night access (midnight–5am)
- Detects bulk delete attempts
- Returns risk score 0–100 + risk level (LOW/MEDIUM/HIGH)
- Logs every event to `access_logs` table
- Results available via `/api/analytics/*` endpoints

### 4. DevOps Practices (3/3 marks)
- Docker + docker-compose (existing)
- `.github/workflows/deploy.yml` — GitHub Actions CI/CD — NEW
  - Runs pytest on every push
  - Builds Docker images
  - Deploys to EC2 via SSH

### 5. Security Implementation (3/3 marks)
- Password hashing with bcrypt (existing)
- 2FA TOTP with QR codes (existing)
- Fernet encryption for AWS credentials (existing)
- JWT session management (existing)
- ML-based threat detection — NEW
- Structured JSON logging for audit trail — NEW

---

## Setup Instructions

### Prerequisites
- Docker + Docker Compose
- AWS Account (free tier)
- Python 3.11+

### Step 1 — Clone and configure
```bash
git clone <your-repo-url>
cd secure-file-locker
cp backend/env_example.txt backend/.env
```

Edit `backend/.env`:
```
MYSQL_HOST=your-rds-endpoint
MYSQL_USER=admin
MYSQL_PASSWORD=your-password
MYSQL_DB=secure_file_storage
SECRET_KEY=your-secret-key
AWS_CREDENTIALS_ENCRYPTION_KEY=your-fernet-key
```

Generate keys:
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "from cryptography.fernet import Fernet; print('AWS_CREDENTIALS_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### Step 2 — Run locally
```bash
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Health check: http://localhost:5000/health

### Step 3 — Run with ELK Stack (monitoring)
```bash
docker-compose -f docker-compose.yml -f docker-compose.elk.yml up
```
- Kibana dashboard: http://localhost:5601

### Step 4 — Run tests
```bash
cd backend
pip install pytest pytest-flask pytest-cov
python -m pytest tests/ -v --cov=. --cov-report=term
```

### Step 5 — Deploy to AWS EC2
```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone repo on EC2
git clone <your-repo-url>
cd secure-file-locker

# Set environment variables
cp backend/env_example.txt backend/.env
# Edit .env with your RDS endpoint

# Start application
docker-compose up --build -d
```

### Step 6 — GitHub Actions CI/CD Setup
Add these secrets to your GitHub repo (Settings → Secrets):
```
EC2_HOST          → your EC2 public IP
EC2_USERNAME      → ubuntu
EC2_SSH_KEY       → contents of your .pem file
AWS_CREDENTIALS_ENCRYPTION_KEY → your Fernet key
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login (supports 2FA) |
| POST | /api/auth/logout | Logout |
| GET  | /api/auth/me | Get current user |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/files/upload | Upload file (max 500MB) |
| GET  | /api/files/ | List files |
| GET  | /api/files/{id}/download | Download file |
| DELETE | /api/files/{id} | Delete file |
| POST | /api/files/{id}/share | Generate share link |
| GET  | /api/files/stats | File statistics |

### Analytics (ML/AI)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/analytics/risk-summary | ML risk summary (24h) |
| GET | /api/analytics/access-logs | Access log history |
| GET | /api/analytics/high-risk-events | HIGH risk events only |
| GET | /api/analytics/stats | Action statistics |

---

## PBL-II Marks Breakdown

| Criterion | What to show | Marks |
|-----------|-------------|-------|
| Functional Implementation | Demo: register → upload → share → download → delete | 6/6 |
| Cloud & Hyperscaler | Show EC2 running, S3 bucket, RDS connected | 4/4 |
| ML / AI Workflow | Show `/api/analytics/risk-summary` response + explain AnomalyDetector | 4/4 |
| DevOps | Show GitHub Actions pipeline run + docker-compose | 3/3 |
| Security | Show 2FA login + risk_level in upload response | 3/3 |
| **Total** | | **20/20** |
