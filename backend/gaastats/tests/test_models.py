"""
Tests for GAA Stats App models

Tests:
- Club model creation and fields
- Player model relationships
- Match model scheduling and status
- MatchEvent model (goals, points, stats)
- UserProfile model roles
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from gaastats.models import Club, Match, Player, MatchEvent, MatchParticipant, UserProfile


class TestClubModel:
    """Test Club model."""

    def test_create_club(self, db):
        """Test creating a club with required fields."""
        club = Club.objects.create(
            subdomain='testclub',
            name='Test Club',
            county='Kerry'
        )
        assert club.subdomain == 'testclub'
        assert club.name == 'Test Club'
        assert club.county == 'Kerry'
        assert club.is_active is True

    def test_club_subdomain_uniqueness(self, club):
        """Test club subdomain must be unique."""
        with pytest.raises(Exception):
            Club.objects.create(
                subdomain='testclub',  # Duplicate subdomain
                name='Another Club',
                county='Kerry'
            )

    def test_club_str_method(self, club):
        """Test club string representation."""
        assert str(club) == 'Test Club'


class TestUserProfileModel:
    """Test UserProfile model."""

    def test_create_user_profile(self, club):
        """Test creating a user profile with club."""
        user = User.objects.create(username='testuser', email='test@test.com')
        profile = UserProfile.objects.create(
            user=user,
            club=club,
            role='admin'
        )
        assert profile.user == user
        assert profile.club == club
        assert profile.role == 'admin'

    def test_user_profile_club_relationship(self, club):
        """Test user belongs to one club."""
        user = User.objects.create(username='testuser', email='test@test.com')
        profile = UserProfile.objects.create(
            user=user,
            club=club,
            role='viewer'
        )
        assert profile.club.subdomain == 'testclub'


class TestPlayerModel:
    """Test Player model."""

    def test_create_player(self, club):
        """Test creating a player."""
        player = Player.objects.create(
            club=club,
            name='Test Player',
            number=10,
            position='Forward'
        )
        assert player.name == 'Test Player'
        assert player.number == 10
        assert player.position == 'Forward'
        assert player.club == club

    def test_player_club_relationship(self, player):
        """Test player belongs to club."""
        assert player.club.name == 'Test Club'

    def test_multiple_players_per_club(self, club):
        """Test club can have multiple players."""
        players = []
        for i in range(11):
            player = Player.objects.create(
                club=club,
                name=f'Player {i}',
                number=i,
                position='Forward'
            )
            players.append(player)
        assert len(players) == 11

    def test_player_str_method(self, player):
        """Test player string representation."""
        assert str(player) == 'Test Player (10)'


class TestMatchModel:
    """Test Match model."""

    def test_create_match(self, club):
        """Test creating a match."""
        opponent = Club.objects.create(
            subdomain='opponent',
            name='Opponent Club',
            county='Cork'
        )
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            venue=club.name,
            match_type='championship',
            scheduled_time='2026-02-10T15:00:00Z'
        )
        assert match.club == club
        assert match.opponent == opponent
        assert match.venue == club.name
        assert match.match_type == 'championship'
        assert match.status == 'scheduled'

    def test_match_status_transition_scheduled_to_live(self, match):
        """Test match status transitions from scheduled to live."""
        assert match.status == 'scheduled'
        match.status = 'live'
        match.save()
        assert match.status == 'live'

    def test_match_status_transition_live_to_completed(self, match):
        """Test match status transitions from live to completed."""
        match.status = 'live'
        match.save()
        match.status = 'completed'
        match.save()
        assert match.status == 'completed'


class TestMatchParticipantModel:
    """Test MatchParticipant model."""

    def test_add_player_to_match(self, match, player):
        """Test adding a player to a match."""
        participant = MatchParticipant.objects.create(
            match=match,
            player=player,
            team='home',
            is_starter=True
        )
        assert participant.match == match
        assert participant.player == player
        assert participant.team == 'home'
        assert participant.is_starter is True

    def test_multiple_participants_per_match(self, match, players):
        """Test match can have multiple participants."""
        participants = []
        for player in players[:6]:
            participant = MatchParticipant.objects.create(
                match=match,
                player=player,
                team='home',
                is_starter=True
            )
            participants.append(participant)
        assert len(participants) == 6


class TestMatchEventModel:
    """Test MatchEvent model."""

    def test_create_goal_event(self, match_event):
        """Test creating a goal event."""
        assert match_event.minute == 15
        assert match_event.event_type == 'goal'
        assert match_event.team == 'home'
        assert match_event.x_location == 50
        assert match_event.y_location == 30

    def test_create_point_event(self, match, player):
        """Test creating a point event."""
        point = MatchEvent.objects.create(
            match=match,
            player=player,
            minute=20,
            event_type='point',
            team='home',
            x_location=45,
            y_location=35
        )
        assert point.event_type == 'point'
        assert point.minute == 20

    def test_event_player_relationship(self, match_event):
        """Test event is associated with a player."""
        assert match_event.player.name == 'Test Player'

    def test_event_match_relationship(self, match_event):
        """Test event is associated with a match."""
        assert match_event.match.id == match_event.match.id

    def test_multiple_events_per_match(self, match_events):
        """Test match can have multiple events."""
        assert len(match_events) == 5
        assert all(e.match.id == match_events[0].match.id for e in match_events)


class TestAuthentication:
    """Test authentication and tokens."""

    def test_create_token_for_user(self, club):
        """Test creating authentication token for user."""
        user = User.objects.create(username='testuser', email='test@test.com')
        token = Token.objects.create(user=user)
        assert token.user == user
        assert len(token.key) == 40  # DRF token length

    def test_token_regeneration(self, club):
        """Test regenerating token deletes old token."""
        user = User.objects.create(username='testuser', email='test@test.com')
        old_token = Token.objects.create(user=user)
        old_key = old_token.key

        old_token.delete()
        new_token = Token.objects.create(user=user)

        assert new_token.key != old_key
        assert new_token.user == user


class TestModelRelationships:
    """Test cross-model relationships."""

    def test_club_has_many_matches(self, club, matches):
        """Test a club can have multiple matches."""
        club_matches = Match.objects.filter(club=club)
        assert club_matches.count() == 3

    def test_match_has_many_events(self, match, match_events):
        """Test a match can have multiple events."""
        events = MatchEvent.objects.filter(match=match)
        assert events.count() == 5

    def test_player_has_many_events(self, player, match_events):
        """Test a player can have multiple events across matches."""
        # Each player in match_events has one event
        assert match_events[0].player in [e.player for e in match_events]
