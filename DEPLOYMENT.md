# Development Deployment Guide

## Local Development Setup with Docker

This guide helps you set up the GAAStats app locally using Docker Compose.

---

## Prerequisites

- Docker 24.x+
- Docker Compose 2.x+
- Python 3.12+ (for local development without Docker)

---

## Quick Start (Docker)

### 1. Clone and Navigate

```bash
cd /home/jr/.openclaw/workspace/projects/gaastats-app
```

### 2. Create Environment Variables

Create `backend/.env` file:

```bash
cat > backend/.env << 'EOF'
# Django Configuration
SECRET_KEY=django-insecure-dev-key-change-in-production-$ecretk3y12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.gaastats.ie

# CORS
CORS_ORIGINS=http://localhost:3000

# Database Configuration (PostgreSQL)
DB_NAME=gaastats
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432

# Redis for Django Channels
REDIS_URL=redis://redis:6379/0

# X/Twitter OAuth (get these from https://developer.twitter.com/)
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret

# Features
X_AUTO_TWEET_ENABLED=False
DEFAULT_CLUB_SUBDOMAIN=demo

# Email (for password reset)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@gaastats.ie
EOF
```

### 3. Start Services

```bash
cd deployment
docker-compose up -d
```

### 4. Run Database Migrations

```bash
docker-compose exec backend python manage.py migrate
```

### 5. Create Superuser

```bash
docker-compose exec backend python manage.py createsuperuser
```

Follow prompts to create your admin account.

### 6. Create Demo Club

```bash
docker-compose exec backend python manage.py shell
```

```python
from gaastats.models import Club, UserProfile

# Create demo club
club, created = Club.objects.get_or_create(
    subdomain='demo',
    defaults={
        'name': 'Demo GAA Club',
        'status': 'active',
        'colors': {
            'primary': '10B981',
            'secondary': '6B7280',
            'accent': 'F59E0B'
        },
        'twitter_handle': 'democlub'
    }
)

print(f"Club: {club.name} (subdomain: {club.subdomain})")

# Create admin user profile (for your superuser)
from django.contrib.auth import get_user_model
User = get_user_model()

# Get your superuser (replace email)
user = User.objects.get(email='your-email@example.com')

UserProfile.objects.create(
    user=user,
    club=club,
    role='admin'
)

print(f"Admin profile created for {user.email}")
exit()
```

### 7. Access the Application

- **Web Dashboard**: http://localhost:8080/dashboard/
- **Django Admin**: http://localhost:8080/admin/
- **API Root**: http://localhost:8080/api/
- **WebSocket**: `ws://localhost:8080/ws/match/1/`

### 8. Test Authentication

```bash
# Login
curl -X POST http://localhost:8080/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password",
    "subdomain": "demo"
  }'
```

### 9. Stop Services

```bash
docker-compose down
```

---

## Local Development Setup (Without Docker)

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
nano .env
```

### 4. Start PostgreSQL

```bash
# Using Docker for PostgreSQL only
docker run -d \
  --name gaastats-postgres-local \
  -e POSTGRES_DB=gaastats \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:16-alpine
```

### 5. Start Redis

```bash
# Using Docker for Redis only
docker run -d \
  --name gaastats-redis-local \
  -p 6379:6379 \
  redis:7-alpine
```

### 6. Run Migrations

```bash
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Create Demo Club

Same as step 6 in Docker setup above.

### 9. Run Development Server

```bash
# Run Daphne (ASGI server)
daphne -b 127.0.0.1 -p 8000 gaastats.asgi:application
```

Access at: http://localhost:8000/

---

## Testing X/Twitter Integration

### Get Twitter API Credentials

1. Go to https://developer.twitter.com/
2. Sign up or log in
3. Create a new app
4. Generate API Key, API Secret, Access Token, Access Token Secret
5. Add these to your `.env` file

### Test OAuth Flow

