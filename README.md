# VaultOS — Secure File Locker

Enterprise-grade encrypted file storage with ML threat intelligence, two-factor authentication, REST API, real-time notifications, and cloud integration.

## ✨ Features

### Core Security
- **AES-256-CBC encryption** with PBKDF2-HMAC-SHA256 key derivation (100K iterations)
- **Two-Factor Authentication (2FA)** — Google Authenticator TOTP integration
- **Brute-force protection** — account lock after 5 failed login attempts
- **File sharing** with expiry links, max-download limits, and revocation

### ML Intelligence Layer
- **Random Forest Classifier** — 150-tree model trained on 900+ samples, predicts file category
- **Isolation Forest** — anomaly detection for suspicious upload patterns
- **Composite Threat Scorer** — combines ML signals + heuristics into 0–1 risk score
- **Real-time ML pre-scan** — threat analysis before you even submit the upload

### REST API + JWT
- Full programmatic API at `/api/v1/` with JWT Bearer token authentication
- Endpoints: login, list/upload/download/delete files, ML scan, admin stats
- Enables integration with external applications and automation

### Real-Time Notifications (WebSocket)
- **Flask-SocketIO** powered live toast notifications
- Instant alerts when someone shares a file with you
- Admin alerts on HIGH/CRITICAL threat uploads

### Cloud Integration (AWS — Optional)
- **S3** — encrypted file backup storage
- **SNS** — email alerts for high-threat uploads
- **CloudWatch** — cloud audit logs with 90-day retention
- **Terraform IaC** — one-click AWS infrastructure provisioning

### DevOps Pipeline
- **11-stage Jenkinsfile** — checkout, setup, lint, ML train, unit tests, integration tests, coverage, SonarQube, Docker, deploy
- **SonarQube** quality gate for code analysis and security scanning
- **Dockerfile** with Gunicorn for production deployment

### UI/UX
- **Dark/Light theme** toggle with localStorage persistence
- **File preview** — decrypt and view images, PDFs, text files in the browser
- **Glassmorphism design** with Inter + JetBrains Mono fonts
- **Admin dashboard** with threat analytics, ML model status, AWS status, audit logs

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd secure-locker-v2
python -m venv venv
.\venv\Scripts\Activate   # Windows
pip install -r requirements.txt
python run.py
# → http://localhost:5000

# Default admin: admin / Admin@1234
```

---

## 🧪 Run Tests

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov=ml_engine --cov-report=term-missing
```

**65 tests** covering crypto, ML engine, auth, locker, admin, 2FA, preview, REST API, and AWS integration.

---

## 🔌 REST API Usage

```bash
# 1. Get JWT token
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@1234"}' | jq -r '.token')

# 2. List files
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/files

# 3. Upload a file
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" -F "password=mypass123" \
  http://localhost:5000/api/v1/files/upload

# 4. ML threat scan
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename":"suspicious.exe","size":500000}' \
  http://localhost:5000/api/v1/ml/scan
```

---

## 🛡️ Two-Factor Authentication

1. Log in → Click **"Enable 2FA"** on the dashboard
2. Scan the QR code with Google Authenticator
3. Enter the 6-digit code to verify
4. On future logins, you'll be prompted for your TOTP code after password

---

## ☁️ AWS Integration (Optional)

Set these environment variables to activate cloud features:

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your-bucket-name
AWS_SNS_TOPIC_ARN=arn:aws:sns:...
AWS_CLOUDWATCH_GROUP=VaultOS
```

Or use Terraform for one-click provisioning:

```bash
cd terraform
terraform init
terraform apply -var="notification_email=your@email.com"
```

---

## 📁 Project Structure

```
secure-locker-v2/
├── app/
│   ├── __init__.py          # Flask app factory + blueprint registration
│   ├── models.py            # User, LockedFile, SharedFile, AuditLog models
│   ├── auth.py              # Register, login (with 2FA redirect), logout
│   ├── locker.py            # Upload, download, delete, file detail, ML scan
│   ├── admin.py             # Admin dashboard, user management, threats, audit
│   ├── sharing.py           # File sharing with expiry links
│   ├── crypto_utils.py      # AES-256-CBC encrypt/decrypt + PBKDF2 key derivation
│   ├── audit.py             # Audit logging (local + CloudWatch)
│   ├── two_factor.py        # 2FA setup, verify, enable, disable (TOTP)
│   ├── preview.py           # In-browser file preview (images, PDFs, text)
│   ├── api.py               # REST API + JWT authentication
│   └── notifications.py     # WebSocket real-time notifications
├── ml_engine/
│   ├── __init__.py
│   └── engine.py            # Random Forest + Isolation Forest + Threat Scorer
├── aws_integration/
│   ├── config.py            # AWS auto-detection + connectivity check
│   ├── s3_storage.py        # S3 encrypted file storage
│   ├── sns_alerts.py        # SNS threat alert emails
│   └── cloudwatch_logger.py # CloudWatch audit log streaming
├── terraform/
│   ├── main.tf              # AWS infrastructure definition
│   ├── variables.tf         # Input variables
│   ├── outputs.tf           # Output values → env vars
│   └── README.md            # Terraform usage guide
├── templates/               # Jinja2 HTML templates (glassmorphism UI)
├── tests/
│   └── test_all.py          # 65 tests across all modules
├── Jenkinsfile              # 11-stage CI/CD pipeline
├── Dockerfile               # Production container
├── sonar-project.properties # SonarQube code analysis config
├── requirements.txt         # Python dependencies
└── run.py                   # Entry point (with SocketIO support)
```

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.0, SQLAlchemy, Flask-Login |
| Encryption | AES-256-CBC, PBKDF2-HMAC-SHA256 |
| 2FA | pyotp (TOTP), qrcode (QR generation) |
| ML | scikit-learn (Random Forest, Isolation Forest) |
| API | PyJWT (JWT tokens), RESTful JSON |
| Real-time | Flask-SocketIO, WebSocket |
| Cloud | AWS S3, SNS, CloudWatch, boto3 |
| IaC | Terraform (HCL) |
| CI/CD | Jenkins (11 stages), SonarQube, Docker |
| Frontend | Jinja2, vanilla CSS (glassmorphism), SocketIO client |

