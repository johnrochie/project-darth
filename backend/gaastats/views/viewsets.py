"""
REST Framework ViewSets for GAA Stats App
9 API endpoints for multi-tenant club management
"""

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.contrib.auth import get_user_model
from django.db.models import Q, F, Sum, Count, Avg, Max, Min, Prefetch
from django.shortcuts import get_object_or_404

from ..models import (
    Club, UserProfile, Player, Match, MatchParticipant,
    MatchEvent, MatchScoreUpdate, OAuthToken
)
from ..serializers import (
    ClubSerializer, UserProfileSerializer, PlayerSerializer,
    MatchSerializer, MatchParticipantSerializer, MatchEventSerializer,
    MatchScoreUpdateSerializer, OAuthTokenSerializer, StatsSerializer
)

User = get_user_model()


class ClubViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Club CRUD operations
    Dev-only access to view/create/modify clubs
    """
    queryset = Club.objects.all().order_by('name')
    serializer_class = ClubSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]  # Only dev/admin users

    def get_permissions(self):
        """Allow authenticated users to list clubs (read-only), but dev only to modify"""
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    @action(detail=False, methods=['get'])
    def my_club(self, request):
        """Get current user's club subdomain and name"""
        if not hasattr(request.user, 'userprofile'):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

        club = request.user.userprofile.club
        serializer = ClubSerializer(club)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for UserProfile management
    Users can view their own profile
    """
    queryset = UserProfile.objects.select_related('user', 'club').all()
    serializer_class = UserProfileSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Users can only see profiles from their own club"""
        if not hasattr(self.request.user, 'userprofile'):
            return UserProfile.objects.none()
        
        user_club = self.request.user.userprofile.club
        return UserProfile.objects.filter(club=user_club)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        try:
            profile = request.user.userprofile
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)


class PlayerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Player CRUD operations
    Admin users can modify, viewers can only read
    """
    queryset = Player.objects.select_related('club').all()
    serializer_class = PlayerSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter players by user's club"""
        if not hasattr(self.request.user, 'userprofile'):
            return Player.objects.none()
        
        user_club = self.request.user.userprofile.club
        return Player.objects.filter(club=user_club).order_by('name')

    def perform_create(self, serializer):
        """Automatically add club from user profile"""
        serializer.save(club=self.request.user.userprofile.club)

    def perform_update(self, serializer):
        """Only admins can update player details"""
        if self.request.user.userprofile.role == 'viewer':
            return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Only admins can delete players"""
        if request.user.userprofile.role == 'viewer':
            return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available players for team selection (no injuries)"""
        if not hasattr(request.user, 'userprofile'):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

        user_club = request.user.userprofile.club
        available = Player.objects.filter(
            club=user_club,
            is_available=True,
            injury_status='healthy'
        ).order_by('name')
        serializer = PlayerSerializer(available, many=True)
        return Response(serializer.data)


class MatchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Match CRUD operations
    Admins can create/modify matches, viewers can read only
    """
    queryset = Match.objects.select_related('club', 'opponent').prefetch_related(
        'participants__player'
    ).all()
    serializer_class = MatchSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter matches by user's club"""
        if not hasattr(self.request.user, 'userprofile'):
            return Match.objects.none()
        
        user_club = self.request.user.userprofile.club
        queryset = Match.objects.filter(club=user_club)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Order by date descending
        return queryset.order_by('-date', '-time')

    def perform_create(self, serializer):
        """Automatically add club from user profile"""
        serializer.save(club=self.request.user.userprofile.club)

    def perform_update(self, serializer):
        """Only admins can update match details"""
        if self.request.user.userprofile.role == 'viewer':
            return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Only admins can delete matches"""
        if request.user.userprofile.role == 'viewer':
            return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def start_match(self, request, pk=None):
        """Mark match as in progress"""
        match = self.get_object()
        match.status = 'in_progress'
        match.save()
        
        # Broadcast WebSocket event for match start
        # (Handled by MatchConsumer)
        
        serializer = MatchSerializer(match)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_match(self, request, pk=None):
        """Mark match as completed"""
        match = self.get_object()
        match.status = 'completed'
        match.save()
        
        # Broadcast WebSocket event for match completion
        # (Handled by MatchConsumer)
        
        serializer = MatchSerializer(match)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent 10 matches"""
        if not hasattr(request.user, 'userprofile'):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

        user_club = request.user.userprofile.club
        recent = Match.objects.filter(club=user_club).order_by('-date', '-time')[:10]
        serializer = MatchSerializer(recent, many=True)
        return Response(serializer.data)


