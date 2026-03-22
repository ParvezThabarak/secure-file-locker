# Project Structure

This document describes the structure of the S3 File Manager Backend project.

## 📁 Directory Structure

```
secure_file_storage/
├── app/                           # Main application package
│   ├── __init__.py               # Application factory
│   ├── config/                   # Configuration package
│   │   ├── __init__.py
│   │   └── config.py            # Configuration classes
│   └── database/                 # Database package
│       ├── __init__.py
│       └── database.py          # Database instance
├── models/                       # Database models
│   ├── user.py                  # User model
│   └── file.py                  # File model
├── routes/                       # API routes
│   ├── auth.py                  # Authentication routes
│   ├── files.py                 # File management routes
│   ├── profile.py               # Profile management routes
│   └── aws_credentials.py       # AWS credentials routes
├── services/                     # Business logic services
├── static/                       # Static files
├── logs/                         # Application logs
├── migrations/                   # Database migrations
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
├── docker-compose.prod.yml      # Production Docker Compose
├── Makefile                      # Make commands
├── setup.sh                      # Setup script
├── env_example.txt               # Environment variables template
├── README.md                     # Project documentation
├── DEPLOYMENT.md                 # Deployment guide
└── PROJECT_STRUCTURE.md          # This file
```

## 🏗️ Architecture

### Application Factory Pattern
The application uses Flask's application factory pattern for better organization and testing:

- `app/__init__.py`: Creates and configures the Flask application
- `run.py`: Application entry point that creates the app instance

### Configuration Management
Configuration is handled through environment variables and configuration classes:

- `app/config/config.py`: Configuration classes for different environments
- `env_example.txt`: Template for environment variables

### Database Management
Database operations are organized in a dedicated package:

- `app/database/database.py`: SQLAlchemy database instance
- `models/`: Database models (User, File)
- `migrations/`: Database migration files

### API Routes
API endpoints are organized by functionality:

- `routes/auth.py`: Authentication endpoints
- `routes/files.py`: File management endpoints
- `routes/profile.py`: User profile endpoints
- `routes/aws_credentials.py`: AWS integration endpoints

### Business Logic
Business logic is separated into services:

- `services/`: Contains business logic and external service integrations

## 🔧 Key Files

### Core Application Files
- `run.py`: Application entry point
- `app/__init__.py`: Application factory
- `app/config/config.py`: Configuration management
- `app/database/database.py`: Database setup

### Models
- `models/user.py`: User model with authentication and 2FA
- `models/file.py`: File model with S3 integration

### Routes
- `routes/auth.py`: User registration, login, logout
- `routes/files.py`: File upload, download, management
- `routes/profile.py`: Profile management, 2FA setup
- `routes/aws_credentials.py`: AWS S3 credentials management

### Configuration Files
- `requirements.txt`: Python dependencies
- `Dockerfile`: Docker container configuration
- `docker-compose.yml`: Development Docker setup
- `docker-compose.prod.yml`: Production Docker setup
- `Makefile`: Common commands and tasks
- `setup.sh`: Automated setup script

### Documentation
- `README.md`: Project overview and setup instructions
- `DEPLOYMENT.md`: Deployment guide
- `PROJECT_STRUCTURE.md`: This file

## 🚀 Getting Started

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd secure_file_storage

# Run setup script
./setup.sh
```

### Manual Setup
```bash
# Copy environment file
cp env_example.txt .env

# Edit .env with your configuration
nano .env

# Build and start with Docker
docker-compose up --build -d

# Initialize database
docker-compose exec app flask db init
docker-compose exec app flask db migrate -m "Initial migration"
docker-compose exec app flask db upgrade
```

### Using Make Commands
```bash
# View all available commands
make help

# Quick start
make quick-start

# Development
make dev

# Database operations
make migrate
make migrate-create MESSAGE="Add new feature"

# Production
make prod-up
make prod-logs
```

## 🔄 Development Workflow

### Adding New Features
1. Create new model in `models/` if needed
2. Add routes in `routes/`
3. Implement business logic in `services/`
4. Create database migration
5. Update documentation

### Database Changes
```bash
# Create migration
make migrate-create MESSAGE="Description of changes"

# Apply migration
make migrate-upgrade

# Rollback if needed
make migrate-downgrade
```

### Testing
```bash
# Run tests
make test

# Run tests with coverage
make test-coverage
```

## 📦 Deployment

### Development
```bash
make dev
```

### Production
```bash
make prod-up
```

### Docker Commands
```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## 🔍 Monitoring

### Health Checks
- `GET /health`: Basic health check
- `GET /api`: API information

### Logs
- Development: Console output
- Production: `logs/app.log`

### Status Check
```bash
make status
```

## 🛠️ Maintenance

### Database Backup
```bash
make backup-db
```

### Clean Up
```bash
make clean
```

### Environment Check
```bash
make env-check
```

## 📚 Additional Resources

- [README.md](README.md): Complete project documentation
- [DEPLOYMENT.md](DEPLOYMENT.md): Detailed deployment guide
- [API Documentation](README.md#api-documentation): API endpoint reference
- [Security Features](README.md#security-features): Security implementation details
