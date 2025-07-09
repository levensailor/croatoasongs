#!/bin/bash

# SSL Certificate Status Check Script
# Monitors SSL certificate health and renewal status

SERVER_IP="3.91.153.20"
SERVER_USER="ec2-user"
KEY_PATH="~/.ssh/aws-2024.pem"
DOMAIN="songs.croatoa.live"

echo "🔒 SSL Certificate Status Check for $DOMAIN"
echo "=================================================="

# Check certificate details
echo "📜 Certificate Information:"
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'sudo certbot certificates'

echo ""
echo "🔄 Renewal Timer Status:"
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'sudo systemctl status certbot-renew.timer --no-pager'

echo ""
echo "🧪 Test Certificate Renewal (dry run):"
ssh -i $KEY_PATH $SERVER_USER@$SERVER_IP 'sudo certbot renew --dry-run'

echo ""
echo "🌐 Test HTTPS Connection:"
curl -I https://$DOMAIN

echo ""
echo "🔀 Test HTTP to HTTPS Redirect:"
curl -I http://$DOMAIN

echo ""
echo "✅ SSL Status Check Complete!"
echo "🔒 Site: https://$DOMAIN"
echo "📊 Certificate auto-renews every 12 hours"
