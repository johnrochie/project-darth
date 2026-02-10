# GAA Stats App - Django Backend Implementation Complete

**Status:** Phase 1 - Week 4 of 8 (iPad App Complete)

---

## What We've Built

### Complete Django Backend Infrastructure

✅ **Multi-tenant Architecture**
- Subdomain-based club access (`clubname.gaastats.ie`)
- `club_id` foreign key on every model for strict data siloing
- SubdomainMiddleware to extract subdomain from request
- ClubFilterMiddleware to ensure no cross-club data access

✅ **Database Models (8 + User Profile)**
1. `Club` - GAA clubs with logos, colors, Twitter handles
2. `UserProfile` - Extended user with club membership and role (admin, viewer, dev)
3. `Player` - Up to 40 players per club (injury status, availability, positions)
4. `Match` - Match tracking (live/post-match modes, scores, status)
5. `MatchParticipant` - Team selection (15 from 40)
6. `MatchEvent` - Individual stats events (10 preset KPIs)
7. `MatchScoreUpdate` - Social media (X/Twitter) score update history
8. `OAuthToken` - X/Twitter OAuth token storage

✅ **Django REST Framework API (9 ViewSets)**
1. `ClubViewSet` - Club CRUD (dev only)
2. `UserProfileViewSet` - User profile management
3. `PlayerViewSet` - Player CRUD (admin only for modifications)
4. `MatchViewSet` - Match CRUD + start/complete actions
5. `MatchParticipantViewSet` - Team lineup management
6. `MatchEventViewSet` - Stats entry + undo functionality
7. `MatchScoreUpdateViewSet` - Social media tracking
8. `StatsViewSet` - Player and match stats aggregation
9. `OAuthTokenViewSet` - OAuth token management (admin)

✅ **Django Channels (WebSockets)**
- `MatchConsumer` - Real-time match updates
- WebSocket connection: `ws://api.gaastats.ie/ws/match/<match_id>/`
- Event types: `match_update`, `score_update`, `event_created`, `player_subbed`
- Authentication via session auth
- Match state broadcasts to all connected clients

✅ **Django Admin**
- All 8 models registered with ModelAdmin
- Inline participants/events for match management
- Advanced filtering and search
- Optimized queries (select_related)

✅ **Docker Deployment**
- `docker-compose.yml` with PostgreSQL, Redis, Django, Nginx
- Nginx wildcard SSL subdomain support (`*.gaastats.ie`)
- Health checks for all services
- Production-ready configuration

✅ **Web Templates**
- Base template with club branding (logo, colors, subdomain)
- Welcome/home page with quick navigation to dashboard/reports
- Tailwind CSS for rapid styling

---

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Generate auth token for iPad app

### Clubs
- `GET/POST /api/clubs/` - List/create clubs (dev only)
- `GET/PUT/PATCH/DELETE /api/clubs/<id>/` - Club CRUD

### Users
- `GET /api/profiles/me/` - Get current user profile
- `GET/POST /api/profiles/` - List/create profiles

### Players
- `GET /api/players/` - List players (filtered by club)
- `POST /api/players/` - Create player (admin only)
- `GET/PUT/PATCH/DELETE /api/players/<id>/` - Player CRUD
- `GET /api/players/available/` - Get available players for selection

### Matches
- `GET /api/matches/` - List matches (filtered by club)
- `POST /api/matches/` - Create match
- `GET/PUT/PATCH/DELETE /api/matches/<id>/` - Match CRUD
- `POST /api/matches/<id>/start_match/` - Mark match as in progress
- `POST /api/matches/<id>/complete_match/` - Mark match as completed
- `GET /api/matches/recent/` - Get recent 10 matches

### Match Participants (Team Selection)
- `GET /api/match-participants/` - List participants
- `POST /api/match-participants/` - Add player to match
- `GET/PUT/PATCH/DELETE /api/match-participants/<id>/` - Participant CRUD

### Match Events (Stats Entry)
- `GET /api/match-events/` - List events (filtered by match_id if provided)
- `POST /api/match-events/` - Record stat event
- `GET/PUT/PATCH/DELETE /api/match-events/<id>/` - Event CRUD
- `POST /api/match-events/<id>/undo/` - Correct/undo event

