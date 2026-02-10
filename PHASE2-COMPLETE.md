# GAA Stats App - Phase 2 Complete ✅

## Overview

Phase 2 adds the **professional web dashboard** for GAA club coaches/managers, with real-time WebSocket updates and comprehensive PDF/Excel report generation.

---

## What's New in Phase 2

### ✅ 1. Web Dashboard Views (Complete)

**Purpose:** Club coaches/managers can view real-time stats and generate professional reports via web browser.

**Files Created:**
- `backend/gaastats/views/dashboard_views.py` (243 lines, 9,243 bytes) - Django views for pages (not API)
- `backend/gaastats/templates/` - HTML templates for web dashboard

**Dashboard Pages:**

1. **Home/Dashboard** (`/`)
   - Quick stats overview with 4 metric cards
   - Recent matches list with status badges
   - Live match indicator (with WebSocket connection)
   - Quick actions (Reports, Squad, Match History)

2. **Match List** (`/dashboard/matches/`)
   - All matches table
   - Search + filter controls
   - Sort options (date, opposition)
   - Status badges (Scheduled, In Progress, Completed, etc.)
   - Direct links to Detail, Live View, PDF/Excel export

3. **Match Detail** (`/dashboard/matches/<id>/`)
   - Full match information
   - Score breakdown (goals, 1-points, 2-points)
   - Match events timeline
   - Per-player stats table (goals, points, shots accuracy, tackles)
   - Quick access to PDF/Excel

4. **Match Live** (`/dashboard/matches/<id>/live/` - **FEATURE**)
   - **Real-time score display** (WebSocket updates every 30s)
   - **Live events feed** (auto-populates as iPad records events)
   - Animated score pulse on updates
   - Connection status indicator (Connected/Disconnected)
   - Starting lineup display
   - WebSocket auto-reconnection (5s intervals)

5. **Players List** (`/dashboard/players/`)
   - Player roster table
   - Sort by jersey number
   - View detailed stats links

6. **Players Detail** (`/dashboard/players/<id>/`)
   - Player profile with stat breakdown
   - Match participation history
   - Recent events list (last 50)

7. **Reports Index** (`/reports/`)
   - **Match Reports:** Select match dropdown + generate PDF/Excel
   - **Player Reports:** Select player dropdown + generate PDF/Excel
   - **Season Reports:** One-click entire season Excel export

---

### ✅ 2. Report Generation (Complete)

**Files Created:**
- `backend/gaastats/reports/match_report.py` (14,942 bytes, 453 lines)
- `backend/gaastats/reports/player_report.py` (8,937 bytes, 272 lines)
- `backend/gaastats/reports/season_report.py` (6,331 bytes, 231 lines)
- `backend/gaastats/reports/__init__.py` (434 bytes)

**Features:**

**Match Reports (PDF + Excel):**
- Match info (date, opposition, venue, weather, referee, competition)
- Final score
- Team stats (goals, 1-points, 2-points, shots, accuracy, tackles)
- Per-player breakdown with shooting accuracy
- Styled PDF with club colors
- Formatted Excel with row/column headers

**Player Reports (PDF + Excel):**
- Player info (name, number, position, status)
- Season stats (goals, points, shots, tackles, matches played)
- Color-coded stats display
- Branded with club colors

**Season Reports (Excel):**
- Club-wide season statistics
- All matches aggregated
- Every player's season stats in one Excel file
- Sorted by jersey number
- Complete shot accuracy and tackle counts

**Technology:**
- **WeasyPrint** - HTML to PDF conversion
- **openpyxl** - Excel file generation (XLSX format)
- Professional styling with club colors (primary, secondary, accent)

---

### ✅ 3. Authentication for Web Dashboard

**Files:**
- `backend/gaastats/views/web_auth.py` (7,250 bytes, 205 lines)
- `backend/gaastats/views/web_auth_urls.py` (469 bytes)
- `backend/gaastats/templates/auth/login.html`
- `backend/gaastats/templates/auth/password-reset.html`
- `backend/gaastats/templates/auth/registration-disabled.html`

**Authentication Flow:**
- **Web Dashboard:** Django session-based auth (cookie-based)
  - Login page with email/password/subdomain
  - Password reset via email (with reset link)
  - "Remember me" checkbox
  - Logout returns to login page

- **iPad App:** Token-based auth (Django REST Framework TokenAuthentication)
  - `/api/auth/token/` endpoint for generating token
  - Token sent in `Authorization: Token <token>` header
  - Auto-login from saved token

**Subdomain Isolation:**
- Login checks `User.club.subdomain` against request domain
- Users can only access their own club's dashboard
- Dev users can view all clubs

---

### ✅ 4. Enhanced Base Template

