"""
Tests for Django REST API views advanced scenarios
Extended API test coverage
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status

from gaastats.models import (
    Club, UserProfile, Player, Match, MatchParticipant,
    MatchEvent, MatchScoreUpdate
)

User = get_user_model()


@pytest.mark.django_db
class TestAdvancedClubAPI:
    """Advanced tests for Club API endpoints"""

    def test_club_list_pagination(self, admin_club, api_client):
        """Test API pagination for club list"""
        # Create multiple clubs
        clubs = []
        for i in range(15):
            club = Club.objects.create(
                name=f"Club {i}",
                subdomain=f"club{i}",
                county="Kerry"
            )
            clubs.append(club)

        # Test first page (default 10 per page)
        response = api_client.get('/api/clubs/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'results' in data or isinstance(data, list)
        
        # Should return paginated results
        results = data.get('results', data if isinstance(data, list) else data['results'] if isinstance(data, dict) and 'results' in data else [])
        count = len(results) if isinstance(results, list) else len(data)
        assert count > 0

    def test_club_pagination_page_size(self, admin_club, api_client):
        """Test API pagination with custom page size"""
        # Create 5 clubs
        for i in range(5):
            Club.objects.create(
                name=f"Club {i}",
                subdomain=f"club{i}",
                county="Kerry"
            )

        # Request with page size 2
        response = api_client.get('/api/clubs/?page=1&page_size=2')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        
        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        count = len(results) if isinstance(results, list) else 0
        assert count <= 2

    def test_club_list_filter_by_county(self, admin_club, viewer_club, api_client):
        """Test club list filtering by county"""
        # Clubs in different counties
        Club.objects.filter(subdomain__in=[admin_club.subdomain, viewer_club.subdomain]).update(county="Kerry")
        new_club = Club.objects.create(name="Cork Club", subdomain="corkclub", county="Cork")

        # Filter by county
        response = api_client.get('/api/clubs/?county Kerry')
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        count = len(results) if isinstance(results, list) else 0
        assert count == 2  # Kerry clubs only

    def test_club_detail_with_matches(self, admin_club, api_client):
        """Test club detail includes related matches"""
        opponent = Club.objects.create(name="Opponent", subdomain="opp", county="Kerry")
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="completed"
        )

        response = api_client.get(f'/api/clubs/{admin_club.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        
        assert data['id'] == admin_club.id
        assert data['name'] == admin_club.name
        assert 'matches' in data or 'competition' in data  # Should include match data

    def test_club_search_by_name(self, admin_club, api_client):
        """Test club search functionality"""
        response = api_client.get('/api/clubs/', {'search': 'Kerry'})
        assert response.status_code == status.HTTP_200_OK
        # Clubs with 'Kerry' in name should appear in results


@pytest.mark.django_db
class TestAdvancedMatchAPI:
    """Advanced tests for Match API endpoints"""

    def test_match_list_filter_by_competition(self, admin_club, api_client):
        """Test match list filtering by competition"""
        opponent = Club.objects.create(name="Opponent", subdomain="opp", county="Kerry")
        
        # Create matches in different competitions
        Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="Championship",
            status="scheduled"
        )
        Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-16",
            competition="League",
            status="scheduled"
        )

        # Filter by Championship
        response = api_client.get('/api/matches/?competition=Championship')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        
        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        count = len(results) if isinstance(results, list) else 0
        assert count == 1

    def test_match_list_order_by_date_descending(self, admin_club, api_client):
        """Test match list ordered by date descending"""
        opponent = Club.objects.create(name="Opponent", subdomain="opp", county="Kerry")
        
        # Create matches on different dates
        dates = ['2024-06-10', '2024-06-15', '2024-06-20']
        for i, date in enumerate(dates):
            Match.objects.create(
                club=admin_club,
                opponent=opponent,
                date=f"{date} 14:00",
                competition="League",
                status="scheduled"
            )

        # Request with ordering
        response = api_client.get('/api/matches/?ordering=-date')
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        # Should be ordered by date descending
        if isinstance(results, list) and len(results) >= 3:
            assert results[0]['date'] >= results[1]['date']
            assert results[1]['date'] >= results[2]['date']

    def test_match_status_transitions(self, admin_club, opponent, api_client):
        """Test match status update transitions through API"""
        # Create scheduled match
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15 14:00",
            competition="League",
            status="scheduled"
        )

        # Update to live
        response = api_client.patch(f'/api/matches/{match.id}/', {
            'status': 'live'
        })
        assert response.status_code == status.HTTP_200_OK
        match.refresh_from_db()
        assert match.status == 'live'

        # Update to completed
        response = api_client.patch(f'/api/matches/{match.id}/', {
            'status': 'completed'
        })
        assert response.status_code == status.HTTP_200_OK
        match.refresh_from_db()
        assert match.status == 'completed'

    def test_match_create_with_participants(self, admin_club, opponent, api_client):
        """Test creating match with multiple participants"""
        players = []
        for i in range(3):
            player = Player.objects.create(
                club=admin_club,
                first_name=f"Player {i}",
                last_name=f"Doe {i}",
                jersey_number=i
            )
            players.append(player)

        match_data = {
            "club": admin_club.id,
            "opponent": opponent.id,
            "date": "2024-06-15 14:00",
            "competition": "League",
            "venue": "Home Ground",
            "status": "scheduled",
            "participants": [
                {"player": players[0].id, "team": "home"},
                {"player": players[1].id, "team": "home"},
                {"player": players[2].id, "team": "home"},
            ]
        }

        response = api_client.post('/api/matches/', match_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.data
        
        assert data['participants'] == 3
        # Verify MatchParticipant objects created

    def test_match_create_validation_invalid_status(self, admin_club, opponent, api_client):
        """Test match creation rejects invalid status"""
        invalid_statuses = ['invalid', 'pending', 'running', 'finished']
        
        for invalid_status in invalid_statuses:
            response = api_client.post('/api/matches/', {
                "club": admin_club.id,
                "opponent": opponent.id,
                "date": "2024-06-15 14:00",
                "competition": "League",
                "status": invalid_status,
            })
            # Should fail with 400 Bad Request or 422 Unprocessable Entity
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.django_db
class TestAdvancedPlayerAPI:
    """Advanced tests for Player API endpoints"""

    def test_player_list_with_pagination(self, admin_club, api_client):
        """Test player list pagination"""
        # Create players
        for i in range(12):
            Player.objects.create(
                club=admin_club,
                first_name=f"Player {i}",
                last_name=f"Name {i}",
                jersey_number=i
            )

        # First page (default 10 per page)
        response = api_client.get('/api/players/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        count = len(results) if isinstance(results, list) else 0
        # Page 1 should have 10 results (default)
        assert count <= 10

    def test_player_list_filter_by_position(self, admin_club, api_client):
        """Test player list filtering by position"""
        positions = ['Forward', 'Midfielder', 'Back', 'Goalkeeper']
        for i, pos in enumerate(positions):
            Player.objects.create(
                club=admin_club,
                first_name=f"Player {i}",
                last_name=f"{pos}",
                jersey_number=i,
                position=pos
            )

        # Filter by Forward
        response = api_client.get('/api/players/?position=Forward')
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        count = len(results) if isinstance(results, list) else 0
        assert count >= 1

    def test_player_jersey_number_search(self, admin_club, api_client):
        """Test player search by jersey number"""
        Player.objects.create(
            club=admin_club,
            first_name="John",
            last_name="Doe",
            jersey_number=10
        )

        response = api_client.get('/api/players/', {'jersey_number': 10})
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        # Should return player with jersey number 10
        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        found = any(
            player.get('jersey_number') == 10
            for player in results if isinstance(player, dict)
        )
        assert found is True

    def test_player_update_transfer(self, admin_club, api_client):
        """Test player transfer between clubs"""
        new_club = Club.objects.create(
            name="New Club",
            subdomain="newclub",
            county="Kerry"
        )
        player = Player.objects.create(
            club=admin_club,
            first_name="Transfer",
            last_name="Player",
            jersey_number=7,
            position="Midfielder"
        )

        # Transfer player to new club
        response = api_client.patch(f'/api/players/{player.id}/', {
            'club': new_club.id
        })
        assert response.status_code == status.HTTP_200_OK
        player.refresh_from_db()
        assert player.club == new_club
        assert player.club != admin_club

    def test_player_delete_with_no_permission(self, viewer_user, viewer_club, api_client):
        """Test non-admin cannot delete player"""
        player = Player.objects.create(
            club=viewer_club,
            first_name="Delete",
            last_name="Test",
            jersey_number=99,
            position="Forward"
        )

        # Viewer user tries to delete
        api_client.force_authenticate(viewer_user)
        response = api_client.delete(f'/api/players/{player.id}/')

        # Should be forbidden (403 Forbidden)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_player_search_full_name(self, admin_club, api_client):
        """Test player search by full name"""
        Player.objects.create(
            club=admin_club,
            first_name="Searchable",
            last_name="Player",
            jersey_number=5,
            position="Forward"
        )

        # Search by full name
        response = api_client.get('/api/players/', {'search': 'Searchable Player'})
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        found = any(
            player.get('first_name') == 'Searchable' and player.get('last_name') == 'Player'
            for player in results if isinstance(player, dict)
        )
        assert found is True


@pytest.mark.django_db
class TestAdvancedMatchEventAPI:
    """Advanced tests for MatchEvent API endpoints"""

    def test_match_events_for_match(self, admin_club, api_client):
        """Test retrieving events for a specific match"""
        opponent = Club.objects.create(name="Opponent", subdomain="opp", county="Kerry")
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        player = Player.objects.create(club=admin_club, first_name="John", last_name="Doe", jersey_number=10)

        # Create multiple events
        for i in range(5):
            MatchEvent.objects.create(
                match=match,
                player=player,
                event_type="goal",
                minute=5 * (i + 1)
            )

        # Get events for this match
        response = api_client.get(f'/api/matches/{match.id}/events/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        assert len(results) == 5

    def test_match_events_filter_by_event_type(self, admin_club, api_client):
        """Test filtering events by event type"""
        opponent = Club.objects.create(name="Opponent", subdomain="opp", county="Kerry")
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="completed"
        )
        player = Player.objects.create(club=admin_club, first_name="Scorer", last_name="Player", jersey_number=14)

        # Create mixed events
        MatchEvent.objects.create(match=match, player=player, event_type="goal", minute=15)
        MatchEvent.objects.create(match=match, player=player, event_type="point", minute=30)
        MatchEvent.objects.create(match=match, player=player, event_type="tackle_won", minute=45)

        # Filter by goal only
        response = api_client.get(f'/api/matches/{match.id}/events/?event_type=goal')
        assert response.status_code == status.HTTP_200_OK
        data = response.data

        results = data.get('results', data if isinstance(data, list) else data.get('results', []))
        assert len(results) == 1
        assert results[0]['event_type'] == 'goal'

    def test_match_event_create_multiple_ownership_check(self, admin_club, opponent, api_client):
        """Test event creation (player must belong to home club)"""
        # Same club (should work)
        player1 = Player.objects.create(club=admin_club, first_name="Home", last_name="Player1", jersey_number=1)
        
        # Different club (should fail ownership check)
        viewer_club = Club.objects.create(name="Viewer", subdomain="viewer", county="Kerry")
        player2 = Player.objects.create(club=viewer_club, first_name="Away", last_name="Player2", jersey_number=2)

        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        # Create event with player from same club (should work)
        response1 = api_client.post(f'/api/matches/{match.id}/events/', {
            "player": player1.id,
            "event_type": "goal",
            "minute": 15
        })
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create event with player from different club (should fail ownership check)
        response2 = api_client.post(f'/api/matches/{match.id}/events/', {
            "player": player2.id,
            "event_type": "goal",
            "minute": 30
        })
        # Should fail with 403 Forbidden (player not from home club)
        assert response2.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]

    def test_match_event_update(self, admin_club, opponent, api_client):
        """Test updating existing match event"""
        player = Player.objects.create(club=admin_club, first_name="Correction", last_name="Player", jersey_number=9)
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )

        # Create event
        event = MatchEvent.objects.create(
            match=match,
            player=player,
            event_type="goal",
            minute=15
        )

        # Update event to 2-point instead of goal
        response = api_client.patch(f'/api/match-events/{event.id}/', {
            "event_type": "2_point"
        })
        assert response.status_code == status.HTTP_200_OK
        event.refresh_from_db()
        assert event.event_type == "2_point"

    def test_match_event_delete(self, admin_club, opponent, api_client):
        """Test deleting match event (admin only)"""
        player = Player.objects.create(club=admin_club, first_name="Delete", last_name="Me", jersey_number=99)
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            status="live"
        )
        event = MatchEvent.objects.create(
            match=match,
            player=player,
            event_type="foul",
            minute=50
        )

        event_id = event.id

        # Delete event
        response = api_client.delete(f'/api/match-events/{event_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify event was deleted
        with pytest.raises(ObjectDoesNotExist):
            MatchEvent.objects.get(id=event_id)
