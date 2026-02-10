"""
Django Admin Configuration for GAA Stats App Models
"""

from django.contrib import admin
from .models import (
    Club, UserProfile, Player, Match,
    MatchParticipant, MatchEvent, MatchScoreUpdate, OAuthToken
)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    """Club admin interface"""

    list_display = ['name', 'subdomain', 'status', 'twitter_handle', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'subdomain', 'twitter_handle']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Club Information', {
            'fields': ('name', 'subdomain', 'status')
        }),
        ('Branding', {
            'fields': ('logo_url', 'colors', 'twitter_handle')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin interface"""

    list_display = ['user', 'club', 'role']
    list_filter = ['role', 'club']
    search_fields = ['user__email', 'user__username', 'club__name']


class MatchParticipantInline(admin.TabularInline):
    """Inline for managing match participants from Match admin"""

    model = MatchParticipant
    extra = 15  # Number of empty rows
    fields = ['player', 'position', 'is_starting', 'minute_on', 'minute_off']


class MatchEventInline(admin.TabularInline):
    """Inline for viewing events from Match admin (readonly)"""

    model = MatchEvent
    extra = 0
    can_delete = False
    readonly_fields = ['player', 'minute', 'event_type', 'timestamp', 'data']

    def has_add_permission(self, request, obj=None):
        return False


class MatchScoreUpdateInline(admin.TabularInline):
    """Inline for viewing score updates from Match admin"""

    model = MatchScoreUpdate
    extra = 0
    can_delete = False
    readonly_fields = ['timestamp', 'score_text', 'social_media_posted', 'x_post_id']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    """Match admin interface with inline participants"""

    list_display = [
        'club', 'date', 'opposition', 'status', 'total_club_score',
        'total_opposition_score', 'entry_mode'
    ]
    list_filter = ['status', 'entry_mode', 'date', 'competition']
    list_select_related = ['club']
    search_fields = ['opposition', 'venue', 'club__name']
    readonly_fields = ['total_club_score', 'total_opposition_score', 'created_at', 'updated_at']

    inlines = [MatchParticipantInline, MatchEventInline, MatchScoreUpdateInline]

    fieldsets = (
        ('Match Details', {
            'fields': ('club', 'date', 'time', 'opposition', 'venue', 'weather', 'referee', 'competition')
        }),
        ('Configuration', {
            'fields': ('entry_mode', 'status')
        }),
        ('Score (Club)', {
            'fields': ('club_goals', 'club_1point', 'club_2point')
        }),
        ('Score (Opposition)', {
            'fields': ('opposition_goals',)
        }),
        ('Calculated', {
            'fields': ('total_club_score', 'total_opposition_score'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('club')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Player admin interface"""

    list_display = ['name', 'number', 'club', 'position', 'injury_status', 'is_available']
    list_filter = ['position', 'injury_status', 'is_available', 'club']
    search_fields = ['name', 'club__name']
    list_select_related = ['club']

    fieldsets = (
        ('Player Information', {
            'fields': ('club', 'name', 'number', 'position')
        }),
        ('Status', {
            'fields': ('injury_status', 'is_available')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('club')


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    """Match event admin interface"""

    list_display = ['match', 'player', 'event_type', 'minute', 'timestamp']
    list_filter = ['event_type', 'match__status']
    search_fields = ['player__name', 'match__opposition']
    list_select_related = ['match', 'player']
    readonly_fields = ['timestamp', 'created_at']

    fieldsets = (
        ('Event Details', {
            'fields': ('match', 'player', 'event_type', 'minute', 'timestamp')
        }),
        ('Event Data (JSON)', {
            'fields': ('data',)
        }),
        ('Correction', {
            'fields': ('corrected_event',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('match', 'player')


@admin.register(MatchParticipant)
class MatchParticipantAdmin(admin.ModelAdmin):
    """Match participant admin interface"""

    list_display = ['match', 'player', 'position', 'is_starting', 'minute_on', 'minute_off']
    list_filter = ['is_starting', 'match__status']
    list_select_related = ['match', 'player']
    search_fields = ['player__name', 'match__opposition']

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('match', 'player')


@admin.register(MatchScoreUpdate)
class MatchScoreUpdateAdmin(admin.ModelAdmin):
    """Match score update admin interface (for social media tracking)"""

    list_display = ['match', 'timestamp', 'score_text', 'social_media_posted', 'x_post_id']
    list_filter = ['social_media_posted', 'match__status']
    list_select_related = ['_match']
    readonly_fields = ['timestamp', 'created_at']

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('match')


@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    """OAuth token admin interface"""

    list_display = ['club', 'provider', 'created_at', 'updated_at']
    list_filter = ['provider']
    readonly_fields = ['created_at', 'updated_at']
