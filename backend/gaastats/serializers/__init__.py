"""
Django REST Framework Serializers for GAA Stats App
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ClubSerializer(serializers.ModelSerializer):
    """Club serializer"""

    class Meta:
        from ..models import Club
        model = Club
        fields = [
            'id', 'name', 'subdomain', 'logo_url', 'colors',
            'status', 'twitter_handle',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""

    class Meta:
        from ..models import UserProfile
        model = UserProfile
        fields = ['id', 'user', 'club', 'role']

    def to_representation(self, instance):
        """Include user details"""
        data = super().to_representation(instance)
        data['username'] = instance.user.username
        data['email'] = instance.user.email
        return data


class PlayerSerializer(serializers.ModelSerializer):
    """Player serializer"""

    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        from ..models import Player
        model = Player
        fields = [
            'id', 'club', 'name', 'number', 'position',
            'injury_status', 'is_available', 'notes',
            'club_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PlayerListSerializer(serializers.ModelSerializer):
    """Lightweight player serializer for list views"""

    class Meta:
        from ..models import Player
        model = Player
        fields = ['id', 'name', 'number', 'position', 'injury_status', 'is_available']


class MatchParticipantSerializer(serializers.ModelSerializer):
    """Match participant serializer"""

    player_name = serializers.CharField(source='player.name', read_only=True)
    player_number = serializers.IntegerField(source='player.number', read_only=True)

    class Meta:
        from ..models import MatchParticipant
        model = MatchParticipant
        fields = [
            'id', 'match', 'player', 'player_name', 'player_number',
            'position', 'is_starting', 'minute_on', 'minute_off'
        ]


class MatchEventSerializer(serializers.ModelSerializer):
    """Match event serializer"""

    player_name = serializers.CharField(source='player.name', read_only=True, allow_null=True)

    class Meta:
        from ..models import MatchEvent
        model = MatchEvent
        fields = [
            'id', 'match', 'player', 'player_name', 'timestamp',
            'minute', 'event_type', 'data', 'corrected_event', 'created_at'
        ]
        read_only_fields = ['created_at']

    def validate(self, data):
        """Validate match event data"""
        event_type = data.get('event_type')

        # Certain events require a player
        player_required_events = [
            'score_goal', 'score_1point', 'score_2point',
            'shot_on_target', 'shot_wide', 'shot_saved',
            'tackle_won', 'tackle_lost', 'block',
            'turnover_lost', 'turnover_won',
            'injury', 'foul_committed', 'foul_conceded'
        ]

        if event_type in player_required_events and not data.get('player'):
            raise serializers.ValidationError({
                'player': f"{event_type} events must be associated with a player"
            })

        return data


class MatchScoreUpdateSerializer(serializers.ModelSerializer):
    """Match score update serializer"""

    class Meta:
        from ..models import MatchScoreUpdate
        model = MatchScoreUpdate
        fields = [
            'id', 'match', 'timestamp', 'score_text',
            'social_media_posted', 'x_post_id', 'created_at'
        ]
        read_only_fields = ['created_at', 'social_media_posted', 'x_post_id']


class MatchSerializer(serializers.ModelSerializer):
    """Match serializer"""

    club_name = serializers.CharField(source='club.name', read_only=True)
    total_club_score = serializers.ReadOnlyField()
    total_opposition_score = serializers.ReadOnlyField()
    event_count = serializers.SerializerMethodField()
    participants = MatchParticipantSerializer(many=True, read_only=True)

    class Meta:
        from ..models import Match
        model = Match
        fields = [
            'id', 'club', 'club_name', 'date', 'time', 'opposition',
            'venue', 'weather', 'referee', 'competition',
            'entry_mode', 'status',
            'club_goals', 'club_1point', 'club_2point', 'club_score',
            'opposition_goals', 'opposition_score',
            'total_club_score', 'total_opposition_score',
            'event_count', 'participants',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_club_score', 'total_opposition_score']

    def get_event_count(self, obj):
        """Get number of events for this match"""
        return obj.events.count()


class MatchListSerializer(serializers.ModelSerializer):
    """Lightweight match serializer for list views"""

    class Meta:
        from ..models import Match
        model = Match
        fields = [
            'id', 'date', 'opposition', 'status',
            'club_goals', 'club_1point', 'club_2point',
            'opposition_goals', 'total_club_score', 'total_opposition_score'
        ]


class OAuthTokenSerializer(serializers.ModelSerializer):
    """OAuth token serializer"""

    class Meta:
        from ..models import OAuthToken
        model = OAuthToken
        fields = [
            'id', 'club', 'provider', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'oauth_token': {'write_only': True},
            'oauth_token_secret': {'write_only': True},
        }


# Stats serializers for analytics
class PlayerStatsSerializer(serializers.Serializer):
    """Player statistics aggregator"""

    player_id = serializers.IntegerField()
    player_name = serializers.CharField()
    goals = serializers.IntegerField(default=0)
    _1point = serializers.IntegerField(default=0, source='point_1')
    _2point = serializers.IntegerField(default=0, source='point_2')
    shots_taken = serializers.IntegerField(default=0)
    shots_on_target = serializers.IntegerField(default=0)
    tackles_won = serializers.IntegerField(default=0)
    turnovers_lost = serializers.IntegerField(default=0)
    matches_played = serializers.IntegerField()


class MatchStatsSerializer(serializers.Serializer):
    """Match statistics aggregator"""

    goals = serializers.IntegerField(default=0)
    _1point = serializers.IntegerField(default=0, source='point_1')
    _2point = serializers.IntegerField(default=0, source='point_2')
    shots_taken = serializers.IntegerField(default=0)
    shots_on_target = serializers.IntegerField(default=0)
    tackles_won = serializers.IntegerField(default=0)
    turnovers_lost = serializers.IntegerField(default=0)
    kickouts_won = serializers.IntegerField(default=0)
    kickouts_lost = serializers.IntegerField(default=0)
