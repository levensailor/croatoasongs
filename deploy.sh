#!/bin/bash

# Deployment script for songs application
# Deploy to EC2 instance with songs.croatoa.live domain

SERVER_IP="3.91.153.20"
SERVER_USER="ec2-user"
KEY_PATH="~/.ssh/aws-2024.pem"
APP_NAME="songs"

echo "🚀 Deploying songs application to songs.croatoa.live..."

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf songs-app.tar.gz \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='log_archive' \
  --exclude='*.db' \
  .

# Upload files to server
echo "📤 Uploading files to server..."
scp -i $KEY_PATH songs-app.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

# Deploy on server
echo "🔧 Setting up application on server..."
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP << 'EOF'
# Install required packages
sudo yum update -y
sudo yum install -y python3 python3-pip git
sudo amazon-linux-extras install nginx1

# Create app directory
sudo mkdir -p /var/www/songs
sudo chown ec2-user:ec2-user /var/www/songs

# Extract application
cd /var/www/songs
tar -xzf /tmp/songs-app.tar.gz
rm /tmp/songs-app.tar.gz

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/songs.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Songs FastAPI Application
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/var/www/songs
Environment=PATH=/var/www/songs/venv/bin
ExecStart=/var/www/songs/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Configure nginx
sudo tee /etc/nginx/conf.d/songs.conf > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name songs.croatoa.live;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_EOF

# Start services
sudo systemctl daemon-reload
sudo systemctl enable songs
sudo systemctl start songs
sudo systemctl enable nginx
sudo systemctl start nginx

echo "✅ Application deployed successfully!"
echo "🌐 Access at: http://songs.croatoa.live"
EOF

# Clean up
rm songs-app.tar.gz

echo "✅ Deployment completed!"
echo "🌐 Application should be available at: http://songs.croatoa.live"
echo "📊 Check status: ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'sudo systemctl status songs'"
echo ""
echo "🔒 To enable HTTPS with SSL certificate, run:"
echo "    ./setup-ssl.sh"
echo ""
