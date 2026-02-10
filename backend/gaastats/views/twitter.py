"""
X (Twitter) OAuth API Views
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from ..models import OAuthToken, Club
from ..social_media.x_service import XService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def twitter_oauth_request(request):
    """
    Initiate X/Twitter OAuth flow

    Request body:
    {
        "callback_url": "https://clubname.gaastats.ie/auth/twitter/callback/"
    }

    Returns:
    {
        "auth_url": "https://api.twitter.com/oauth/authorize?oauth_token=...",
        "request_token": "..."
    }
    """

    user_profile = request.user.gaastats_profile
    club = user_profile.club

    callback_url = request.data.get('callback_url')

    if not callback_url:
        return Response(
            {'error': 'callback_url is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        auth_url, request_token, request_token_secret = XService.get_oauth_url(
            club_id=club.id,
            callback_url=callback_url
        )

        return Response({
            'success': True,
            'auth_url': auth_url,
            'request_token': request_token,
            # Store request token secret temporarily (could use Redis in production)
            'request_token_secret': request_token_secret,
        })

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def twitter_oauth_callback(request):
    """
    Handle X/Twitter OAuth callback

    Request body:
    {
        "oauth_token": "request_token",
        "oauth_token_secret": "request_token_secret",
        "oauth_verifier": "..."
    }

    Exchanges request token for access token and stores it
    """

    user_profile = request.user.gaastats_profile
    club = user_profile.club

    # Verify user is admin
    if user_profile.role != 'admin':
        return Response(
            {'error': 'Only admins can connect X accounts'},
            status=status.HTTP_403_FORBIDDEN
        )

    request_token = request.data.get('oauth_token')
    request_token_secret = request.data.get('oauth_token_secret')
    oauth_verifier = request.data.get('oauth_verifier')

    if not all([request_token, request_token_secret, oauth_verifier]):
        return Response(
            {'error': 'Missing OAuth parameters'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Exchange request token for access token
        access_token, access_token_secret = XService.exchange_request_token(
            request_token=request_token,
            request_token_secret=request_token_secret,
            oauth_verifier=oauth_verifier
        )

        # Store access tokens
        oauth_token, created = OAuthToken.objects.update_or_create(
            club=club,
            provider='twitter',
            defaults={
                'oauth_token': access_token,
                'oauth_token_secret': access_token_secret,
                'expires_at': None  # Twitter OAuth 1.0a tokens don't expire automatically
            }
        )

        return Response({
            'success': True,
            'message': 'X account connected successfully'
        })

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def twitter_post_tweet(request):
    """
    Post a custom tweet/quote

    Request body:
    {
        "content": "Tweet content (max 280 characters)"
    }

    Returns:
    {
        "success": true,
        "tweet_id": "1234567890"
    }
    """

    user_profile = request.user.gaastats_profile

    # Verify user is admin
    if user_profile.role not in ['admin', 'dev']:
        return Response(
            {'error': 'Only admins can post tweets'},
            status=status.HTTP_403_FORBIDDEN
        )

    content = request.data.get('content')

    if not content:
        return Response(
            {'error': 'content is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        # Initialize X service
        x_service = XService(club=user_profile.club)

        # Post tweet
        tweet_id, success = x_service.post_tweet(content)

        if not success:
            return Response(
                {'error': 'Failed to post tweet'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'success': True,
            'tweet_id': tweet_id
        })

    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def twitter_status(request):
    """
    Get X/Twitter connection status

    Returns:
    {
        "connected": true,
        "twitter_handle": "@clubname"
    }
    """

    user_profile = request.user.gaastats_profile

    try:
        oauth_token = OAuthToken.objects.get(
            club=user_profile.club,
            provider='twitter'
        )

        # Initialize X service to verify credentials
        x_service = XService(club=user_profile.club)

        # Try to verify credentials
        try:
            api = x_service._get_client()
            user = api.verify_credentials()
            twitter_handle = user.screen_name
            connected = True
        except:
            connected = False
            twitter_handle = None

        return Response({
            'connected': connected,
            'twitter_handle': f'@{twitter_handle}' if twitter_handle else user_profile.club.twitter_handle,
            'club_handle': user_profile.club.twitter_handle
        })

    except OAuthToken.DoesNotExist:
        return Response({
            'connected': False,
            'twitter_handle': user_profile.club.twitter_handle
        })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def twitter_disconnect(request):
    """
    Disconnect X/Twitter account

    Deletes OAuth tokens
    """

    user_profile = request.user.gaastats_profile

    # Verify user is admin
    if user_profile.role not in ['admin', 'dev']:
        return Response(
            {'error': 'Only admins can disconnect X accounts'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        OAuthToken.objects.filter(
            club=user_profile.club,
            provider='twitter'
        ).delete()

        return Response({
            'success': True,
            'message': 'X account disconnected'
        })

    except Exception as e:
        return Response(
            {'error': f'Failed to disconnect: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
