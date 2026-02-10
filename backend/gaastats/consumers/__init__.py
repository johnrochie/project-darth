"""
WebSocket Consumers for Real-Time Match Updates
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class MatchConsumer(AsyncWebsocketConsumer):
    """
    Real-time match updates via WebSockets

    Connection: ws://api.gaastats.ie/ws/match/<match_id>/

    Events sent to client:
    - match_update: Generic match update
    - score_update: Score change
    - event_created: New match event created
    - player_subbed: Player substitution
    """

    async def connect(self):
        """Accept WebSocket connection for specific match"""

        # Get match_id from URL
        match_id = self.scope['url_route']['kwargs']['match_id']

        # Get user from scope (authenticated via AuthMiddlewareStack)
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Authentication required
            return

        # Verify user has access to this match (same club)
        try:
            match = await self.get_match(match_id)
            user_profile = await self.get_user_profile(user)

        except Exception:
            await self.close(code=4004)  # Not found
            return

        if match.club.id != user_profile.club.id:
            await self.close(code=4003)  # Forbidden
            return

        # Join match-specific WebSocket group
        self.match_group_name = f'match_{match_id}'
        await self.channel_layer.group_add(
            self.match_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()

    async def disconnect(self, close_code):
        """Leave match WebSocket group"""

        # Leave group
        if hasattr(self, 'match_group_name'):
            await self.channel_layer.group_discard(
                self.match_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Receive messages from client
        Client can send: ping, request_match_state
        """

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                # Respond with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))

            elif message_type == 'request_match_state':
                # Client requests current match state
                match_id = self.scope['url_route']['kwargs']['match_id']
                match_state = await self.get_match_state(match_id)
                await self.send(text_data=json.dumps({
                    'type': 'match_state',
                    'data': match_state
                }))

        except json.JSONDecodeError:
            # Invalid JSON - ignore
            pass

    async def match_update(self, event):
        """Send match update to client"""

        data = event['data']

        await self.send(text_data=json.dumps({
            'type': 'match_update',
            'data': data
        }))

    async def score_update(self, event):
        """Send score update to client"""

        data = event['data']

        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'data': data
        }))

    async def event_created(self, event):
        """Send new event notification to client"""

        data = event['data']

        await self.send(text_data=json.dumps({
            'type': 'event_created',
            'data': data
        }))

    async def player_subbed(self, event):
        """Send player substitution notification to client"""

        data = event['data']

        await self.send(text_data=json.dumps({
            'type': 'player_subbed',
            'data': data
        }))

    @database_sync_to_async
    def get_match(self, match_id):
        """Get match by ID"""
        from ..models import Match
        return Match.objects.get(id=match_id)

    @database_sync_to_async
    def get_user_profile(self, user):
        """Get user profile"""
        from ..models import UserProfile
        return UserProfile.objects.get(user=user)

    @database_sync_to_async
    def get_match_state(self, match_id):
        """Get current match state for client response"""
        from ..models import Match

        match = Match.objects.get(id=match_id)
        events = list(match.events.all().select_related('player').values(
            'id', 'event_type', 'minute', 'player__name', 'player__number'
        )[:50])  # Last 50 events

        participants = list(match.participants.filter(is_starting=True).select_related('player').values(
            'player__id', 'player__name', 'player__number', 'position'
        ))

        return {
            'match_id': match.id,
            'status': match.status,
            'score': {
                'club': {
                    'goals': match.club_goals,
                    'point_1': match.club_1point,
                    'point_2': match.club_2point,
                    'total': match.total_club_score
                },
                'opposition': {
                    'goals': match.opposition_goals,
                    'total': match.total_opposition_score
                }
            },
            'recent_events': events,
            'starting_lineup': participants
        }


# Helper function to broadcast events to match group
async def broadcast_to_match(match_id, event_type, data):
    """
    Broadcast event to all WebSocket clients for a match

    Usage:
        await broadcast_to_match(match_id, 'score_update', {
            'goals': 3,
            'points': 12
        })
    """

    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()

    await channel_layer.group_send(
        f'match_{match_id}',
        {
            'type': event_type,
            'data': data
        }
    )