class MatchParticipantViewSet(viewsets.ModelViewSet):
    """
    API endpoint for team lineup management
    Admins can add/remove players from match
    """
    queryset = MatchParticipant.objects.select_related('match', 'player').all()
    serializer_class = MatchParticipantSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter participants by user's club matches"""
        if not hasattr(self.request.user, 'userprofile'):
            return MatchParticipant.objects.none()
        
        user_club = self.request.user.userprofile.club
        return MatchParticipant.objects.filter(match__club=user_club)

    def perform_create(self, serializer):
        """Validate player belongs to same club as match"""
        match = serializer.validated_data['match']
        player = serializer.validated_data['player']
        
        if player.club != match.club:
            raise serializers.ValidationError(
                {'error': 'Player must belong to the same club as the match'}
            )
        
        serializer.save()

    def perform_destroy(self, instance):
        """Only admins can remove players from lineup"""
        if self.request.user.userprofile.role == 'viewer':
            raise serializers.ValidationError({'error': 'Insufficient permissions'})
        instance.delete()


class MatchEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint for stats entry (score, shots, tackles, turnovers, etc.)
    Supports undo functionality to correct errors
    Triggers auto-tweet on score events (if enabled)
    """
    queryset = MatchEvent.objects.select_related('match', 'player').prefetch_related(
        'corrected_event'
    ).all()
    serializer_class = MatchEventSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter events by user's club matches"""
        if not hasattr(self.request.user, 'userprofile'):
            return MatchEvent.objects.none()
        
        user_club = self.request.user.userprofile.club
        
        # Filter by match_id if provided
        match_id = self.request.query_params.get('match_id')
        if match_id:
            return MatchEvent.objects.filter(match__club=user_club, match_id=match_id).order_by('minute')
        
        return MatchEvent.objects.filter(match__club=user_club).order_by('-timestamp')

    def perform_create(self, serializer):
        """Record stat event with player ownership check and auto-tweet"""
        match = serializer.validated_data['match']
        player = serializer.validated_data.get('player')
        
        # Validate player belongs to match's club (home club only)
        if player and player.club != match.club:
            raise serializers.ValidationError(
                {'error': 'Player must belong to the home club (not opposition)'}
            )
        
        # Validate match is in progress
        if match.status != 'in_progress':
            raise serializers.ValidationError(
                {'error': 'Can only record events for in-progress matches'}
            )
        
        # Save the event
        event = serializer.save()
        
        # Auto-tweet score events (if enabled)
        from django.conf import settings
        if getattr(settings, 'X_AUTO_TWEET_ENABLED', False) and event.event_type in [
            'score_goal', 'score_1point', 'score_2point'
        ]:
            try:
                from ..social_media.x_service import XService
                x_service = XService(event.match.club)
                x_service.post_score_update(event.match, event)
            except Exception as e:
                # Log error but don't fail the event creation
                print(f"Auto-tweet failed: {e}")
        
        # Broadcast WebSocket event for live updates
        # (Handled by MatchConsumer)
        
        return event

    @action(detail=True, methods=['post'])
    def undo(self, request, pk=None):
        """
        Correct/undo an event by marking it as corrected
        Creates a corrected event with same data but 'corrected' flag
        """
        original_event = self.get_object()
        
        # Validate event hasn't been undone already
        if original_event.corrected_event:
            return Response(
                {'error': 'Event has already been undone'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create corrected event
        corrected_event = MatchEvent.objects.create(
            match=original_event.match,
            player=original_event.player,
            event_type=original_event.event_type,
            minute=original_event.minute,
            corrected_event=original_event,
            data=original_event.data
        )
        
        # Link original event to corrected event
        original_event.corrected_event = corrected_event
        original_event.save()
        
        # Broadcast WebSocket event for undo
        # (Handled by MatchConsumer)
        
        serializer = MatchEventSerializer(corrected_event)
        return Response(serializer.data)


class MatchScoreUpdateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for social media (X/Twitter) score update tracking
    """
    queryset = MatchScoreUpdate.objects.select_related('match').all()
    serializer_class = MatchScoreUpdateSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter score updates by user's club matches"""
        if not hasattr(self.request.user, 'userprofile'):
            return MatchScoreUpdate.objects.none()
        
        user_club = self.request.user.userprofile.club
        return MatchScoreUpdate.objects.filter(match__club=user_club).order_by('-timestamp')


class StatsViewSet(viewsets.ViewSet):
    """
    API endpoint for stats aggregation (player and match summaries)
    Computed stats from events and matches
    """
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Health check endpoint"""
        return Response({'status': 'stats endpoint available'})

    @action(detail=False, methods=['get'])
    def player_summary(self, request):
        """
        Get player stats (goals, points, shots, tackles, etc.)
        Query params: player_id (required), match_id (optional)
        """
        player_id = request.query_params.get('player_id')
        match_id = request.query_params.get('match_id')
        
        if not player_id:
            return Response(
                {'error': 'player_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate player belongs to user's club
        if not hasattr(request.user, 'userprofile'):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user_club = request.user.userprofile.club
        try:
            player = Player.objects.get(id=player_id, club=user_club)
        except Player.DoesNotExist:
            return Response(
                {'error': 'Player not found in your club'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filter events by player
        events = MatchEvent.objects.filter(player=player)
        
        # Filter by match if specified
        if match_id:
            events = events.filter(match_id=match_id)
        
        # Calculate stats
        goals = events.filter(event_type='score_goal').count()
        point_1 = events.filter(event_type='score_1point').count()
        point_2 = events.filter(event_type='score_2point').count()
        shots_on_target = events.filter(event_type='shot_on_target').count()
        shots_wide = events.filter(event_type='shot_wide').count()
        shots_saved = events.filter(event_type='shot_saved').count()
        tackles_won = events.filter(event_type='tackle_won').count()
        tackles_lost = events.filter(event_type='tackle_lost').count()
        blocks = events.filter(event_type='block').count()
        turnovers_lost = events.filter(event_type='turnover_lost').count()
        turnovers_won = events.filter(event_type='turnover_won').count()

        total_score = (goals * 3) + point_1 + (point_2 * 2)
        total_shots = shots_on_target + shots_wide + shots_saved
        tackle_success_rate = (tackles_won / (tackles_won + tackles_lost) * 100) if (tackles_won + tackles_lost) > 0 else 0
        
        return Response({
            'player_id': player.id,
            'player_name': player.name,
            'player_number': player.number,
            'match_id': match_id,
            'stats': {
                'goals': goals,
                'point_1': point_1,
                'point_2': point_2,
                'total_score': total_score,
                'shots': {
                    'on_target': shots_on_target,
                    'wide': shots_wide,
                    'saved': shots_saved,
                    'total': total_shots
                },
                'tackles': {
                    'won': tackles_won,
                    'lost': tackles_lost,
                    'success_rate': round(tackle_success_rate, 2)
                },
                'blocks': blocks,
                'turnovers': {
                    'lost': turnovers_lost,
                    'won': turnovers_won
                }
            }
        })

    @action(detail=False, methods=['get'])
    def match_summary(self, request):
        """
        Get match-level stats
        Query params: match_id (required)
        """
        match_id = request.query_params.get('match_id')
        
        if not match_id:
            return Response(
                {'error': 'match_id query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate match belongs to user's club
        if not hasattr(request.user, 'userprofile'):
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        user_club = request.user.userprofile.club
        try:
            match = Match.objects.get(id=match_id, club=user_club)
        except Match.DoesNotExist:
            return Response(
                {'error': 'Match not found in your club'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get match events
        events = MatchEvent.objects.filter(match=match)
        home_events = events.filter(player__club=match.club)
        
        # Calculate club stats
        goals = home_events.filter(event_type='score_goal').count()
        point_1 = home_events.filter(event_type='score_1point').count()
        point_2 = home_events.filter(event_type='score_2point').count()
        club_score = (goals * 3) + point_1 + (point_2 * 2)
        
        # Player participation
        participants = MatchParticipant.objects.filter(match=match)
        players_used = participants.values('player').distinct().count()
        
        # Kick-out stats
        kickouts_won = home_events.filter(event_type='kickout_won').count()
        kickouts_lost = home_events.filter(event_type='kickout_lost').count()
        
        return Response({
            'match_id': match.id,
            'team': match.club.name,
            'opposition': match.opposition.name,
            'score': {
                'goals': goals,
                'point_1': point_1,
                'point_2': point_2,
                'total': club_score
            },
            'opposition_score': match.opposition_score,
            'players_used': players_used,
            'kickouts': {
                'won': kickouts_won,
                'lost': kickouts_lost,
                'total': kickouts_won + kickouts_lost
            },
            'status': match.status,
            'date': match.date,
            'venue': match.venue
        })


class OAuthTokenViewSet(viewsets.ModelViewSet):
    """
    API endpoint for OAuth token management (X/Twitter)
    Admin-only access to store/oauth tokens for social media integration
    """
    queryset = OAuthToken.objects.select_related('club').all()
    serializer_class = OAuthTokenSerializer
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter OAuth tokens by user's club"""
        if not hasattr(self.request.user, 'userprofile'):
            return OAuthToken.objects.none()
        
        user_club = self.request.user.userprofile.club
        return OAuthToken.objects.filter(club=user_club)

    def perform_create(self, serializer):
        """Validate admin permissions before storing token"""
        if self.request.user.userprofile.role != 'admin':
            raise serializers.ValidationError({'error': 'Only admin users can store OAuth tokens'})
        serializer.save(club=self.request.user.userprofile.club)

    def perform_update(self, serializer):
        """Only admins can update OAuth tokens"""
        if self.request.user.userprofile.role != 'admin':
            raise serializers.ValidationError({'error': 'Only admin users can update OAuth tokens'})
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Only admins can delete OAuth tokens"""
        if request.user.userprofile.role != 'admin':
            return Response({'error': 'Only admin users can delete OAuth tokens'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


# GenerateAuthToken endpoint for iPad app token generation
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token


class GenerateAuthToken(APIView):
    """Generate auth token for iPad app"""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate or return existing auth token for current user"""
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({'token': token.key})
