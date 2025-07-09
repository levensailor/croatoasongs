#!/bin/bash

# Quick redeploy script for songs application
# This script updates the existing deployment without full setup

SERVER_IP="3.91.153.20"
SERVER_USER="ec2-user"
KEY_PATH="~/.ssh/aws-2024.pem"

echo "🔄 Redeploying songs application..."

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf songs-app.tar.gz \
  --exclude='.git' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='log_archive' \
  --exclude='*.db' \
  --exclude='deploy.sh' \
  --exclude='redeploy.sh' \
  --exclude='dns-record.json' \
  .

# Upload and redeploy
echo "📤 Uploading and redeploying..."
scp -i $KEY_PATH songs-app.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP << 'EOF'
# Stop the application
sudo systemctl stop songs

# Update application files
cd /var/www/songs
tar -xzf /tmp/songs-app.tar.gz
rm /tmp/songs-app.tar.gz

# Restart the application
sudo systemctl start songs
sudo systemctl restart nginx

echo "✅ Application redeployed successfully!"
EOF

# Clean up
rm songs-app.tar.gz

echo "✅ Redeploy completed!"
echo "🌐 Application available at: http://songs.croatoa.live"
echo "📊 Check status: ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'sudo systemctl status songs'"
