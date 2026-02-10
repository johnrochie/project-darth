"""
X (Twitter) Integration Service

Handles OAuth 1.0a and tweet posting
"""

import tweepy
from django.conf import settings
from ..models import OAuthToken, Club


class XService:
    """Service for interacting with X/Twitter API"""

    def __init__(self, club):
        """
        Initialize X service for a specific club

        Args:
            club: Club instance with stored OAuth tokens
        """
        self.club = club
        self.tokens = self._get_tokens()
        self.client = None

    def _get_tokens(self):
        """Retrieve OAuth tokens for this club"""

        try:
            return OAuthToken.objects.get(club=self.club, provider='twitter')
        except OAuthToken.DoesNotExist:
            raise ValueError(f"No OAuth tokens found for club {self.club.name}")

    def _get_client(self):
        """
        Get authenticated Tweepy API client

        Returns:
            tweepy.API instance
        """

        if self.client:
            return self.client

        # Check if we have tokens stored
        if not self.tokens:
            raise ValueError("No OAuth tokens available - club not authorized")

        # Initialize OAuth1.0a auth
        auth = tweepy.OAuth1UserHandler(
            consumer_key=settings.SOCIAL_AUTH_TWITTER_KEY,
            consumer_secret=settings.SOCIAL_AUTH_TWITTER_SECRET,
            access_token=self.tokens.oauth_token,
            access_token_secret=self.tokens.oauth_token_secret
        )

        # Create API client
        self.client = tweepy.API(
            auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )

        # Verify credentials
        try:
            self.client.verify_credentials()
        except tweepy.TweepyException as e:
            raise ValueError(f"Failed to verify X credentials: {e}")

        return self.client

    def post_tweet(self, content):
        """
        Post a tweet/quote on X

        Args:
            content: Tweet text (max 280 chars)

        Returns:
            tweet_id: The ID of the posted tweet
            success: Boolean indicating if tweet was successful
        """

        if len(content) > 280:
            raise ValueError("Tweet content exceeds 280 character limit")

        api = self._get_client()

        try:
            # Post tweet
            tweet = api.update_status(content)
            return tweet.id, True
        except tweepy.TweepyException as e:
            print(f"Failed to post tweet: {e}")
            return None, False

    def post_score_update(self, match):
        """
        Post live score update tweet

        Args:
            match: Match instance with current scores

        Returns:
            tweet_id: The ID of the posted tweet, or None
            success: Boolean
        """

        # Build tweet content
        club_handle = self.club.twitter_handle or self.club.subdomain
        total_club_score = match.total_club_score
        total_opposition_score = match.total_opposition_score

        content = settings.X_TWEET_TEMPLATE.format(
            club_handle=club_handle,
            team=self.club.name,
            score=total_club_score,
            opposition_score=total_opposition_score,
            minute=match.status  # Could be current minute if in progress
        )

        # Post tweet
        tweet_id, success = self.post_tweet(content)

        # Record score update history
        from ..models import MatchScoreUpdate
        MatchScoreUpdate.objects.create(
            match=match,
            content=content,
            social_media_posted=success,
            x_post_id=tweet_id
        )

        return tweet_id, success

    @staticmethod
    def get_oauth_url(club_id, callback_url):
        """
        Generate OAuth request token and authorization URL

        Args:
            club_id: ID of club being authorized
            callback_url: OAuth callback URL

        Returns:
            (auth_url, request_token, request_token_secret)
        """

        import oauthlib.oauth1 as oauth
        import urllib.parse

        # Twitter OAuth endpoints
        request_token_url = 'https://api.twitter.com/oauth/request_token'
        authorize_url = 'https://api.twitter.com/oauth/authorize'

        # Create OAuth1 client
        consumer = oauth.OAuth1(
            client_key=settings.SOCIAL_AUTH_TWITTER_KEY,
            client_secret=settings.SOCIAL_AUTH_TWITTER_SECRET,
            callback_uri=callback_url,
            signature_method=oauth.SIGNATURE_HMAC_SHA1,
            signature_type=oauth.SIGNATURE_TYPE_QUERY
        )

        # Request temporary token
        headers = {'Accept': '*/*'}

        import requests

        response = requests.post(request_token_url, headers=headers, auth=consumer)

        if response.status_code != 200:
            raise ValueError(f"Failed to get request token: {response.text}")

        # Parse response
        response_data = urllib.parse.parse_qs(response.text)
        request_token = response_data.get('oauth_token', [None])[0]
        request_token_secret = response_data.get('oauth_token_secret', [None])[0]

        if not request_token:
            raise ValueError("No OAuth token received")

        # Build authorization URL
        auth_url = f"{authorize_url}?oauth_token={request_token}"

        return auth_url, request_token, request_token_secret

    @staticmethod
    def exchange_request_token(request_token, request_token_secret, oauth_verifier):
        """
        Exchange request token for access token

        Args:
            request_token: Temporary request token
            request_token_secret: Temporary request token secret
            oauth_verifier: OAuth verifier from callback

        Returns:
            (access_token, access_token_secret)
        """

        import oauthlib.oauth1 as oauth
        import urllib.parse
        import requests

        # Access token endpoint
        access_token_url = 'https://api.twitter.com/oauth/access_token'

        # Create OAuth1 client
        consumer = oauth.OAuth1(
            client_key=settings.SOCIAL_AUTH_TWITTER_KEY,
            client_secret=settings.SOCIAL_AUTH_TWITTER_SECRET,
            resource_owner_key=request_token,
            resource_owner_secret=request_token_secret,
            verifier=oauth_verifier,
            signature_method=oauth.SIGNATURE_HMAC_SHA1,
            signature_type=oauth.SIGNATURE_TYPE_QUERY
        )

        # Request access token
        headers = {'Accept': '*/*'}

        response = requests.post(access_token_url, headers=headers, auth=consumer)

        if response.status_code != 200:
            raise ValueError(f"Failed to get access token: {response.text}")

        # Parse response
        response_data = urllib.parse.parse_qs(response.text)
        access_token = response_data.get('oauth_token', [None])[0]
        access_token_secret = response_data.get('oauth_token_secret', [None])[0]

        if not access_token:
            raise ValueError("No access token received")

        return access_token, access_token_secret
