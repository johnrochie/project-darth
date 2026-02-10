"""
Tests for PDF/Excel report generation
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from io import BytesIO
import zipfile

from gaastats.models import Club, UserProfile, Player, Match
from gaastats.reports import (
    generate_match_report,
    generate_player_report,
    generate_season_report
)

User = get_user_model()


@pytest.mark.django_db
class TestMatchReportGeneration:
    """Test PDF match report generation"""

    def test_generate_match_report_pdf(self, admin_club, rf):
        """Test match report PDF generation"""
        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="Championship",
            venue="Home Ground",
            status="completed"
        )

        # Generate PDF report
        report = generate_match_report(match.id)
        
        # Verify PDF was generated
        assert report is not None
        assert isinstance(report, bytes)
        # PDF files typically start with %PDF-
        assert report.startswith(b'%PDF-') or len(report) > 1000

    def test_generate_match_report_with_events(self, admin_club):
        """Test match report includes events"""
        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        match = Match.objects.create(
            club=admin_club,
            opponent=opponent,
            date="2024-06-15",
            competition="League",
            venue="Home Ground",
            status="completed"
        )
        player = Player.objects.create(club=admin_club, first_name="Test", last_name="Player", jersey_number=10)
        
        # Add events
        from gaastats.models import MatchEvent
        MatchEvent.objects.create(match=match, player=player, event_type="goal", minute=15)
        MatchEvent.objects.create(match=match, player=player, event_type="point", minute=30)
        
        # Generate report
        report = generate_match_report(match.id)
        
        assert report is not None
        assert len(report) > 1000

    def test_generate_match_report_nonexistent_match(self):
        """Test report generation with non-existent match ID"""
        try:
            report = generate_match_report(99999)
            # Should either return None or raise appropriate error
            assert False  # Should not get here
        except Exception as e:
            # Expected to raise error for non-existent match
            assert "not found" in str(e) or "does not exist" in str(e)


@pytest.mark.django_db
class TestPlayerReportGeneration:
    """Test PDF player report generation"""

    def test_generate_player_report_pdf(self, admin_club):
        """Test player report PDF generation"""
        player = Player.objects.create(
            club=admin_club,
            first_name="Test",
            last_name="Player",
            jersey_number=10,
            position="Forward"
        )

        # Generate PDF report
        report = generate_player_report(player.id)
        
        assert report is not None
        assert isinstance(report, bytes)

    def test_generate_player_report_with_matches(self, admin_club):
        """Test player report includes match statistics"""
        player = Player.objects.create(
            club=admin_club,
            first_name="Scorer",
            last_name="Player",
            jersey_number=14,
            position="Forward"
        )
        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        
        # Create matches and events
        for i in range(3):
            match = Match.objects.create(
                club=admin_club,
                opponent=opponent,
                date=f"2024-06-{15+i:02d}",
                competition="League",
                status="completed"
            )
            # Add goals
            from gaastats.models import MatchEvent
            MatchEvent.objects.create(
                match=match,
                player=player,
                event_type="goal",
                minute=15
            )
        
        # Generate report
        report = generate_player_report(player.id)
        
        assert report is not None
        assert len(report) > 1000  # PDF with match data


@pytest.mark.django_db
class TestSeasonReportGeneration:
    """Test PDF season report generation"""

    def test_generate_season_report_pdf(self, admin_club):
        """Test season report PDF generation for club"""
        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        
        # Create matches for the season
        for month in range(6):
            Match.objects.create(
                club=admin_club,
                opponent=opponent,
                date=f"2024-0{month+1:02d}-15",
                competition="League",
                status="completed"
            )

        # Generate season report
        report = generate_season_report(admin_club.id)
        
        assert report is not None
        assert isinstance(report, bytes)
        assert len(report) > 1000

    def test_generate_season_report_empty_season(self, admin_club):
        """Test season report with no matches"""
        # Don't create any matches
        
        # Generate season report for empty season
        report = generate_season_report(admin_club.id)
        
        # Should still generate PDF, just with minimal data
        assert report is not None

    def test_generate_season_report_with_multiple_clubs(self, admin_club):
        """Test season report filtering"""
        # Create multiple clubs
        opponent1 = Club.objects.create(name="Opponent 1", subdomain="opp1", county="Kerry")
        opponent2 = Club.objects.create(name="Opponent 2", subdomain="opp2", county="Cork")
        opponent3 = Club.objects.create(name="Opponent 3", subdomain="opp3", county="Limerick")
        
        # Create matches for admin_club
        for opponent in [opponent1, opponent2, opponent3]:
            Match.objects.create(
                club=admin_club,
                opponent=opponent,
                date="2024-06-15",
                competition="League",
                status="completed"
            )
        
        # Create matches for opponent club (should not be included)
        new_club = Club.objects.create(name="New Club", subdomain="new", county="Kerry")
        Match.objects.create(
            club=new_club,
            opponent=admin_club,
            date="2024-06-16",
            competition="League",
            status="completed"
        )
        
        # Generate season report for admin_club only
        report = generate_season_report(admin_club.id)
        
        assert report is not None


@pytest.mark.django_db
class TestExcelReportGeneration:
    """Test Excel report generation"""

    def test_generate_player_excel_report(self, admin_club):
        """Test Excel report for player statistics"""
        from gaastats.reports import generate_player_excel_report

        player = Player.objects.create(
            club=admin_club,
            first_name="Test",
            last_name="Player",
            jersey_number=10,
            position="Midfielder"
        )

        # Generate Excel report
        excel_file = generate_player_excel_report(player.id)
        
        assert excel_file is not None
        # Excel files start with PK (Office Open XML format)
        assert excel_file.startswith(b'PK\x03\x04') or len(excel_file) > 1000
        assert excel_file.endswith(b'.xlsx')

    def test_generate_season_excel_report(self, admin_club):
        """Test Excel report for club season statistics"""
        from gaastats.reports import generate_season_excel_report

        opponent = Club.objects.create(
            name="Opponent",
            subdomain="opp",
            county="Kerry"
        )
        
        # Create matches
        for i in range(5):
            Match.objects.create(
                club=admin_club,
                opponent=opponent,
                date=f"2024-06-{15+i:02d}",
                competition="League",
                status="completed"
            )

        # Generate season Excel report
        excel_file = generate_season_excel_report(admin_club.id)
        
        assert excel_file is not None
        assert excel_file.startswith(b'PK\x03\x04') or len(excel_file) > 1000

    def test_excel_report_file_download(self, admin_club):
        """Test Excel report file can be downloaded"""
        from gaastats.reports import generate_season_excel_report

        # Generate Excel report
        excel_file = generate_season_excel_report(admin_club.id)
        
        # Simulate download by writing to BytesIO
        bytes_io = BytesIO(excel_file)
        
        # Verify file is complete
        bytes_io.seek(0)
        content = bytes_io.read()
        
        assert len(content) > 1000
