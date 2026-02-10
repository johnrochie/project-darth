"""
API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views import (
    ClubViewSet, UserProfileViewSet, PlayerViewSet, MatchViewSet,
    MatchParticipantViewSet, MatchEventViewSet, MatchScoreUpdateViewSet,
    StatsViewSet, OAuthTokenViewSet, GenerateAuthToken
)
from .auth import (
    auth_login, auth_register, auth_logout, auth_me,
    password_reset, password_reset_confirm
)
from .twitter import (
    twitter_oauth_request, twitter_oauth_callback,
    twitter_post_tweet, twitter_status, twitter_disconnect
)

router = DefaultRouter()
router.register(r'clubs', ClubViewSet, basename='club')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'match-participants', MatchParticipantViewSet, basename='matchparticipant')
router.register(r'match-events', MatchEventViewSet, basename='matchevent')
router.register(r'match-score-updates', MatchScoreUpdateViewSet, basename='matchscoreupdate')
router.register(r'stats', StatsViewSet, basename='stats')
router.register(r'oauth-tokens', OAuthTokenViewSet, basename='oauthtoken')

urlpatterns = [
    path('', include(router.urls)),

    # Authentication
    path('auth/login/', auth_login, name='auth_login'),
    path('auth/register/', auth_register, name='auth_register'),
    path('auth/logout/', auth_logout, name='auth_logout'),
    path('auth/me/', auth_me, name='auth_me'),
    path('auth/password-reset/', password_reset, name='password_reset'),
    path('auth/password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
    path('auth/token/', GenerateAuthToken.as_view(), name='generate-token'),

    # X (Twitter) OAuth
    path('twitter/oauth/request/', twitter_oauth_request, name='twitter_oauth_request'),
    path('twitter/oauth/callback/', twitter_oauth_callback, name='twitter_oauth_callback'),
    path('twitter/tweet/', twitter_post_tweet, name='twitter_post_tweet'),
    path('twitter/status/', twitter_status, name='twitter_status'),
    path('twitter/disconnect/', twitter_disconnect, name='twitter_disconnect'),
]
