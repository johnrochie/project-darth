"""
Views Package
Exports all ViewSets for REST API and web dashboard views
"""

# REST Framework ViewSets (API endpoints)
from .viewsets import (
    ClubViewSet,
    UserProfileViewSet,
    PlayerViewSet,
    MatchViewSet,
    MatchParticipantViewSet,
    MatchEventViewSet,
    MatchScoreUpdateViewSet,
    StatsViewSet,
    OAuthTokenViewSet,
    GenerateAuthToken,  # APIView for auth token generation
)

# Web Dashboard Views (Django templates)
from .dashboard_views import *

__all__ = [
    # API ViewSets
    'ClubViewSet',
    'UserProfileViewSet',
    'PlayerViewSet',
    'MatchViewSet',
    'MatchParticipantViewSet',
    'MatchEventViewSet',
    'MatchScoreUpdateViewSet',
    'StatsViewSet',
    'OAuthTokenViewSet',
    'GenerateAuthToken',  # Auth token generation endpoint (APIView)
]