### Stats (Aggregation)
- `GET /api/stats/player_summary/` - Player stats (query params: player_id, match_id)
- `GET /api/stats/match_summary/` - Match stats (query params: match_id - required)

### OAuth Tokens (X/Twitter)
- `GET /api/oauth-tokens/` - List tokens (filtered by club)
- `POST /api/oauth-tokens/` - Store OAuth token (admin only)
- `GET/PUT/PATCH/DELETE /api/oauth-tokens/<id>/` - Token CRUD

---

## Database Schema

### Club Table
```
id (PK), name, subdomain (unique), logo_url, colors (JSONB),
status, twitter_handle, created_at, updated_at
```

### UserProfile Table
```
id (PK), user (FK), club (FK), role (admin/viewer/dev)
```

### Player Table
```
id (PK), club (FK), name, number, position, injury_status,
is_available, notes, created_at, updated_at
UNIQUE: (club, number), (club, name)
```

### Match Table
```
id (PK), club (FK), date, time, opposition, venue, weather,
referee, competition, entry_mode, status, club_goals,
club_1point, club_2point, club_score, opposition_goals,
opposition_score, created_at, updated_at
```

### MatchParticipant Table
```
id (PK), match (FK), player (FK), position, is_starting,
minute_on, minute_off, created_at
UNIQUE: (match, player)
```

### MatchEvent Table
```
id (PK), match (FK), player (FK nullable), timestamp, minute,
event_type, data (JSONB), corrected_event (FK nullable), created_at
INDEX: (match, minute), (match, event_type), (player, match)
```

### MatchScoreUpdate Table
```
id (PK), match (FK), timestamp, score_text, social_media_posted,
x_post_id, created_at
```

### OAuthToken Table
```
id (PK), club (FK unique), provider, oauth_token, oauth_token_secret,
expires_at, created_at, updated_at
```

---

## Event Types (10 Preset KPIs)

### Scores
- `score_goal` - Goal scored (3 points)
- `score_1point` - 1-point scored
- `score_2point` - 2-point scored (outside 40m arc, new GAA rule)

### Shots
- `shot_on_target` - Shot on target (not saved)
- `shot_wide` - Shot wide
- `shot_saved` - Shot saved by goalkeeper

### Defensive
- `tackle_won` - Tackle won
- `tackle_lost` - Tackle lost
- `block` - Block

### Possession
- `turnover_lost` - Turnover lost
- `turnover_won` - Turnover won back

### Kick-outs
- `kickout_won` - Kick-out won by team
- `kickout_lost` - Kick-out lost to opposition

### Other
- `substitution` - Player substitution
- `injury` - Player injury
- `foul_committed` - Foul committed
- `foul_conceded` - Foul conceded

---

## Kick-out Data Storage

Stored in `MatchEvent.data` JSONB when event_type = `kickout_won` or `kickout_lost`:

```json
{
  "angle": 45.0,      // 0-360 degrees (North = 0, East = 90)
  "distance": 35.0,   // meters from goal
  "outcome": "won"    // won / lost / turnover / score
}
```

---

## Data Isolation Strategy

### Multi-Tenancy Implementation

**URL-based Subdomain Routing:**
- Request: `https://www.austinstacks.gaastats.ie/`
- SubdomainMiddleware extracts: `www.austinstacks`
- Club model queried: `Club.objects.get(subdomain='www.austinstacks')`
- club_id set in `request.club_id`

**Database Filtering:**
- All API endpoints filter queries by club_id
- Example: `Player.objects.filter(club=request.club_id)`
- ClubFilterMiddleware ensures consistent filtering

**User Roles:**
- `viewer`: Read-only access to own club's data
- `admin`: Full CRUD access to own club's data
- `dev`: Platform admin, can see all clubs

**Example Query Filtering:**
```python
# In PlayerViewSet.get_queryset()
user_profile = UserProfile.objects.get(user=request.user)
return Player.objects.filter(club=user_profile.club)

# In MatchEventViewSet.get_queryset()
user_profile = UserProfile.objects.get(user=request.user)
return MatchEvent.objects.filter(match__club=user_profile.club)
```

---

## WebSocket Real-time Updates

### Connection
```
ws://api.gaastats.ie/ws/match/123/
```

### Events Sent to Clients

