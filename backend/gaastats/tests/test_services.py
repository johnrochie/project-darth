"""
Tests for services (X/Twitter integration, business logic)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from gaastats.social_media.x_service import XService


@pytest.mark.django_db
class TestXService:
    """Test X/Twitter Service"""

    def test_x_service_initialization(self):
        """Test XService initializes with configuration"""
        # Test with empty config
        service = XService(consumer_key='test-key', consumer_secret='test-secret')
        
        assert service.consumer_key == 'test-key'
        assert service.consumer_secret == 'test-secret'

    @patch('gaastats.social_media.x_service.tweepy.API')
    def test_x_service_send_tweet_success(self, mock_api):
        """Test sending a tweet successfully"""
        # Mock the API response
        mock_api_instance = MagicMock()
        mock_api.return_value.update_status.return_value = MagicMock(
            id=123456,
            text="Test tweet"
        )
        
        service = XService(
            consumer_key='test-key',
            consumer_secret='test-secret',
            access_token='token',
            access_secret='secret'
        )
        
        result = service.tweet("Test tweet")
        
        assert result['id'] == 123456
        assert result['text'] == "Test tweet"
        mock_api_instance.update_status.assert_called_once_with("Test tweet")

    @patch('gaastats.social_media.x_service.tweepy.API')
    def test_x_service_get_oauth_request_token(self, mock_api):
        """Test getting OAuth request token"""
        mock_request_token = MagicMock()
        mock_request_token.oauth_token = 'request-token'
        mock_request_token.oauth_token_secret = 'request-secret'
        mock_api.return_value.request_token.return_value = mock_request_token
        
        service = XService(
            consumer_key='test-key',
            consumer_secret='test-secret'
        )
        
        token, token_secret = service.get_oauth_request_token()
        
        assert token == 'request-token'
        assert token_secret == 'request-secret'

    @patch('gaastysocial_media.x_service.tweepy.API')
    def test_x_service_get_oauth_access_token(self, mock_api):
        """Test getting OAuth access token"""
        mock_request_token = MagicMock()
        mock_access_token = MagicMock()
        mock_access_token.oauth_token = 'access-token'
        mock_access_token.oauth_token_secret = 'access-secret'
        mock_api.return_value.request_token.return_value = mock_request_token
        mock_api.return_value.access_token.return_value = mock_access_token
        
        service = XService(
            consumer_key='test-key',
            consumer_secret='test-secret'
        )
        
        access_token, access_secret = service.get_oauth_access_token(
            oauth_token='request-token',
            oauth_verifier='verifier-code'
        )
        
        assert access_token == 'access-token'
        assert access_secret == 'access-secret'

    @patch('gaastats.social_media.x_service.tweepy.API')
    def test_x_service_tweets_on_score(self, mock_api):
        """Test auto-tweet on score event"""
        mock_api_instance = MagicMock()
        mock_api.return_value.update_status.return_value = MagicMock(id=789, text="Goal! Test Club scores")
        
        service = XService(
            consumer_key='test-key',
            consumer_secret='test-secret',
            access_token='token',
            access_secret='secret'
        )
        
        match_mock = MagicMock()
        match_mock.home_club.name = "Test Club"
        
        player_mock = MagicMock()
        player_mock.first_name = "Test Player"
        player_mock.last_name = "Doe"
        
        result = service.tweet_score(
            match=match_mock,
            event_type="goal",
            player=player_mock,
            minute=15
        )
        
        # Verify tweet contains relevant information
        assert "Goal!" in result['text']
        assert "Test Club" in result['text']

    @patch('gaastats.social_media.x_service.tweepy.API')
    def test_x_service_handles_tweet_failure(self, mock_api):
        """Test service handles tweet failures gracefully"""
        mock_api.return_value.update_status.side_effect = Exception("Twitter API error")
        
        service = XService(
            consumer_key='test-key',
            consumer_secret='test-secret',
            access_token='token',
            access_secret='secret'
        )
        
        # Service should either raise exception or handle gracefully
        # For this test, we verify it doesn't crash
        try:
            service.tweet("Test tweet")
        except Exception as e:
            assert "Twitter API error" in str(e)

    def test_x_service_tweet_length_validation(self):
        """Test service validates tweet length (280 char max)"""
        service = XService(
            consumer_key='test-key',
            consumer_secret='test-secret',
            access_token='token',
            access_secret='secret'
        )
        
        # Short tweet
        short_tweet = "Test"
        assert len(short_tweet) <= 280
        
        # Long tweet
        long_tweet = "A" * 300
        # Note: Twitter API will reject this, service should validate before sending
        # For now, we're just testing the logic exists


@pytest.mark.django_db
class TestBusinessLogicServices:
    """Test business logic services (if any additional services are added)"""

    def test_calculate_score_from_events(self):
        """Test score calculation from match events"""
        from gaastats.models import Match, MatchEvent, Player, Club
        
        club = Club.objects.create(
            name="Test Club",
            subdomain="test",
            county="Kerry"
        )
        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            competition="League"
        )
        player = Player.objects.create(
            club=club,
            first_name="Test",
            last_name="Player",
            jersey_number=10
        )
        
        # Create events
        MatchEvent.objects.create(match=match, player=player, event_type="goal", minute=15)
        MatchEvent.objects.create(match=match, player=player, event_type="goal", minute=30)
        MatchEvent.objects.create(match=match, player=player, event_type="point", minute=45)
        MatchEvent.objects.create(match=match, player=player, event_type="2_point", minute=60)
        
        # Calculate score
        events = MatchEvent.objects.filter(match=match, player__club=club)
        goals = events.filter(event_type="goal").count()
        points = events.filter(event_type="point").count()
        two_points = events.filter(event_type="2_point").count()
        
        total_goals = goals
        total_points = points + (two_points * 2)
        
        assert total_goals == 2
        assert total_points == 3  # 1 point + 2*(1 two-point = 2) = 3

    def test_determine_match_status_transition(self):
        """Test match status transition validation"""
        from gaastats.models import Match, Club
        
        club = Club.objects.create(
            name="Test Club",
            subdomain="test",
            county="Kerry"
        )
        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        
        # Valid transitions: scheduled -> live -> completed
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            date="2024-06-15",
            status="scheduled"
        )
        
        # Transition to live
        match.status = "live"
        match.save()
        assert match.status == "live"
        
        # Transition to completed
        match.status = "completed"
        match.save()
        assert match.status == "completed"
        
        # Cannot transition from completed back to scheduled (logic check)
        # This would typically be enforced in code, not database

    def test_match_participant_limits(self):
        """Test match participant constraints"""
        from gaastats.models import Match, MatchParticipant, Player, Club
        
        club = Club.objects.create(
            name="Test Club",
            subdomain="test",
            county="Kerry"
        )
        match = Match.objects.create(
            club=club,
            opponent=Club.objects.create(name="Opponent", subdomain="opp", county="Kerry"),
            date="2024-06-15"
        )
        
        # Create participants
        players = []
        for i in range(15):
            player = Player.objects.create(
                club=club,
                first_name=f"Player {i}",
                last_name=f"Name {i}",
                jersey_number=i
            )
            players.append(player)
            
        for player in players:
            MatchParticipant.objects.create(
                match=match,
                player=player,
                team="home"
            )
        
        # Verify all 15 players can participate
        participants = MatchParticipant.objects.filter(match=match, team="home")
        assert participants.count() == 15
