"""
WebSocket routing for Django Channels

Real-time match updates via WebSockets
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
import gaastats.consumers

websocket_urlpatterns = [
    path('ws/match/<int:match_id>/', gaastats.consumers.MatchConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
