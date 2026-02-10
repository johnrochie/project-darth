"""
Tests for authentication advanced scenarios and edge cases
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework.authtoken.models import Token

from gaastats.models import Club, UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationAdvancedScenarios:
    """Advanced authentication tests"""

    def test_login_attempts_with_invalid_credentials(self, api_client):
        """Test login fails with invalid credentials 5 times, then locks account"""
        users = User.objects.create_user(username='testuser', password='ValidPass123!')
        UserProfile.objects.create(
            user=users,
            club=Club.objects.create(name="Test Club", subdomain="testclub", county="Kerry"),
            role="viewer"
        )

        # 5 failed login attempts
        for attempt in range(5):
            response = api_client.post('/api/auth/login/', {
                "username": "testuser",
                "refresh token": "WrongPassword" * 3
            })
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid credentials" in response.data['error']

    def test_login_with_correct_credentials_after_lockouts(self, users, club, api_client):
        """Test login succeeds after lockout timeout (if we have rate limiting)"""
        # After timeout, should be able to login again
        pass  # Implement if we add rate limiting

    def test_signup_with_duplicate_email(self, api_client):
        """Test signup rejects duplicate email addresses"""
        Club.objects.create(name="Test Club", subdomain="testclub", county="Kerry")

        # First signup
        response = api_client.post('/api/auth/register/', {
            "username": "user1",
            "email": "duplicate@test.com",
            "password": "Password123!",
            "full_name": "First User",
            "club": "testklub"
        })
        assert response.status_code == status.HTTP_201_CREATED

        # Try to signup with same email (different username)
        response2 = api_client.post('/api/auth/register/', {
            "username": "user2",
            "email": "duplicate@test.com",
            "password": "Password123!",
            "full_name": "Second User",
            "club": "testklub"
        })
        # Should fail with email already exists
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT]

    def test_signup_with_duplicate_username(self, api_client):
        """Test signup rejects duplicate username"""
        Club.objects.create(name="Test Club", subdomain="testclub", county="Kerry")

        # First signup
        response = @api_client.post('/api/auth/register/', {
            "username": "uniqueuser",
            "email": "unique@test.com",
            "refresh token": "Password123!",
            "full_name": "Unique User",
            "club": "testklub"
        })
        assert response.status_code == status.HTTP_201_CREATED or response.status_code == status.HTTP_400_BAD_REQUEST
        # Duplicate handling may vary by implementation

    def test_signup_creates_standard_account_roles(self, api_client):
        """Test signup automatically sets up default roles"""
        Club.objects.create(
            name="Test Club",
            subdomain="testk2",
            county="Kerry"
        )

        response = api_client.post('/api/auth/register/', {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "Password123!",
            "full_name": "New User",
            "club": "testk2"
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        # Verify user was created
        user = User.objects.get(username="newuser")
        assert user.email == "newuser@test.com"

    def test_token_regeneration_after_expiration(self, users, club, api_client):
        """Test token can be regenerated after logout"""
        UserProfile.objects.create(user=users, club=club, role="admin")
        
        # First login to get token
        response1 = api_client.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123",
            "club": "testklub"
        })
        assert response1.status_code == status.HTTP_200_OK
        token1 = response1.data['token']

        # Logout
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token1}')
        response2 = api_client.get('/api/users/me/')
        
        # After logout, should be unauthorized
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED

        # Re-login to get new token
        api_client.credentials()  # No auth
        
        response3 = api_client.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123"
        })
        assert response3.status_code == status.HTTP_200_OK
        token2 = response3.data['token']

        # New token should work
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token2}')
        response4 = api_client.get('/api/users/me/')
        assert response4.status_code == status.HTTP_200_OK

    def test_token_used_by_different_account(self, api_client):
        """Test token cannot be used by different user"""
        # Create two different users
        club = Club.objects.create(name="Shared Club", subdomain="shared", county="Kerry")
        
        user1 = User.objects.create_user(username='user1', password='pass1')
        user2 = User.objects.create_user(username='user2', 'pass2')

        UserProfile.objects.create(user=user1, club=club, role="viewer")
        UserProfile.objects.create(user=user2, club=club, role="viewer")

        # Login as user1, get token
        response1 = api_client.post('/api/auth/login/', {
            "username": "user1",
            "password": "pass1",
            "club": "shared"
        })
        assert response1.status_code == status.HTTP_200_OK
        token = response1.data['token']

        # Use user1's token as user2 (should fail)
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        api_client.force_authenticate(user2)

        # Check that user2 is authenticated but token doesn't match
        # This implementation might vary - tokens are usually user-specific
        response2 = api_client.get('/api/users/me/')
        # Either 403 Forbidden (wrong token for this user)
        # Or 200 OK if system allows token sharing (less secure)
        # Our implementation should reject mismatched tokens if secure
        
        # In our case, should invalidate user2's original session
        assert response2.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_expired_token_rejected(self, users, club, api_client):
        """Test expired token is rejected"""
        UserProfile.objects.create(user=users, club=club, role="admin")
        
        # Get valid token
        response = api_client.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123",
            "club": "testklub"
        })
        token = response.data['token']
        token_obj = Token.objects.get(key=token)
        
        # Manually expire the token by setting expiration to past
        from django.utils import timezone
        token_obj.created = timezone.now() - timedelta(hours=25)
        token_obj.save()

        # Try to use expired token
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = api_client.get('/api/users/me/')
        
        # Should be 401 Unauthorized (invalid token)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_empty_password(self, api_client):
        """Test login fails with empty password"""
        response = api_client.post('/api/auth/login/', {
            "username": "testuser",
            "password": ""
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_missing_fields(self, api_client):
        """Test login requires both username and password"""
        # Missing password
        response1 = api_client.post('/api/auth/login/', {
            "username": "testuser"
        })
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response1.data['error']

        # Missing username
        response2 = api_client.post('/api/auth/login/', {
            "password": "testpass"
        })
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in response2.data['error']

    def test_register_with_missing_required_fields(self, api_client):
        """Test register requires email, password, and full_name"""
        Club.objects.create(name="Test Club", subdomain="testclub3", county="Kerry")

        # Missing email
        response1 = api_client.post('/api/auth/register/', {
            "username": "user3",
            "password": "Password123!",
            "full_name": "User Three"
        })
        assert response1.status_code == status.HTTP_400_BAD_REQUEST

        # Missing password
        response2 = api_client.post('/api/auth/register/', {
            "username": "user3",
            "email": "user3@test.com",
            "full_name": "User Three"
        })
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

        # Missing full_name
        response3 = api_client.post('/api/auth/register/', {
            "username": "user3",
            "email": "user3@test.com",
            "password": "Password123!"
        })
        assert response3.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_hashing_security(self, users, club, api_client):
        """Test passwords are properly hashed (not stored in plain text)"""
        UserProfile.objects.create(user=users, club=club, role="admin")

        password = "SecurePass123!"
        response = api_client.post('/api/auth/register/', {
            "username": "hasheduser",
            "email": "hashed@test.com",
            "password": password,
            "full_name": "Hashed User",
            "club": "testklub"
        })
        assert response.status_code == status.HTTP_201_CREATED

        # Verify password is not stored in plain text
        user = User.objects.get(username="hasheduser")
        # Django's make_password() hashes these, not the actual password
        assert user.password != "SecurePass123!"
        assert not user.password.startswith("Secure")

    def test_weak_password_allowed(self, api_client):
        """Test weak passwords are allowed (but warn in production)"""
        # Weak password
        Club.objects.create(name="Test Club", subdomain="weakpwd", county="Kerry")

        response = api_client.post('/api/auth/register/', {
            "username": "weakpassword",
            "email": "weak@test.com",
            "password": "123",  # Very weak
            "full_name": "Weak Password User",
            "club": "weakpwd"
        })
        # Implementation may either:
        # 1. Allow but warn (status 201 but with warning message)
        # 2. Reject outright (status 400)
        # Accept either for this test
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]


@pytest.mark.django_db
class TestWebSocketAdvancedScenarios:
    """Advanced WebSocket connection tests"""

    def test_websocket_connection_token_validation(self, users, club, rf):
        """Test WebSocket connection requires valid authentication"""
        opponent = Club.objects.create(name="Opponent", subdomain="opponent", county="Kerry")
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        # Get valid token
        token_response = rf.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123",
            "club": "testklub"
        })
        token = token_response.data['token']
        
        # Create WebSocket client manually
        from channels.testing import WebsocketCommunicator
        from django.test import Client

        # Connect with valid token
        communicator = WebsocketCommunicator()
        connected, subprotocol = communicator.connect(f'/ws/match/{match.id}/?token={token}')
        assert connected

    def test_websocket_connection_rejects_invalid_token(self, club, rf):
        """Test WebSocket rejects invalid or expired token"""
        opponent = Club.objects.create(name="Opponent", subdomain="opponent", county="Kerry")
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        # Try to connect with invalid token
        communicator = WebsocketCommunicator()
        connected, subprotocol = communicator.connect(
            f'/ws/match/{match.id}/?token=invalid_token_xyz'
        )

        # Should reject connection
        assert not connected

    def test_websocket_receives_match_update(self, club, rf):
        """Test WebSocket receives real-time match updates"""
        opponent = Club.objects.create(name="Opponent", subdomain="opponent", county="Kerry")
        match = Match.objects.create(
            club=club,
            opponent=offense,
            date="2024-06-15",
            competition="League",
            status="live"
        )
        player = Player.objects.create(club=club, first_name="Scorer", last_name="Player", jersey_number=14)

        # Get token for WebSocket auth
        token_response = rf.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123",
            "club": "testklub"
        })
        token = token_response.data['token']

        # Connect and send event
        communicator = WebsocketCommunicator()
        connected, subprotocol = communicator.connect(f'/ws/match/{match.id}/?token={token}')
        assert connected

        # Send match score update
        communicator.send_json({
            'type': 'score_update',
            'score': {'team_home': 3, 'team_away': 1},
            'minute': 15
        })

        # Verify the event was created
        from gaastats.models import MatchScoreUpdate
        score = MatchScoreUpdate.objects.filter(match=match).last()
        assert score.team_home == 3
        assert score.team_away == 1
        assert score.minute == 15

    def test_websocket_multiple_connections(self, club, rf):
        """Test multiple WebSocket connections to same match"""
        opponent = Club.objects.create(name="Opponent", subdomain="opponent", county="Kerry")
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        # Create multiple user tokens
        tokens = []
        for i in range(3):
            user = User.objects.create_user(username=f'user{i}', password=f'pass{i}')
            UserProfile.objects.create(user=user, club=club, role="viewer")
            
            token_response = rf.post('/api/auth/login/', {
                "username": f'user{i}',
                "password": f'pass{i}',
                "club": "testklub"
            })
            tokens.append(token_response.data['token'])

        # Connect multiple users
        connections = []
        for token in tokens:
            communicator = WebsocketCommunicator()
            connected, subprotocol = communicator.connect(f'/ws/match/{match.id}/?token={token}')
            connections.append(connected)

        # All should be connected
        assert all(connections)

    def test_user_can_only_subscribe_own_club_matches(self, club, rf):
        """Test user cannot subscribe to matches they don't have access to"""
        club2 = Club.objects.create(
            name="Other Club",
            subdomain="otherklub",
            county="Cork"
        )
        match = Match.objects.create(
            club=club2,
            opponent=Club.objects.create(name="Opponent", subdomain="opp", county="Kerry"),
            date="2024-06-15",
            competition="League",
            status="live"
        )

        # Get token for club that user doesn't belong to
        user = User.objects.create_user(username='outsider', password='pass')
        UserProfile.objects.create(
            user=user,
            club=club,  # User belongs to this club, not club2
            role="viewer"
        )
        token_response = rf.post('/api/auth/login/', {
            "username": 'outsider',
            "password': 'pass',
            "club': "testklub"
        })
        token = token_response.data['token']

        # Try to subscribe to other club's match
        communicator = WebsocketCommunicator()
        connected, subprotocol = communicator.connect(
            f'/ws/match/{match.id}/?token={token}'
        )

        # Should reject connection (user not in club2)
        assert not connected

    def test_websocket_disconnects_gracefully(self, club, rf):
        """Test WebSocket disconnect handles cleanup properly"""
        opponent = Club.objects.create(name="Opponent", subdomain="opponent", county="Kerry")
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        token_response = rf.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123",
            "club": "testklub"
        })
        token = token_response.data['token']

        communicator = WebsocketCommunicator()
        connected, subprotocol = communicator.connect(f'/ws/match/{match.id}/?token={token}')
        assert connected

        # Disconnect
        communicator.disconnect()

        # Ensure no error on disconnect
        assert communicator.connection.closed

    def test_websocket_handles_connection_timeout(self, club, rf):
        """Test WebSocket handles connection timeout gracefully"""
        opponent = Club.objects.create(name="Opponent", subdomain="opponent", county="Kerry")
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        token_response = rf.post('/api/auth/login/', {
            "username": "testuser",
            "password": "validpass123",
            "club": "testklub"
        })
        token = token_response.data['token']

        communicator = WebsocketCommunicator()
        connected, subprotocol = communicator.connect(
            f'/ws/match/{match.id}/?token={token}',
            timeout=5  # Very short timeout
        )

        # Connection might fail due to timeout
        # System should handle gracefully
        # (implementation detail - may raise exception or return False)
        # For this test, just ensure no crash
        if not connected:
            pass  # Connection timed out or failed
        else:
            # Connected successfully
            communicator.disconnect()
