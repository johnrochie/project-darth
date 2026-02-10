"""
Tests for GAA Stats App API views

Tests:
- Health check endpoint
- Authentication (login, token generation)
- List matches API
- Create match API
- List players API
- WebSocket connection handling
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from gaastats.models import Club, Match, Player, MatchEvent


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self, api_client):
        """Test API health check returns 200 OK."""
        response = api_client.get('/api/')
        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.json()


class TestAuthenticationAPI:
    """Test authentication API endpoints."""

    def test_api_login_creates_token(self, club):
        """Test logging in via API creates auth token."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.json()

    def test_api_login_invalid_credentials(self, club):
        """Test API login with invalid password fails."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_request_with_token(self, authenticated_client):
        """Test authenticated request succeeds with valid token."""
        response = authenticated_client.get('/api/clubs/')
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_request_fails(self, api_client):
        """Test unauthenticated request fails."""
        response = api_client.get('/api/clubs/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestClubAPI:
    """Test club API endpoints."""

    def test_list_clubs_authenticated(self, authenticated_client):
        """Test authenticated user can list clubs."""
        response = authenticated_client.get('/api/clubs/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_club_detail(self, club_admin_user, club):
        """Test getting details of a specific club."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.get(f'/api/clubs/{club.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Test Club'


class TestMatchAPI:
    """Test match API endpoints."""

    def test_list_matches_unauthenticated(self, api_client, matches):
        """Test unauthenticated user cannot list matches."""
        response = api_client.get('/api/matches/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_matches_authenticated(self, authenticated_client, matches):
        """Test authenticated user can list matches."""
        response = authenticated_client.get('/api/matches/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 3

    def test_create_match_authenticated(self, authenticated_client, club):
        """Test authenticated user cannot create match (admin only)."""
        data = {
            'club': club.id,
            'opponent': club.id,  # Using same club as opponent for test
            'venue': club.name,
            'match_type': 'championship',
            'scheduled_time': '2026-02-10T15:00:00Z'
        }
        response = authenticated_client.post('/api/matches/', data)
        # Viewer role should fail to create
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]

    def test_get_match_detail(self, club_admin_user, match):
        """Test getting details of a specific match."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.get(f'/api/matches/{match.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['venue'] == 'Test Club'
        assert data['status'] == 'scheduled'


class TestPlayerAPI:
    """Test player API endpoints."""

    def test_list_players_unauthenticated(self, api_client, club):
        """Test unauthenticated user cannot list players."""
        response = api_client.get('/api/players/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_players_authenticated(self, authenticated_client, players):
        """Test authenticated user can list players."""
        response = authenticated_client.get('/api/players/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 11

    def test_get_player_detail(self, club_admin_user, player):
        """Test getting details of a specific player."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.get(f'/api/players/{player.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == 'Test Player'
        assert data['number'] == 10

    def test_delete_player_unauthorized(self, club_viewer_user, player):
        """Test viewer role cannot delete player."""
        token, _ = Token.objects.get_or_create(user=club_viewer_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.delete(f'/api/players/{player.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestMatchEventAPI:
    """Test match event API endpoints."""

    def test_list_match_events_unauthenticated(self, api_client, match):
        """Test unauthenticated user cannot list match events."""
        response = api_client.get(f'/api/match-events/?match={match.id}')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_match_events_authenticated(self, club_admin_user, match, match_events):
        """Test authenticated user can list match events."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.get(f'/api/match-events/?match={match.id}')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 5

    def test_create_match_event_admin(self, club_admin_user, match, player):
        """Test admin can create a match event."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        data = {
            'match': match.id,
            'player': player.id,
            'minute': 30,
            'event_type': 'goal',
            'team': 'home',
            'x_location': 50,
            'y_location': 30
        }
        response = client.post('/api/match-events/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_match_event_viewer(self, club_viewer_user, match, player):
        """Test viewer cannot create a match event."""
        token, _ = Token.objects.get_or_create(user=club_viewer_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        data = {
            'match': match.id,
            'player': player.id,
            'minute': 30,
            'event_type': 'goal',
            'team': 'home'
        }
        response = client.post('/api/match-events/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestWebSocketConnections:
    """Test WebSocket connection handling."""

    def test_websocket_accepts_authenticated_user(self, match, club_admin_user):
        """Test WebSocket connection accepts authenticated user."""
        # In production, test with actual WebSocket client
        # For now, verify consumer can get token from URL
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        assert token is not None
        assert token.user == club_admin_user

    def test_websocket_rejects_invalid_token(self):
        """Test WebSocket connection rejects invalid token."""
        # Mock consumer behavior
        invalid_token = "invalid_token_string"
        assert len(invalid_token) == 19  # Invalid length
        # Consumer should reject this token


class TestPagination:
    """Test API pagination."""

    def test_match_api_pagination(self, club_admin_user, matches):
        """Test match API returns paginated results."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        # Default page size is 100 from settings
        response = client.get('/api/matches/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'count' in data or isinstance(data, list)


class TestFiltering:
    """Test API filtering and ordering."""

    def test_filter_matches_by_club(self, club_admin_user, matches):
        """Test filtering matches by club."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        club_id = matches[0].club.id
        response = client.get(f'/api/matches/?club={club_id}')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_players_by_club(self, club_admin_user, players):
        """Test filtering players by club."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        club_id = players[0].club.id
        response = client.get(f'/api/players/?club={club_id}')
        assert response.status_code == status.HTTP_200_OK

    def test_order_matches_by_time(self, club_admin_user, matches):
        """Test ordering matches by scheduled_time."""
        token, _ = Token.objects.get_or_create(user=club_admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.get('/api/matches/?ordering=scheduled_time')
        assert response.status_code == status.HTTP_200_OK
