"""
Multi-tenant middleware for subdomain-based club access
"""

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages


class SubdomainMiddleware(MiddlewareMixin):
    """
    Extracts subdomain from Host header and sets it in request
    Subdomain format: clubname.gaastats.ie
    """

    def process_request(self, request):
        """Extract subdomain from request Host header"""

        # Get the Host header
        host = request.get_host().split(':')[0]  # Remove port if present

        # Skip if localhost or IP address
        if host in ['localhost', '127.0.0.1']:
            request.subdomain = settings.DEFAULT_CLUB_SUBDOMAIN
            return

        # Extract subdomain from wildcard domain
        base_domain = settings.ALLOWED_HOSTS[-1]  # e.g., .gaastats.ie

        if host.endswith(base_domain.lstrip('.')):
            subdomain = host[:-len(base_domain.lstrip('.'))]
            request.subdomain = subdomain
        else:
            # No subdomain match - use default
            request.subdomain = settings.DEFAULT_CLUB_SUBDOMAIN


class ClubFilterMiddleware(MiddlewareMixin):
    """
    Filters all database queries by club_id for the current subdomain
    Ensures complete data siloing between clubs
    """

    def process_request(self, request):
        """Set club context for the request"""

        # Note: This is simplified - in production, you would:
        # 1. Query Club model by subdomain
        # 2. Set request.club_id
        # 3. Filter queries via custom manager

        # For now, placeholder logic
        request.club_id = getattr(request, 'club_id', None)


# Context processor for templates
def club_context(request):
    """Add club info to all templates"""

    # Placeholder - will be populated from Club model
    subdomain = getattr(request, 'subdomain', settings.DEFAULT_CLUB_SUBDOMAIN)

    return {
        'club_subdomain': subdomain,
        'club_name': subdomain.replace('-', ' ').title(),  # Placeholder
    }