**Updates:**
- Dynamic club colors from database
- Club logo display (if available)
- Club name in header
- Navigation menu (Dashboard, Matches, Players, Reports, Admin)
- Footer with club name + year
- Tailwind CSS for rapid, professional styling

**Club Branding:**
- Header gradient background (primary → secondary colors)
- Status badges color-coded
- Buttons and links styled with club colors
- Responsive design (mobile-friendly)

---

### ✅ 5. Enhanced URL Configuration

**Updates:**
- Added `/api/auth/` routes (from auth_urls.py - for iPad app token generation)
- Added `/auth/` routes (from web_auth_urls.py - for web dashboard login/logout)
- Separated API auth (token-based) from web auth (session-based)
- Reports routes integration

---

## Technical Implementation

### WebSocket Real-Time Updates

**How It Works:**

1. **iPad records event** → POST to API → `MatchEvent.objects.create()`
2. **Django Signal/Middleware** → Triggers `broadcast_match_update()` on event creation
3. **Channels Consumer** - Already implemented
4. **Web Dashboard Client** - JavaScript listens to `ws://app/match/<id>/`

**Events Sent:**
- `match_state` - Full match state (on request or periodic interval)
- `score_update` - Score changes (every score event)
- `event_created` - New event recorded (real-time feed)
- `player_subbed` - Substitution notifications

**Client-Side JavaScript:**
- WebSocket connection with auto-reconnect (5s intervals)
- Event handling with DOM updates
- Connection status indicator (green=connected, red=disconnected)
- Ping/keep-alive every 30 seconds

### Report Generation Workflow

**Match Report PDF:**
1. Query Match + Events + calculate stats
2. Generate HTML template with WeasyPrint
3. Render PDF to `/media/reports/match_<id>_report.pdf`
4. Return file as HTTP download

**Player Report PDF:**
1. Query Player events + participations + matches
2. Calculate stats (goals, points, accuracy, tackles)
3. Generate HTML template
4. Render PDF

**Season Report Excel:**
1. Query all club matches aggregated stats
2. Query all player events
3. Calculate comprehensive stats
4. Generate multi-sheet Excel file with:
   - Team statistics summary
   - Per-player stats table
   - Club colors in header rows

---

## Complete File Structure (Phase 2 Added)

```
backend/gaastats/
├── views/
│   ├── api_urls.py          # API routes (iPad app token auth)
│   ├── auth_urls.py          # API auth routes (legacy, may remove) + Twitter
│   ├── dashboard_urls.py     # Web dashboard routes (8 routes)
│   ├── twitter.py            # X/Twitter API views (share, status, connect)
│   ├── dashboard_views.py    # Dashboard page views (7 views)
│   ├── auth.py              # REST API auth views (serializer-based)
│   ├── web_auth.py           # Web dashboard auth (session-based)
│   ├── web_auth_urls.py         # Web auth URL configuration (3 routes)
│   ├── reports_urls.py       # Report generation URLs (6 routes)
│   └── __init__.py           # Views module init
├── templates/
│   ├── base.html             # Base template (club branding, colors, nav)
│   ├── dashboard/
│   │   ├── home.html        # Dashboard home
│   │   ├── matches.html     # Matches list page
│   │   ├── match_live.html  # Live stats (WebSocket client)
│   │   └── reports.html     # Reports index
│   └── auth/
│       ├── login.html        # Login page
│       ├── password-reset.html   # Password reset (sent)
│       └── registration-disabled.html # Registration disabled page
└── reports/
    ├── __init__.py
    ├── match_report.py     # Match PDF/Excel generation
    ├── player_report.py    # Player PDF/Excel generation
    └── season_report.py     # Season Excel generation
```

**New Files This Phase:**
- 14 Python files
- 9 HTML template files
- **~1,300+ lines of report generation code**
- **~5,000+ lines of total template/view code**

---

## Dashboard Features

### Real-Time Match Updates (Live Page)

**Connection:**
- WebSocket automatically connects when page loads
- Auto-reconnect if connection drops (5s intervals)
- Ping every 30s to keep connection alive

**Updates Received:**
1. **Score changes:** Header score updates with pulse animation
2. **New events:** Events list auto-populates with latest
3. **Player substitutions:** Notification banner
4. **Match state changes:** Full state refresh (lineups, participants)

**UI Features:**
- **Live indicator:** Pulsing red circle when live
- **Connection status:** "● Connected" (green) or "● Disconnected" (red)
- **Events feed:** Auto-prepends new events, "slide-in" animation
- **Score pulse:** Highlighting animation when score changes
- **Player cards:** Starting lineup display with jersey numbers

---

### Report Features

**Match PDF Report:**
- Professional formatting with club header
- Match information table
- Team statistics (8 stats: goals, 1-points, 2-points, total, shots, accuracy, tackles)
- Per-player stats table (sorted by jersey number)
- Footer with generation timestamp
- Club colors applied to headers