#### 1. Match State (on request)
```json
{
  "type": "match_state",
  "data": {
    "match_id": 123,
    "status": "in_progress",
    "score": {
      "club": { "goals": 2, "point_1": 8, "point_2": 1, "total": 15 },
      "opposition": { "goals": 1, "total": 3 }
    },
    "recent_events": [...],
    "starting_lineup": [...]
  }
}
```

#### 2. Score Update (broadcasted)
```json
{
  "type": "score_update",
  "data": {
    "goals": 3,
    "point_1": 10,
    "point_2": 1
  }
}
```

#### 3. Event Created (broadcasted)
```json
{
  "type": "event_created",
  "data": {
    "id": 456,
    "event_type": "score_1point",
    "minute": 28,
    "player": { "id": 12, "name": "John Smith", "number": 10 }
  }
}
```

---

## Deployment Configuration

### Docker Compose Services

1. **PostgreSQL 16** - Database
   - Port: 5432
   - Volume: `postgres_data`
   - Health check: `pg_isready`

2. **Redis 7** - Django Channels layer
   - Port: 6379
   - Health check: `redis-cli ping`

3. **Django Backend (Daphne)** - ASGI server
   - Port: 8000
   - Includes: REST API + WebSockets
   - Health check: HTTP GET /api/
   - Command: `daphne -b 0.0.0.0 -p 8000 gaastats.asgi:application`

