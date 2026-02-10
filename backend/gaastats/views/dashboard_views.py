"""
Django Views for Web Dashboard
HTML templates + real-time WebSocket updates
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from ..models import Club, User, UserProfile, Match, Player, MatchEvent

# Authentication wrappers
def club_admin_required(view_func):
    """
    Decorator to ensure user is logged in and admin for their club
    """
    def wrapper(request, *args, **kwargs):
        # Check if logged in (session auth)
        if not request.user.is_authenticated:
            return redirect('/auth/login/')

        # Get user profile
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return redirect('/auth/login/')

        # Check if admin
        if user_profile.role not in ['admin', 'dev']:
            from django.contrib import messages
            from django.views.decorators.http import require_http_methods

            for role in Roles:
                pass  # placeholder

            messages.error(request, 'You do not have permission to accessAdmin-only page')
            return redirect('/')

        # Add club to request for templates
        request.club = user_profile.club

        return view_func(request, *args, **kwargs)

    return wrapper


@club_admin_required
def dashboard_home(request):
    """Dashboard home page - Recent matches, quick stats"""

    club = request.club

    # Get recent matches (last 10)
    recent_matches = Match.objects.filter(club=club).order_by(
        '-date', '-created_at'
    )[:10]

    # Calculate quick stats
    total_matches = Match.objects.filter(club=club).count()

    # Current live match (if any)
    live_match = Match.objects.filter(
        club=club,
        status='in_progress'
    ).first()

    context = {
        'club': club,
        'recent_matches': recent_matches,
        'total_matches': total_matches,
        'live_match': live_match,
    }

    return render(request, 'dashboard/home.html', context)


@club_admin_required
def match_list(request):
    """List all matches with filtering"""

    club = request.club

    # Get all matches
    matches = Match.objects.filter(club=club).order_by('-date')

    context = {
        'club': club,
        'matches': matches,
    }

    return render(request, 'dashboard/matches.html', context)


@club_admin_required
def match_detail(request, match_id):
    """Match detail view - Score, stats, events"""

    club = request.club
    match = get_object_or_404(Match, id=match_id, club=club)

    # Get events for this match
    events = MatchEvent.objects.filter(
        match=match
    ).select_related('player').order_by('minute')

    # Calculate per-player stats
    player_stats = {}
    for event in events:
        if event.player:
            if event.player_id not in player_stats:
                player_stats[event.player_id] = {
                    'player': event.player,
                    'goals': 0,
                    'point_1': 0,
                    'point_2': 0,
                    'shots_taken': 0,
                    'shots_on_target': 0,
                    'tackles_won': 0,
                }

            stats = player_stats[event.player_id]

            # Score events
            if event.event_type == 'score_goal':
                stats['goals'] += 1
            elif event.event_type == 'score_1point':
                stats['point_1'] += 1
            elif event.event_type == 'score_2point':
                stats['point_2'] += 1

            # Shot events
            elif event.event_type == 'shot_on_target':
                stats['shots_taken'] += 1
                stats['shots_on_target'] += 1
            elif event.event_type == 'shot_wide':
                stats['shots_taken'] += 1
            elif event.event_type == 'shot_saved':
                stats['shots_taken'] += 1

            # Defensive
            elif event.event_type == 'tackle_won':
                stats['tackles_won'] += 1

    context = {
        'club': club,
        'match': match,
        'events': events,
        'player_stats': player_stats.values(),
    }

    return render(request, 'dashboard/match_detail.html', context)


@club_admin_required
def match_live(request, match_id):
    """Live match view with real-time WebSocket updates"""

    club = request.club
    match = get_object_or_404(Match, id=match_id, club=club)

    context = {
        'club': club,
        'match': match,
        'match_id': match_id,
    }

    return render(request, 'dashboard/match_live.html', context)


@club_admin_required
def player_list(request):
    """List all players with stats summary"""

    club = request.club
    players = Player.objects.filter(club=club).order_by('number', 'name')

    context = {
        'club': club,
        'players': players,
    }

    return render(request, 'dashboard/players.html', context)


@club_admin_required
def player_detail(request, player_id):
    """Player detail view - Stats over time, match history"""

    club = request.club
    player = get_object_or_404(Player, id=player_id, club=club)

    # Get all events for this player
    events = MatchEvent.objects.filter(player=player).order_by('-timestamp')[:50]

    # Get matches participated in
    from ..models import MatchParticipant

    participations = MatchParticipant.objects.filter(
        player=player
    ).select_related('match')

    context = {
        'club': club,
        'player': player,
        'events': events,
        'participations': participations,
    }

    return render(request, 'dashboard/player_detail.html', context)


@club_admin_required
def reports_index(request):
    """Reports index page - PDF/Excel generation options"""

    club = request.club

    # Get matches and players for select dropdowns
    matches = Match.objects.filter(club=club).order_by('-date')[:50]
    players = Player.objects.filter(club=club).order_by('number', 'name')

    context = {
        'club': club,
        'matches': matches,
        'players': players,
    }

    return render(request, 'dashboard/reports.html', context)


@club_admin_required
def report_match_pdf(request, match_id):
    """Generate PDF report for a specific match"""

    club = request.club
    match = get_object_or_404(Match, id=match_id, club=club)

    from ..reports.match_report import generate_match_report_pdf

    pdf_path = generate_match_report_pdf(match)

    with open(pdf_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="match_{match.id}_report.pdf"'
        return response


@club_admin_required
def report_match_excel(request, match_id):
    """Generate Excel report for a specific match"""

    club = request.club
    match = get_object_or_404(Match, id=match_id, club=club)

    from ..reports.match_report import generate_match_report_excel

    excel_path = generate_match_report_excel(match)

    with open(excel_path, 'rb') as f:
        response = HttpResponse(
            f.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="match_{match.id}_report.xlsx"'
        return response


@club_admin_required
def report_player_pdf(request, player_id):
    """Generate PDF report for a specific player"""

    club = request.club
    player = get_object_or_404(Player, id=player_id, club=club)

    from ..reports.player_report import generate_player_report_pdf

    pdf_path = generate_player_report_pdf(player)

    with open(pdf_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="player_{player.id}_report.pdf"'
        return response


@club_admin_required
def report_player_excel(request, player_id):
    """Generate Excel report for a specific player"""

    club = request.club
    player = get_object_or_404(Player, id=player_id, club=club)

    from ..reports.player_report import generate_player_report_excel

    excel_path = generate_player_report_excel(player)

    with open(excel_path, 'rb') as f:
        response = HttpResponse(
            f.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="player_{player.id}_report.xlsx"'
        return response


@club_admin_required
def report_season_excel(request):
    """Generate Excel report for entire season"""

    club = request.club

    from ..reports.season_report import generate_season_report_excel

    excel_path = generate_season_report_excel(club)

    with open(excel_path, 'rb') as f:
        response = HttpResponse(
            f.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="season_report.xlsx"'
        return response