```bash
# 1. Get OAuth URL
curl -X POST http://localhost:8080/api/twitter/oauth/request/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-auth-token>" \
  -d '{
    "callback_url": "http://localhost:8080/auth/twitter/callback/"
  }'

# 2. Visit the returned auth_url in browser
# 3. After authorization, you'll be redirected with oauth_verifier
# 4. Exchange verifier for access token
curl -X POST http://localhost:8080/api/twitter/oauth/callback/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-auth-token>" \
  -d '{
    "oauth_token": "<request_token>",
    "oauth_token_secret": "<request_token_secret>",
    "oauth_verifier": "<verifier_from_callback>"
  }'

# 5. Post a test tweet
curl -X POST http://localhost:8080/api/twitter/tweet/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-auth-token>" \
  -d '{
    "content": "Testing GAA Stats app X integration!"
  }'

# 6. Check connection status
curl http://localhost:8080/api/twitter/status/ \
  -H "Authorization: Token <your-auth-token>"
```

---

## Production SSL Setup (Let's Encrypt)

### 1. Install Certbot

```bash
sudo apt-get update
sudo apt-get install -y certbot
```

### 2. Obtain Wildcard Certificate

```bash
# This will require DNS TXT record verification
sudo certbot certonly \
  --manual \
  --preferred-challenges dns \
  -d "*.gaastats.ie" \
  -d "gaastats.ie"
```

Certbot will give you a TXT record to add to your DNS. After adding it, continue.

### 3. Copy Certificates to Nginx

```bash
sudo cp /etc/letsencrypt/live/gaastats.ie/fullchain.pem \
  deployment/ssl/gaastats.ie.crt

sudo cp /etc/letsencrypt/live/gaastats.ie/privkey.pem \
  deployment/ssl/gaastats.ie.key

sudo chown 1000:1000 deployment/ssl/gaastats.ie.*
```

### 4. Renew Automatically

```bash
# Create renewal script
cat > /home/jr/.openclaw/workspace/projects/gaastats-app/deployment/renew-ssl.sh << 'EOF'
#!/bin/bash

certbot renew --manual --preferred-challenges dns \
  -d "*.gaastats.ie" -d "gaastats.ie"

# Copy new certificates to docker
sudo cp /etc/letsencrypt/live/gaastats.ie/fullchain.pem \
  /home/jr/.openclaw/workspace/projects/gaastats-app/deployment/ssl/gaastats.ie.crt

sudo cp /etc/letsencrypt/live/gaastats.ie/privkey.pem \
  /home/jr/.openclaw/workspace/projects/gaastats-app/deployment/ssl/gaastats.ie.key

sudo chown 1000:1000 \
  /home/jr/.openclaw/workspace/projects/gaastats-app/deployment/ssl/gaastats.ie.*

# Restart nginx to load new certificates
cd /home/jr/.openclaw/workspace/projects/gaastats-app/deployment && \
  docker-compose restart nginx

echo "SSL certificates renewed and Nginx restarted"
EOF

chmod +x /home/jr/.openclaw/workspace/projects/gaastats-app/deployment/renew-ssl.sh
```

### 5. Add Cron Job for Auto-Renewal

```bash
# Run renewal script weekly (Sunday at 2am)
sudo crontab -e
```

Add:
```
0 2 * * 0 /home/jr/.openclaw/workspace/projects/gaastats-app/deployment/renew-ssl.sh >> /var/log/ssl-renewal.log 2>&1
```

---

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL container
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Failed

```bash
# Check Redis container
docker-compose ps redis

# View logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### WebSocket Connection Failed

```bash
# Check Django backend
docker-compose logs backend | grep WebSocket

# Verify Redis is running
docker-compose exec backend python -c "import redis; r = redis.Redis(host='redis'); print(r.ping())"
```

### Migrations Not Applying

```bash
# Run makemigrations
docker-compose exec backend python manage.py makemigrations

# Show pending migrations
docker-compose exec backend python manage.py showmigrations

# Force apply (be careful!)
docker-compose exec backend python manage.py migrate --fake
docker-compose exec backend python manage.py migrate
```

---

## Next Steps

After confirming local setup works:

1. **Test all API endpoints** using curl or Postman
2. **Test WebSocket connection** with a WebSocket client
3. **Configure X/Twitter OAuth** with real credentials
4. **Test auto-tweeting** when scores are recorded
5. **Set up production SSL** if deploying to production

---

**Last Updated:** 2026-02-09
**Developer:** John Roche (@johnrochie)