4. **Nginx** - Reverse proxy
   - HTTP: Port 80 (redirects to HTTPS)
   - HTTPS: Port 443 (wildcard SSL for *.gaastats.ie)
   - WebSocket proxy: /ws/* to backend:8000

---

## Week 2 Complete ✅

### X/Twitter Integration (Complete)

✅ **XService Class** (`gaastats/social_media/x_service.py`)
- OAuth 1.0a flow for X account authorization
- `post_tweet()` - Post custom tweets
- `post_score_update()` - Auto-post live score updates
- `get_oauth_url()` - Generate OAuth auth URL
- `exchange_request_token()` - Exchange for access tokens
- Tweepy API client integration

✅ **X (Twitter) API Views** (`gaastats/views/twitter.py`)
- `POST /api/twitter/oauth/request/` - Initiate OAuth flow
- `POST /api/twitter/oauth/callback/` - Handle OAuth callback
- `POST /api/twitter/tweet/` - Post custom tweet
- `GET /api/twitter/status/` - Check connection status
- `DELETE /api/twitter/disconnect/` - Remove OAuth tokens

✅ **Auto-Tweet on Score Events**
- Integrated into `MatchEventViewSet.perform_create()`
- Auto-tweets when `score_goal`, `score_1point`, `score_2point` events recorded
- Toggleable via `X_AUTO_TWEET_ENABLED` environment variable
- Gracefully handles missing/invalid OAuth tokens

### Authentication Flow (Complete)

✅ **Auth Views** (`gaastats/views/auth.py`)
- `POST /api/auth/login/` - Email/password login (web + iPad)
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - Logout (web)
- `GET /api/auth/me/` - Get current user info
- `POST /api/auth/password-reset/` - Request password reset (email)
- `POST /api/auth/password-reset-confirm/` - Confirm password reset

✅ **Features Implemented**
- Subdomain-aware login ( verifies user belongs to club )
- Club-based access control
- Session auth for web dashboard
- Token auth for iPad app (DRF TokenAuthentication)
- Password reset via email (console backend for dev)
- User roles: admin, viewer, dev

### Docker & Deployment Setup (Complete)

✅ **Deployment Guide** (`DEPLOYMENT.md`)
- Complete local Docker setup guide
- docker-compose configuration details
- Environment variable setup
- Database migration steps
- Demo club creation script

✅ **Self-Signed SSL Certificates**
- Generated for development: `*.gaastats.ie`
- Files: `deployment/ssl/gaastats.ie.crt`, `gaastats.ie.key`
- Nginx configured for HTTPS

✅ **Production SSL Setup Guide**
- Let's Encrypt wildcard certificate instructions
- Certbot DNS verification steps
- SSL certificate renewal script
- Cron job for auto-renewal

### Files Added This Week

**X/Twitter Integration:**
- ✅ `gaastats/social_media/__init__.py`
- ✅ `gaastats/social_media/x_service.py` (7121 bytes)

**Authentication:**
- ✅ `gaastats/views/auth.py` (10372 bytes)
- ✅ `gaastats/views/twitter.py` (7093 bytes)

**Deployment:**
- ✅ `DEPLOYMENT.md` (8826 bytes)
- ✅ `deployment/ssl/gaastats.ie.crt` (self-signed)
- ✅ `deployment/ssl/gaastats.ie.key` (private key)
- ✅ `backend/.env` (local config)

**Updated:**
- ✅ `gaastats/views/api_urls.py` (added auth + twitter routes)
- ✅ `gaastats/views/__init__.py` (auto-tweet in MatchEventViewSet)
- ✅ `requirements.txt` (added tweepy, requests, oauthlib)

---

## Next Steps (Week 3-4) - iPad App Development

Coming next:
- **Week 3-4:** React Native iPad App (pitch-side stats entry)
- **Quick Taps UI** - Large buttons for fast events
- **Offline SQLite** - Local storage + sync queue
- **Team Selection** - 15 from 40 picker
- **Live Stats Entry** - Scores, shots, tackles, kick-outs
- **WebSocket Client** - Receive real-time updates
- **X Share Button** - Manual tweet posting

### What's Coming Next

### After Week 2

- **Week 3-4:** iPad App Development (React Native)
- **Week 5-6:** Offline Sync & Polish
- **Week 7:** Web Dashboard Templates
- **Week 8:** Testing & Deployment

---

## Technology Stack

| Component           | Technology                      | Purpose                     |
|---------------------|---------------------------------|-----------------------------|
| Backend Framework   | Django 5.x                      | REST API + Admin            |
| API                 | Django REST Framework 3.x       | API endpoints               |
| Real-time           | Django Channels 4.x             | WebSockets                  |
| ASGI Server         | Daphne 4.x                      | ASGI application server     |
| Database            | PostgreSQL 16                   | Multi-tenant data storage   |
| Redis               | Redis 7                         | Channels layer              |
| Frontend (Web)      | Django Templates + JavaScript   | Web dashboard               |
| Frontend (iPad)     | React Native (React Native CLI) | Pitch-side stats entry      |
| Authentication      | DRF Token + Django Sessions     | iPad + Web auth            |
| Social Media        | Python Social Auth              | X/Twitter OAuth             |
| Reports             | WeasyPrint + openpyxl           | PDF + Excel exports         |
| Deployment          | Docker + Nginx                  | Production hosting          |

---

## Files Created

**Backend (Django):**
- ✅ `backend/gaastats/settings.py` - Multi-tenant configuration
- ✅ `backend/gaastats/urls.py` - URL routing
- ✅ `backend/gaastats/wsgi.py` - WSGI config
- ✅ `backend/gaastats/asgi.py` - ASGI config (Channels)
- ✅ `backend/gaastats/routing.py` - WebSocket routing
- ✅ `backend/gaastats/middleware.py` - Subdomain + club filtering
- ✅ `backend/gaastats/models/` - 8 models + admin
- ✅ `backend/gaastats/serializers/` - DRF serializers
- ✅ `backend/gaastats/views/` - DRF viewsets + API URLs
- ✅ `backend/gaastats/consumers/` - WebSocket consumer
- ✅ `backend/gaastats/templates/` - Base + home templates
- ✅ `backend/requirements.txt` - Python dependencies
- ✅ `backend/Dockerfile` - Docker image
- ✅ `backend/manage.py` - Django management

**Deployment:**
- ✅ `deployment/docker-compose.yml` - Multi-service docker setup
- ✅ `deployment/nginx.conf` - Wildcard SSL subdomain routing

**Documentation:**
- ✅ `README.md` - Project overview
- ✅ `MVP-IMPLEMENTATION-STATUS.md` - This file

---

## Run the Backend (Local)

### Prerequisites
- Python 3.12+
- PostgreSQL 16
- Redis 7

### Installation

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create demo club (via Django shell)
python manage.py shell
>>> from gaastats.models import Club
>>> Club.objects.create(name="Demo Club", subdomain="demo", status="active")
>>> exit()

# Run development server (with Channels)
daphne -b 127.0.0.1 -p 8000 gaastats.asgi:application
```

### Access
- Django Admin: http://127.0.0.1:8000/admin/
- API Root: http://127.0.0.1:8000/api/

---

**Last Updated:** 2026-02-09 23:10 UTC
**Developer:** John Roche (@johnrochie)
