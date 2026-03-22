#!/bin/bash
# ============================================================
# Secure File Locker — EC2 Setup Script
# 21IPE315P — Cloud Product and Platform Engineering
#
# Run this ONCE on a fresh EC2 Ubuntu instance:
#   chmod +x setup.sh
#   ./setup.sh
# ============================================================

echo "================================================"
echo " Secure File Locker — EC2 Setup"
echo " 21IPE315P Cloud Product and Platform Engineering"
echo "================================================"

# Step 1 — Update system
echo ""
echo "Step 1: Updating system..."
sudo apt update -y
sudo apt upgrade -y

# Step 2 — Install Docker
echo ""
echo "Step 2: Installing Docker..."
sudo apt install -y docker.io docker-compose git curl unzip
sudo usermod -aG docker ubuntu
sudo systemctl start docker
sudo systemctl enable docker

# Step 3 — Generate secret keys
echo ""
echo "Step 3: Generating secret keys..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

echo ""
echo "================================================"
echo " YOUR SECRET KEYS (save these!)"
echo "================================================"
echo "SECRET_KEY=$SECRET_KEY"
echo "AWS_CREDENTIALS_ENCRYPTION_KEY=$FERNET_KEY"
echo "================================================"

# Step 4 — Create .env file
echo ""
echo "Step 4: Creating .env file..."
cat > /home/ubuntu/secure-file-locker/backend/.env << EOF
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
MYSQL_HOST=mysql
MYSQL_USER=sfluser
MYSQL_PASSWORD=sflpass123
MYSQL_ROOT_PASSWORD=sflroot123
MYSQL_DB=secure_file_storage
AWS_CREDENTIALS_ENCRYPTION_KEY=$FERNET_KEY
CORS_ORIGINS=http://localhost:3000,http://$(curl -s ifconfig.me):3000
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

echo ".env file created!"

# Step 5 — Create required directories
echo ""
echo "Step 5: Creating directories..."
mkdir -p /home/ubuntu/secure-file-locker/logs
mkdir -p /home/ubuntu/secure-file-locker/uploads
mkdir -p /home/ubuntu/secure-file-locker/static

# Step 6 — Start application
echo ""
echo "Step 6: Starting application..."
cd /home/ubuntu/secure-file-locker
sudo docker-compose up --build -d

# Step 7 — Wait and verify
echo ""
echo "Waiting for containers to start (30 seconds)..."
sleep 30

echo ""
echo "Checking container status..."
sudo docker-compose ps

# Step 8 — Health check
echo ""
echo "Running health check..."
curl -s http://localhost:5000/health && echo "" || echo "Backend starting up..."

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "================================================"
echo " SETUP COMPLETE!"
echo "================================================"
echo ""
echo " Your app is running at:"
echo " Frontend:  http://$PUBLIC_IP:3000"
echo " Backend:   http://$PUBLIC_IP:5000"
echo " Grafana:   http://$PUBLIC_IP:3001"
echo " Health:    http://$PUBLIC_IP:5000/health"
echo ""
echo " Grafana login:"
echo " Username: admin"
echo " Password: admin123"
echo ""
echo " Next steps:"
echo " 1. Open http://$PUBLIC_IP:3000 in browser"
echo " 2. Register an account"
echo " 3. Connect your AWS S3 bucket"
echo " 4. Upload a test file"
echo "================================================"