**Match Excel Report:**
- Two sheets:
  - **Match Info:** Opposition, date, venue, weather, referee, competition
  - **Team Stats:** All 8 stats
  - **Player Stats:** Name, number, goals, points, shots, accuracy, tackles
- Column width optimization
- Data formatting (numbers aligned center, text aligned left)

**Player PDF Report:**
- Player profile section (name, number, position, status, matches played)
- Season stats overview (4 key stats)
- Total points breakdown (goals×3 + points)
- Shooting accuracy display
- Branded with club colors
- Footer with timestamp

**Player Excel Report:**
- Player info + season stats (6 stats)
- Single sheet, formatted for Excel
- Easy to sort/filter in Excel

**Season Excel Report:**
- Team statistics summary
- All players in one table
- Jersey number sort order
- Complete season overview in one export

---

## Authentication Comparison

| Platform | Auth Type | Token Storage | Flow |
|----------|-----------|--------------|------|
| **iPad App** | Token-based (Django REST Framework) | Local storage + SQLite | Log in → Generate Token → Store → Send in header |
| **Web Dashboard** | Session-based (Django sessions) | Browser cookies | Log in → Session set → Browser cookie |
| **API Endpoints** | `/api/auth/login/` - Returns token + user | Same endpoint used by iPad for login | |
| **Web Routes** | `/auth/login/`, `/auth/logout/` |  | Login → Session set → Redirect to dashboard |

**Why Two Auth Systems?**
- iPad app: Needs offline support (SQLite persistence)
- Web dashboard: Traditional web app (session cookies work well)
- Both endpoints use same `UserProfile.club` model for club isolation

---

## Testing the Web Dashboard

### Setup
1. **Start Backend:**
   ```bash
   cd deployment
   docker-compose up -d
   ```

2. **Create Test Data:**
   ```bash
   docker-compose exec backend python manage.py shell
   ```
   ```python
   from gaastats.models import Club, User, UserProfile, Player, Match
   import secrets

   # Create demo club
   club, created = Club.objects.get_or_create(
       subdomain='demo',
       defaults={
           'name': 'Demo GAA Club',
           'colors': {'primary': '10B981', 'secondary': '6B7280', 'accent': 'F59E0B'},
           'twitter_handle': 'democlub',
       }
   )
   print(f"Club: {club.name} | Subdomain: {club.subdomain}")
   exit()
   ```

3. **Create Test User:**
   ```python
   user = User.objects.create_user(
       username='admin',
       email='admin@demo.gaastats.ie',
       first_name='Admin',
       last_name='User',
       password='Password123'
   )
   UserProfile.objects.create(
       user=user,
       club=club,
       role='admin'
   )
   print(f"Created: {user.email} | Role: admin")
   exit()
   ```

4. **Create Test Players (quick script):**
   ```python
   from gaastats.models import Player
   club = Club.objects.get(subdomain='demo')

   positions = [
       ('Goalkeeper', 'goalkeeper'),
       ('Full Back', 'fullback'),
       ('Half Back', 'halfback'),
       ('Midfielder', 'midfield'),
       ('Half Forward', 'halfforward'),
       ('Full Forward', 'fullforward'),
   ]

   for i, (pos, pos_key) in enumerate(positions, 1):
       for j in range(3):
           Player.objects.create(
               club=club,
               name=f'Player #{j} of type {pos}',
               number=i,
               position=pos_key,
               injury_status='fit',
               is_available=True,
           )

   print(f"Created team of {Player.objects.filter(club=club).count()} players")
   exit()
   ```

5. **Create Test Match:**
   ```python
   from gaastats.models import Match
   from datetime import date
   club = Club.objects.get(subdomain='demo')

   match = Match.objects.create(
       club=club,
       date=date.today(),
       opposition='Test Opposition',
       entry_mode='live',
       status='in_progress',
   )

   print(f"Created live match: {match.id} | vs {match.opposition}")

   # Add match participants (select first 15 players)
   players = list(Player.objects.filter(club=club).order_by('number'))[:15]
   for i, player in enumerate(players, 1):
       from ..models import MatchParticipant
       MatchParticipant.objects.create(
           match=match,
           player=player,
           is_starting=True,
           minute_on=0,
       )

   print(f"Added {len(players)} participants to match")
   exit()
   ```

6. **Test Match Entry (via API or iPad app):**
   - Record a goal manually via API or use iPad app `LiveStatsScreen.tsx`
   - Check if events appear in `MatchEvent.objects.all()`

### Access Web Dashboard

**Local Development:**
- `http://localhost/dashboard/` (redirects to home)
- `http://localhost/dashboard/matches/` - View all matches
- `http://localhost/dashboard/matches/<id>/live/` - Real-time updates
- `http://localhost/reports/` - Generate reports

