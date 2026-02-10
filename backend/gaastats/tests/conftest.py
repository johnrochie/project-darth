"""
Pytest configuration and fixtures for GAA Stats App
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token

from gaastats.models import Club, Match, Player, MatchEvent, MatchParticipant, UserProfile


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def disable_signals(mocker):
    """Disable post_save signals to prevent auto-creation of UserProfile during tests."""
    mocker.patch.object(post_save, 'send')


@pytest.fixture
def club(db):
    """Create a test club."""
    return Club.objects.create(
        subdomain='testclub',
        name='Test Club',
        county='Kerry',
        logo_url='https://example.com/logo.png',
        primary_colour='#008000',
        secondary_colour='#ffffff'
    )


@pytest.fixture
def club_admin_user(club, disable_signals):
    """Create a club admin user."""
    user = User.objects.create_user(
        username='admin',
        email='admin@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(
        user=user,
        club=club,
        role='admin'
    )
    return user


@pytest.fixture
def club_viewer_user(club, disable_signals):
    """Create a club viewer (read-only) user."""
    user = User.objects.create_user(
        username='viewer',
        email='viewer@test.com',
        password='testpass123'
    )
    UserProfile.objects.create(
        user=user,
        club=club,
        role='viewer'
    )
    return user


@pytest.fixture
def multiple_users(db, club, disable_signals):
    """Create multiple users for testing."""
    users = []
    for i in range(3):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=user,
            club=club,
            role='admin' if i == 0 else 'viewer'
        )
        users.append(user)
    return users


@pytest.fixture
def authenticated_client(club_admin_user, client):
    """Create an authenticated client for API testing."""
    token, _ = Token.objects.get_or_create(user=club_admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return client


@pytest.fixture
def player(club):
    """Create a test player."""
    return Player.objects.create(
        club=club,
        name='Test Player',
        number=10,
        position='Forward'
    )


@pytest.fixture
def players(club):
    """Create multiple players for testing."""
    return [
        Player.objects.create(club=club, name=f'Player {i}', number=i, position='Forward' if i % 2 else 'Back')
        for i in range(1, 12)
    ]


@pytest.fixture
def match(club, players):
    """Create a test match with players."""
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

    # Add home team players
    for i, player in enumerate(players[:6]):
        MatchParticipant.objects.create(
            match=match,
            player=player,
            team='home',
            is_starter=True
        )

    return match


@pytest.fixture
def matches(club):
    """Create multiple matches for testing."""
    opponent = Club.objects.create(
        subdomain='opponent',
        name='Opponent Club',
        county='Cork'
    )

    matches = []
    for i in range(3):
        match = Match.objects.create(
            club=club,
            opponent=opponent,
            venue=club.name if i % 2 else 'Away Venue',
            match_type='championship' if i % 2 else 'league',
            scheduled_time=f'2026-02-{10 + i}T15:00:00Z'
        )
        matches.append(match)
    return matches


@pytest.fixture
def match_event(match, player):
    """Create a test match event."""
    return MatchEvent.objects.create(
        match=match,
        player=player,
        minute=15,
        event_type='goal',
        team='home',
        x_location=50,
        y_location=30
    )


@pytest.fixture
def match_events(match, players):
    """Create multiple match events for testing."""
    events = []
    for i, player in enumerate(players[:5]):
        event = MatchEvent.objects.create(
            match=match,
            player=player,
            minute=10 + i * 5,
            event_type='goal' if i % 2 else 'point',
            team='home',
            x_location=50,
            y_location=30
        )
        events.append(event)
    return events


@pytest.fixture
def api_client():
    """Create an API client for testing API endpoints."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def mock_redis_consumer(mocker):
    """Mock WebSocket consumer for testing WebSocket message flows."""
    consumer = AsyncMock()
    consumer.channel_layer = AsyncMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.channel_layer.group_discard = AsyncMock()
    consumer.channel_layer.group_send = AsyncMock()

    # Mock WebSocket methods
    consumer.accept = AsyncMock()
    consumer.send_json = AsyncMock()
    consumer.close = AsyncMock()

    return consumer


# Django pytest configuration
pytest_plugins = [
    'pytest_django'
]

# Django settings override
def pytest_configure():
    """Configure pytest for Django."""
    from django.conf import settings
    settings.DATABASES['default']['TEST'] = {
        'NAME': 'test_gaastats',
    }
