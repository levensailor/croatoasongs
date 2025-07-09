#!/bin/bash

# SSL Setup Script for songs.croatoa.live
# Sets up Let's Encrypt certificate with automatic renewal

SERVER_IP="3.91.153.20"
SERVER_USER="ec2-user"
KEY_PATH="~/.ssh/aws-2024.pem"
DOMAIN="songs.croatoa.live"

echo "🔒 Setting up SSL certificate for $DOMAIN..."

ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP << 'EOF'
# Install certbot for Let's Encrypt
sudo amazon-linux-extras install epel
sudo yum install -y certbot python2-certbot-nginx

# Generate SSL certificate and configure nginx automatically
sudo certbot --nginx \
  -d songs.croatoa.live \
  --non-interactive \
  --agree-tos \
  --email jeff@levensailor.com \
  --redirect

# Add security headers to nginx configuration
sudo tee -a /etc/nginx/conf.d/songs.conf > /dev/null << 'SECURITY_EOF'

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
SECURITY_EOF

# Restart nginx to apply changes
sudo systemctl restart nginx

# Set up automatic certificate renewal
sudo tee /etc/systemd/system/certbot-renew.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Certbot Renewal Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"
User=root
SERVICE_EOF

# Create timer for automatic renewal (runs twice daily)
sudo tee /etc/systemd/system/certbot-renew.timer > /dev/null << 'TIMER_EOF'
[Unit]
Description=Run certbot renewal twice daily
Requires=certbot-renew.service

[Timer]
OnCalendar=*-*-* 00,12:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
TIMER_EOF

# Enable and start the renewal timer
sudo systemctl daemon-reload
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer

# Test certificate renewal (dry run)
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates

echo "✅ SSL certificate setup complete!"
echo "🔒 HTTPS enabled for songs.croatoa.live"
echo "🔄 Automatic renewal configured"
EOF

echo "✅ SSL setup completed!"
echo "🔒 Application now available at: https://songs.croatoa.live"
echo "🔄 Certificate will auto-renew every 12 hours"
echo "📊 Check certificate status: ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'sudo certbot certificates'"
