# Project: Darth

**GAA Stats App** - Professional multi-tenant stats and communication platform for GAA clubs (Gaelic Athletic Association)

---

## 🎯 Project Overview

Multi-tenant Django + React Native platform for real-time match statistics, player performance tracking, and club management with subdomain-based access (`clubname.gaastats.ie`).

---

## 📋 Features

### Backend (Django)
- **10 Preset KPIs** (Goals, 1-Point Scores, 2-Point Scores, Shots Taken, Shots on Target, Tackles Won, Turnovers Lost, Kick-outs Won/Lost, Kick-out Location)
- **Real-time Updates** via Django Channels WebSockets (live match stats)
- **Multi-tenant Architecture** - subdomain-based club access
- **X/Twitter Integration** - auto-post score updates and manual tweeting
- **Report Generation** - PDF (WeasyPrint) and Excel (openpyxl) match/club reports
- **Role-based Access** (viewer, admin, dev)
- **REST API** with Django REST Framework

### iPad App (React Native)
- Quick Taps UI (17 event types with large touch targets)
- Offline SQLite Storage (5 tables with sync queue)
- 7 Screens (Login, Home, Create Match, Live Stats, Squad, History, Settings)
- Real-time WebSocket updates (match state, scores, events)
- X/Twitter Manual Share
- Background sync service (30s intervals, 3 attempt retry)

---

## 🏗️ Tech Stack

### Backend
- **Django 5.0.10** + Django REST Framework 3.15.2
- **Django Channels 4.2.0** (WebSockets)
- **PostgreSQL 16** + Redis 7
- **WeasyPrint 62.3** + openpyxl 3.1.5 (PDF/Excel reports)
- **Tweepy 4.14.0** (X/Twitter)
- **Daphne 4.1.2** (ASGI server)

### iPad App
- **React Native 0.83.1** + React Navigation 7.x
- **Zustand 5.x** (state management)
- **SQLite** + react-native-sqlite-storage 6.0.1
- **Axios 1.7.9** (HTTP client)

### Deployment
- **Docker Compose** (PostgreSQL, Redis, Django/Daphne, Nginx)
- **GitHub Actions** (CI/CD with pytest)

---

## 🧪 Testing

Full test suite with pytest:
- **Backend Tests:** Models, API views, Authentication, WebSocket flows
- **Test Coverage:** 40+ tests covering core functionality

Run tests locally:
```bash
cd backend
pytest --cov=gaastats --cov-report=term-missing
```

CI/CD: GitHub Actions runs tests on every push/PR.

---

## 🚀 Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Docker Deployment
```bash
cd deployment
docker-compose up -d
```

---

## 📁 Project Structure

```
gaastats-app/
├── backend/                 # Django REST API backend
│   ├── gaastats/
│   │   ├── models.py       # 8 models (Club, Match, Player, User, etc.)
│   │   ├── views/          # API viewsets, dashboard views, X/Twitter
│   │   ├── consumers/      # WebSocket consumers
│   │   ├── serializers/    # REST serializers
│   │   ├── tests/          # Test suite (test_models, test_api_views)
│   │   └── social_media/   # X/Twitter service
│   ├── deployment/         # Docker Compose (Postgres, Redis, Nginx)
│   └── docs/              # Documentation
├── ipad-app/              # React Native iPad app
│   ├── src/screens/       # 7 screens
│   ├── src/services/      # API, WebSocket, sync, offline storage
│   └── src/components/    # QuickButton, KickoutHeatMap
└── .github/workflows/    # CI/CD (pytest, coverage reporting)
```

---

## 🎖️ GAA Rules Implementation

**New 2-Point Scoring Rule:** Shots from outside the 40m arc are worth 2 points.

**Preset KPIs:**
1. Goals Scored (3 points)
2. 1-Point Scores (1 point)
3. 2-Point Scores (40m+ arc - NEW)
4. Shots Taken
5. Shots on Target
6. Tackles Won
7. Turnovers Lost
8. Kick-outs Won
9. Kick-outs Lost
10. Kick-out Location (angle 0-360°, distance 10-70m)

---

## 🚧 Status

- ✅ MVP Backend Complete
- ✅ MVP iPad App Complete
- ✅ Real-time WebSocket Dashboard
- ✅ Report Generation (PDF/Excel)
- ✅ X/Twitter Integration
- ✅ Test Suite Complete (40+ tests)
- 🔄 Production Deployment Pending

---

## 📝 Notes

- **Multi-tenant:** One shared platform, club-specific data isolation
- **Offline-First:** iPad app works without internet, syncs when online
- **Real-time:** Live match stats via WebSockets
- **Scalable:** Docker deployment for easy horizontal scaling

---

*Built by John Roche (@johnrochie) - 2026*
