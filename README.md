# Song Lyrics Manager

A web application for managing and storing song lyrics with an intuitive interface.

## Description

This application provides a simple and efficient way to store, edit, and manage song lyrics. It features:

- A scrollable pane on the left showing all song titles
- An editable canvas on the right for viewing and editing lyrics
- Auto-save functionality - no need to manually save changes
- Add and delete song functionality
- Clean, responsive interface using Tailwind CSS

## Author

Created by levensailor

## Features

- **Real-time editing**: Changes are automatically saved as you type
- **Intuitive interface**: Clean two-pane layout with song list and lyrics editor
- **SQLite database**: Lightweight database for storing songs and lyrics
- **REST API**: Full REST API with versioned endpoints (/api/v1/)
- **Comprehensive logging**: Rotating log files with detailed timestamps and function names
- **Error handling**: Proper error handling and user feedback

## Technology Stack

- **Backend**: FastAPI with Python
- **Database**: SQLite
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Server**: Uvicorn ASGI server

## Installation & Setup

1. Clone or download the project files
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Deployment Instructions

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The application will be available at `http://localhost:8000`

### Production Deployment

The application is deployed on AWS EC2 with the following setup:

- **URL**: https://songs.croatoa.live (HTTPS with SSL certificate)
- **Server**: EC2 t3.micro instance (Amazon Linux 2)
- **Web Server**: Nginx (reverse proxy)
- **Application Server**: Uvicorn (FastAPI)
- **Database**: SQLite
- **Domain**: Route 53 DNS (songs.croatoa.live)

#### Deployment Scripts

- **Initial Deployment**: `./deploy.sh` - Sets up the entire infrastructure
- **Updates**: `./redeploy.sh` - Quick updates to existing deployment
- **SSL Setup**: `./setup-ssl.sh` - Configures HTTPS with Let's Encrypt

#### Infrastructure Components

- **EC2 Instance**: t3.micro with public IP (3.91.153.20)
- **Security Group**: SSH (22), HTTP (80), HTTPS (443)
- **Route 53**: DNS record for songs.croatoa.live
- **SSL Certificate**: Let's Encrypt (auto-renewal every 12 hours)
- **Systemd Service**: Auto-start application service
- **Nginx**: Reverse proxy with HTTP to HTTPS redirect
- **Security Headers**: HSTS, CSP, XSS protection, etc.

#### Monitoring

Check application status:
```bash
ssh -i ~/.ssh/aws-2024.pem ec2-user@3.91.153.20 'sudo systemctl status songs'
```

View logs:
```bash
ssh -i ~/.ssh/aws-2024.pem ec2-user@3.91.153.20 'sudo journalctl -u songs -f'
```

Check SSL certificate:
```bash
ssh -i ~/.ssh/aws-2024.pem ec2-user@3.91.153.20 'sudo certbot certificates'
```

Test SSL renewal:
```bash
ssh -i ~/.ssh/aws-2024.pem ec2-user@3.91.153.20 'sudo certbot renew --dry-run'
```

For manual deployment:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /api/v1/songs` - Get all songs
- `GET /api/v1/songs/{id}` - Get a specific song
- `POST /api/v1/songs` - Create a new song
- `PUT /api/v1/songs/{id}` - Update a song
- `DELETE /api/v1/songs/{id}` - Delete a song

## Usage

1. **Adding Songs**: Click the "Add Song" button and enter a title
2. **Editing Lyrics**: Click on any song title to load its lyrics in the editor
3. **Auto-save**: Simply start typing - changes are saved automatically
4. **Deleting Songs**: Select a song and click "Delete Song"

## Public Assets

- **Production URL**: https://songs.croatoa.live
- **Local Development**: `http://localhost:8000`
- **API Documentation**: `https://songs.croatoa.live/docs` (FastAPI auto-generated docs)
- **Public IP**: 3.91.153.20
- **GitHub Repository**: (if applicable)

## Login Instructions

No authentication is required for this application. Simply navigate to the URL and start using the interface.

## Files Structure

```
songs/
├── main.py              # FastAPI backend application
├── requirements.txt     # Python dependencies
├── .env                # Environment configuration
├── .gitignore          # Git ignore file
├── README.md           # This file
├── songs.db            # SQLite database (created automatically)
├── log_archive/        # Log files directory
└── static/
    └── index.html      # Frontend interface
```
