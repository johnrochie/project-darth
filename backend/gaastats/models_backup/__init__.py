"""
GAA Stats App Models

Multi-tenant data models with club_id foreign key on all tables
"""

from django.db import models
from django.conf import settings


# User model extension for multi-tenant auth
class Club(models.Model):
    """GAA Club - one per subdomain (e.g., clubname.gaastats.ie)"""

    CLUB_STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
    ]

    name = models.CharField(max_length=255, help_text="Club name (e.g., Austin Stacks)")
    subdomain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Subdomain (e.g., austinstacks.gaastats.ie)"
    )
    logo_url = models.URLField(blank=True, null=True, help_text="Club logo URL")
    colors = models.JSONField(
        default=dict,
        help_text="Club colors (primary, secondary, accent)"
    )
    status = models.CharField(
        max_length=20,
        choices=CLUB_STATUS_CHOICES,
        default='active'
    )
    twitter_handle = models.CharField(
        max_length=100,
        blank=True,
        help_text="Club Twitter/X handle (without @)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'club'
        ordering = ['name']
        verbose_name = 'Club'
        verbose_name_plural = 'Clubs'

    def __str__(self):
        return f"{self.name} ({self.subdomain})"


class UserProfile(models.Model):
    """Extended user profile with club membership and role"""

    ROLE_CHOICES = [
        ('admin', 'Club Admin'),
        ('viewer', 'Viewer'),
        ('dev', 'Developer'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gaastats_profile'
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='users'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        db_table = 'user_profile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.email} ({self.get_role_display()}) - {self.club.name}"


class Player(models.Model):
    """GAA Player (up to 40 per club)"""

    POSITION_CHOICES = [
        ('goalkeeper', 'Goalkeeper'),
        ('fullback', 'Full Back'),
        ('fullback_center', 'Full Back Center'),
        ('halfback', 'Half Back'),
        ('centerback', 'Center Back'),
        ('midfield', 'Midfielder'),
        ('halfforward', 'Half Forward'),
        ('centerforward', 'Center Forward'),
        ('fullforward', 'Full Forward'),
        ('fullforward_center', 'Full Forward Center'),
    ]

    INJURY_STATUS_CHOICES = [
        ('fit', 'Fit'),
        ('injured', 'Injured'),
        ('doubtful', 'Doubtful'),
        ('suspended', 'Suspended'),
    ]

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='players'
    )
    name = models.CharField(max_length=255)
    number = models.PositiveIntegerField(null=True, blank=True, help_text="Jersey number")
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, blank=True)
    injury_status = models.CharField(
        max_length=20,
        choices=INJURY_STATUS_CHOICES,
        default='fit'
    )
    is_available = models.BooleanField(default=True, help_text="Available for selection")
    notes = models.TextField(blank=True, help_text="Additional player info")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player'
        ordering = ['number', 'name']
        unique_together = [['club', 'number'], ['club', 'name']]
        verbose_name = 'Player'
        verbose_name_plural = 'Players'

    def __str__(self):
        number_str = f"#{self.number}" if self.number else "No #"
        return f"{self.name} {number_str} ({self.club.name})"


class Match(models.Model):
    """GAA Match (club vs opposition)"""

    ENTRY_MODE_CHOICES = [
        ('live', 'Live (pitch-side)'),
        ('post_match', 'Post-Match (video analysis)'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('postponed', 'Postponed'),
        ('cancelled', 'Cancelled'),
    ]

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    date = models.DateField(help_text="Match date")
    time = models.TimeField(null=True, blank=True, help_text="Match time")
    opposition = models.CharField(max_length=255)
    venue = models.CharField(max_length=255, blank=True, help_text="Venue (e.g., Austin Stacks Park)")
    weather = models.CharField(max_length=100, blank=True, help_text="Weather conditions")
    referee = models.CharField(max_length=255, blank=True)
    competition = models.CharField(max_length=255, blank=True, help_text="Competition name")
    entry_mode = models.CharField(
        max_length=20,
        choices=ENTRY_MODE_CHOICES,
        default='live'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    # Score tracking
    club_score = models.PositiveIntegerField(default=0, help_text="Club score (points)")
    club_goals = models.PositiveIntegerField(default=0, help_text="Club goals")
    club_1point = models.PositiveIntegerField(default=0, help_text="Club 1-point scores")
    club_2point = models.PositiveIntegerField(default=0, help_text="Club 2-point scores (40m+)")

    opposition_score = models.PositiveIntegerField(default=0, help_text="Opposition score (points)")
    opposition_goals = models.PositiveIntegerField(default=0, help_text="Opposition goals")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'match'
        ordering = ['-date', '-created_at']
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'

    def __str__(self):
        return f"{self.club.name} vs {self.opposition} ({self.date})"

    @property
    def total_club_score(self):
        """Calculate total club score (goals × 3 + 1-point + 2-point)"""
        return (self.club_goals * 3) + self.club_1point + self.club_2point

    @property
    def total_opposition_score(self):
        """Calculate total opposition score"""
        return self.opposition_goals * 3


class MatchParticipant(models.Model):
    """Players selected for a match (15 from 40)"""

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='match_participations'
    )
    position = models.CharField(max_length=50, blank=True)
    is_starting = models.BooleanField(default=True, help_text="Started the match")
    minute_on = models.PositiveIntegerField(null=True, blank=True, help_text="Minute entered")
    minute_off = models.PositiveIntegerField(null=True, blank=True, help_text="Minute exited")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'match_participant'
        ordering = ['is_starting', 'minute_on']
        unique_together = [['match', 'player']]
        verbose_name = 'Match Participant'
        verbose_name_plural = 'Match Participants'

    def __str__(self):
        status = "Started" if self.is_starting else f"Sub {self.minute_on}'"
        return f"{self.player.name} - {status}"


class MatchEvent(models.Model):
    """Individual statistical events (scores, tackles, turnovers, etc.)"""

    EVENT_TYPE_CHOICES = [
        # Scores
        ('score_goal', 'Goal Scored'),
        ('score_1point', '1-Point Scored'),
        ('score_2point', '2-Point Scored (40m+)'),

        # Shots
        ('shot_on_target', 'Shot on Target'),
        ('shot_wide', 'Shot Wide'),
        ('shot_saved', 'Shot Saved'),

        # Defensive
        ('tackle_won', 'Tackle Won'),
        ('tackle_lost', 'Tackle Lost'),
        ('block', 'Block'),

        # Possession
        ('turnover_lost', 'Turnover Lost'),
        ('turnover_won', 'Turnover Won Back'),

        # Kick-outs
        ('kickout_won', 'Kick-out Won'),
        ('kickout_lost', 'Kick-out Lost'),

        # Other
        ('substitution', 'Substitution'),
        ('injury', 'Injury'),
        ('foul_committed', 'Foul Committed'),
        ('foul_conceded', 'Foul Conceded'),
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='events'
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True,  # Some events may not be tied to a player (e.g., kick-out)
        related_name='events'
    )
    timestamp = models.DateTimeField()
    minute = models.PositiveIntegerField(help_text="Match minute (0-70)")
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)

    # Additional data (stored as JSON for flexibility)
    data = models.JSONField(
        default=dict,
        help_text="Event-specific data (angle, distance, outcome, assist_player_id, etc.)"
    )

    # Optional - for tracking duplicates or corrections
    corrected_event = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrections',
        help_text="If set, this event was corrected by another"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'match_event'
        ordering = ['timestamp', 'minute']
        indexes = [
            models.Index(fields=['match', 'minute']),
            models.Index(fields=['match', 'event_type']),
            models.Index(fields=['player', 'match']),
        ]
        verbose_name = 'Match Event'
        verbose_name_plural = 'Match Events'

    def __str__(self):
        player_str = f"{self.player.name}" if self.player else "Team"
        return f"{player_str} - {self.get_event_type_display()} at {self.minute}'"


class MatchScoreUpdate(models.Model):
    """Social media (X/Twitter) score update history"""

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
        related_name='score_updates'
    )
    timestamp = models.DateTimeField()
    score_text = models.CharField(max_length=280, help_text="Tweet content")
    social_media_posted = models.BooleanField(default=False, help_text="Successfully posted to X")
    x_post_id = models.CharField(max_length=255, blank=True, null=True, help_text="X post ID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'match_score_update'
        ordering = ['-timestamp']
        verbose_name = 'Match Score Update'
        verbose_name_plural = 'Match Score Updates'

    def __str__(self):
        status = "✓" if self.social_media_posted else "✗"
        return f"{status} {self.score_text}"


class OAuthToken(models.Model):
    """Store OAuth tokens for X/Twitter integration"""

    PROVIDER_CHOICES = [
        ('twitter', 'Twitter / X'),
    ]

    club = models.OneToOneField(
        Club,
        on_delete=models.CASCADE,
        related_name='oauth_token'
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='twitter')
    oauth_token = models.TextField(help_text="OAuth access token")
    oauth_token_secret = models.TextField(blank=True, null=True, help_text="OAuth token secret (OAuth 1.0a)")
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'oauth_tokens'
        verbose_name = 'OAuth Token'
        verbose_name_plural = 'OAuth Tokens'

    def __str__(self):
        return f"{self.club.name} {self.get_provider_display()} token"


# Signal to create UserProfile when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile for new users
    Note: Email will be required to contain club subdomain or club selection screen will be needed
    """
    if created:
        # For now, don't auto-create - club selection required
        pass
