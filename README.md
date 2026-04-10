# S3 File Manager - CPPE Project

A secure file management application that allows users to upload, organize, and share files stored in AWS S3 buckets. This application is designed for local deployment on a user's computer.

## 🏗️ Architecture

This application uses a **separate containers architecture** for better maintainability and scalability:

- **Backend Container**: Flask API server running on port 5000
- **Frontend Container**: React app served by Nginx on port 3000
- **Communication**: Frontend nginx proxies `/api/*` requests to backend
- **Database**: External MySQL database (user-provided)
- **Storage**: Local volumes for logs, uploads, and static files

## 🏗️ Project Structure

```
secure_file_storage/
├── backend/                 # Flask API backend
│   ├── app/                # Application package
│   ├── models/             # Database models
│   ├── routes/             # API routes
│   ├── services/           # Business logic services
│   ├── requirements.txt    # Python dependencies
│   ├── run.py             # Application entry point
│   ├── Dockerfile         # Backend container configuration
│   └── .env               # Backend environment variables
├── frontend/               # React frontend
│   ├── src/               # React source code
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   ├── Dockerfile         # Frontend container configuration
│   ├── nginx.conf         # Nginx configuration for serving frontend
│   └── .env              # Frontend environment variables
├── docker-compose.yml     # Multi-service configuration
├── logs/                  # Application logs (created automatically)
├── uploads/               # File uploads (created automatically)
├── static/                # Static files (created automatically)
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- MySQL 8.0+ server (you must provide your own MySQL database)
- AWS Account (for S3 integration)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd secure_file_storage
```

### 2. Configure Backend

```bash
# Copy backend environment template
cp backend/env_example.txt backend/.env

# Edit backend/.env with your MySQL database configuration:
# MYSQL_HOST=your-mysql-host
# MYSQL_USER=your-mysql-username  
# MYSQL_PASSWORD=your-mysql-password
# MYSQL_DB=secure_file_storage
# SECRET_KEY=your-secret-key-here
# AWS_CREDENTIALS_ENCRYPTION_KEY=your-encryption-key-here
```

**Important**: Generate proper encryption keys:
```bash
# Generate Flask secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# Generate AWS credentials encryption key
python3 -c "from cryptography.fernet import Fernet; print('AWS_CREDENTIALS_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### 3. Configure Frontend

```bash
# Copy frontend environment template
cp frontend/env.example frontend/.env

# The frontend .env is already configured for local deployment
# No changes needed unless you want to customize app settings
```

### 4. Deploy the Application

```bash
# Create necessary directories
mkdir -p logs uploads static

# Start both backend and frontend services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 5. Access the Application

- **Application**: http://localhost:3000 (Frontend served by Nginx)
- **Backend API**: http://localhost:5000 (Direct backend access)
- **API Endpoints**: http://localhost:3000/api/* (Proxied through frontend)
- **Health Check**: http://localhost:3000/health

## 🔧 Configuration

### Backend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MYSQL_HOST` | MySQL server hostname | `localhost` or `your-db-host.com` |
| `MYSQL_USER` | MySQL username | `your_username` |
| `MYSQL_PASSWORD` | MySQL password | `your_password` |
| `MYSQL_DB` | Database name | `secure_file_storage` |
| `SECRET_KEY` | Flask secret key | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `AWS_CREDENTIALS_ENCRYPTION_KEY` | Encryption key for AWS credentials | Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `/api` (proxied through nginx) |
| `VITE_APP_NAME` | Application name | `S3 File Manager` |
| `VITE_APP_VERSION` | Application version | `1.0.0` |

## 🗄️ Database Setup

The application automatically:
1. Connects to your MySQL server
2. Creates the database if it doesn't exist
3. Creates all required tables
4. Verifies the setup

No manual database setup is required!

## 🔐 Security Features

- **User Authentication**: Secure login with password hashing
- **2FA Support**: Two-factor authentication with QR codes and recovery codes
- **AWS Credentials Encryption**: User AWS credentials are encrypted at rest
- **Session Management**: Secure session handling with Flask-Login
- **CORS Protection**: Configured for secure cross-origin requests

## 📁 File Management Features

- **Upload Files**: Drag-and-drop file upload to S3
- **Create Folders**: Organize files in folder structures
- **Download Files**: Secure file downloads via presigned URLs
- **Share Files**: Generate shareable links with expiration
- **Delete Files/Folders**: Safe deletion with confirmation
- **File Navigation**: Browse folder structures with breadcrumbs

## 🛠️ Development

### Development Mode

```bash
# Run in development mode with live reloading
docker-compose up --build

# View logs from both services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Container Management

```bash
# Check container status
docker-compose ps

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Stop application
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild specific service
docker-compose build backend
docker-compose build frontend
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify MySQL server is running
   - Check database credentials in `backend/.env`
   - Ensure MySQL server accepts connections from Docker

2. **AWS Credentials Encryption Error**
   - Ensure `AWS_CREDENTIALS_ENCRYPTION_KEY` is properly set in `backend/.env`
   - Generate a new key: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - Restart backend container: `docker-compose restart backend`

3. **Frontend Can't Connect to Backend**
   - Check if both containers are running: `docker-compose ps`
   - Verify backend health: `curl http://localhost:5000/health`
   - Check frontend nginx configuration in `frontend/nginx.conf`

4. **Port Already in Use**
   - Stop existing containers: `docker-compose down`
   - Check for other services using ports 3000 or 5000
   - Modify ports in `docker-compose.yml` if needed

5. **Container Build Failures**
   - Clean Docker cache: `docker system prune -a`
   - Rebuild without cache: `docker-compose build --no-cache`

### Health Checks

- Frontend: `curl http://localhost:3000/health`
- Backend: `curl http://localhost:5000/health`
- Container status: `docker-compose ps`

## 📝 API Documentation

The backend provides a REST API with the following endpoints:

- `GET /api` - API information
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/files/list` - List files/folders
- `POST /api/files/upload` - Upload file
- `POST /api/files/create-folder` - Create folder
- `DELETE /api/files/delete` - Delete file/folder
- `GET /api/files/download` - Download file
- `POST /api/files/share` - Generate share link
- `GET /api/profile` - Get user profile
- `POST /api/profile/update` - Update profile
- `POST /api/aws/connect` - Connect AWS credentials
- `DELETE /api/aws/disconnect` - Disconnect AWS credentials

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📋 Quick Reference

### Essential Commands

```bash
# Start application
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Check status
docker-compose ps

# Restart backend only
docker-compose restart backend

# Rebuild frontend only
docker-compose build frontend
```

### Key URLs

- **Application**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:3000/health

### Important Files

- **Backend Config**: `backend/.env`
- **Frontend Config**: `frontend/.env`
- **Docker Compose**: `docker-compose.yml`
- **Backend Dockerfile**: `backend/Dockerfile`
- **Frontend Dockerfile**: `frontend/Dockerfile`

## 🤝 Support

For support and questions, please check the troubleshooting section above or create an issue in the project repository.