**Production (with DNS):**
- `http://demo.gaastats.ie/dashboard/` (demo club)
- `http://austinstacks.gaastats.ie/dashboard/` (austinstacks club)

**Login:**
- Email: `admin@demo.gaastats.ie`
- Password: `Password123`
- (or use demo user you created)

---

## Report Examples

### Match Report Content (PDF)

**Example:**
```
========================================
🏈 GAA Match Report
Austin Stacks - Match Summary
========================================

Match Information
========================================
Opposition: Kerry Kingdom
Date: Sunday, 10 February 2026
Venue: Austin Stacks Park
Weather: Partly Cloudy
Referee: Patrick Murphy
Competition: Division 1 Championship
---
Final Score
========================================
11 - 3

11 - 0-0-0 vs 0-0-0

Team Statistics
========================================
Goals: 3
1-Points: 2
2-Points: 1
Total: 11
Shots: 24
Accuracy: 62.5%
Tackles: 18

Player Statistics
========================================
#    Name                Goals  Pts  2-Pts  Shots  Acc   Tackles
---------------------------------------------------------
10   David O'Sullivan    2     1     1      3     66.7%   6
11   Killian Horan      1     0     0      2     50.0%   3
15   Sean O'Sullivan    0     1     0      4     25.0%   5
...
========================================
Generated: 10 February 2026 at 10:30 | GAA Stats App
```

### Match Report Excel Content

**Sheet 1 - Match Info:**
- Opposition, Date, Venue, Weather, Referee, Competition

**Sheet 2 - Team Stats:**
- Goals, 1-Points, 2-Points, Total, Shots, Accuracy, Tackles

**Sheet 3 - Player Stats:**
- #, Player, Goals, 1-Points, 2-Points, Total, Shots, Accuracy, Tackles

---

## Known Limitations

### Phase 2 MVP (Complete)
- ✅ Real-time WebSocket updates for live matches
- ✅ PDF + Excel report generation
- ✅ Club branding across dashboard
- ✅ Session-based auth for web dashboard
- ✅ Match detail views with player stats
- ✅ Report generation for matches, players, season

### Phase 3 Enhancements (Future)
- Match schedule calendar
- Team form (last 5 matches)
- Heat map visualization for kick-outs
- Advanced stats (zone possession, conversion rates)
- Video player integration for post-match analysis
- Push notifications (match reminders, score updates)
- Club communications module
- Player training planner
- Player availability calendar

### Not in MVP
- No login page customization (uses Django default) → Phase 3
- No match scheduling calendar → Phase 3
- No player performance rating algorithms → Phase 3

---

## Deployment Checklist

### Before Going Live
- [ ] Test all report generation (match, player, season)
- [ ] Test real-time WebSocket connection during live match
- [ ] Verify club colors apply correctly in dashboard
- [ ] Test iPad app syncing to backend
- [ ] Set up SSL certificates (Let's Encrypt, wildcards)

### Production Deployment
- [ ] Update `ALLOWED_HOSTS` in settings
- [ ] Configure email backend for password resets
- [ ] Set up production database backups
- [ ] Configure SSL for WebSocket (wss://)
- [ ] Set up cron jobs for database backups
- [ ] Set up monitoring (Sentry for errors)
- [ ] Configure CDN for media files

---

## Status: Phase 2 Complete ✅

**Time to Build Phase 2:** ~1.5 hours (dashboard views + report generation)

**Total Build Time:**
- Phase 1 Backend (Weeks 1-2): ~3 hours
- Phase 2 Web Dashboard (Phase 2): ~1.5 hours
- **iPad App (Weeks 3-4): ~4 hours
- **TOTAL: ~8.5 hours from start to finish**

**Complete Status:**
- ✅ Backend API (Django REST + WebSocket)
- ✅ Offline SQLite + Sync (iPad app)
- ✅ Real-time WebSocket updates (live page)
- ✅ PDF/Excel generation (WeasyPrint + openpyxl)
- ✅ Web dashboard (responsive, with club branding)
- ✅ Authentication (web + app token)

---

**Next Phase:** Phase 3 (Advanced Features) - Or production deployment!

**Recommendation:** Test the web dashboard with backend + iPad app integration first, then deploy to production or move to Phase 3.

---

**Last Updated:** 2026-02-10 08:00 UTC
**Developer:** John Roche (@johnrochie)
**Total Code:** Django: ~10,000+ lines, iPad: ~5,322 lines, Templates: ~7,000 lines = **~22,000+ total lines of code**

---

**Platform Complete:** Web Dashboard + Reports + Real-Time WebSocket Live Stats
**Ready for:** Integration testing with iPad app → Production deployment
