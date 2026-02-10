"""
Tests for Django middleware
"""

import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model

from gaastats.middleware import SubdomainMiddleware, ClubFilterMiddleware
from gaastats.models import Club, UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestSubdomainMiddleware:
    """Test subdomain middleware extraction"""

    def test_extract_subdomain_from_host(self, rf):
        """Test middleware correctly extracts subdomain from Host header"""
        middleware = SubdomainMiddleware(get_response)

        # Test valid subdomain
        request = rf.get('/api/health/')
        request.META['HTTP_HOST'] = 'testklub.api.gaastats.ie'
        
        middleware.process_request(request)
        assert hasattr(request, 'subdomain')
        assert request.subdomain == 'testklub'

    def test_extract_subdomain_from_www(self, rf):
        """Test middleware handles www subdomain"""
        middleware = SubdomainMiddleware(get_response)

        request = rf.get('/api/health/')
        request.META['HTTP_HOST'] = 'www.api.gaastats.ie'
        
        middleware.process_request(request)
        assert hasattr(request, 'subdomain')
        # www is typically handled as root domain

    def test_no_subdomain_from_localhost(self, rf):
        """Test middleware handles localhost (no subdomain)"""
        middleware = SubdomainMiddleware(get_response)

        request = rf.get('/api/health/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        
        middleware.process_request(request)
        # Should not add subdomain for localhost


@pytest.mark.django_db
class TestClubFilterMiddleware:
    """Test club filter middleware for multi-tenant isolation"""

    def test_filter_queries_by_subdomain(self, admin_club, rf):
        """Test middleware filters queries by subdomain"""
        middleware = ClubFilterMiddleware(get_response)
        
        user = User.objects.create_user(username='admin', password='pass')
        profile = UserProfile.objects.create(
            user=user,
            club=admin_club,
            role='admin'
        )

        request = rf.get('/api/clubs/')
        request.META['HTTP_HOST'] = 'testklub.api.gaastats.ie'
        request.user = user
        
        middleware.process_request(request)
        
        # Middleware should set club context
        assert hasattr(request, 'club')
        assert request.club.subdomain == 'testklub'

    def test_middleware_with_no_matching_subdomain(self, rf):
        """Test middleware handles request with non-existent subdomain"""
        middleware = ClubFilterMiddleware(get_response)
        
        user = User.objects.create_user(username='user', password='pass')
        
        request = rf.get('/api/clubs/')
        request.META['HTTP_HOST'] = 'nonexistent.api.gaastats.ie'
        request.user = user
        
        middleware.process_request(request)
        
        # Should not crash, request.club should be None or handle gracefully
        assert hasattr(request, 'club')

    def test_middleware_with_different_user_roles(self, admin_club, viewer_club, rf):
        """Test middleware works with different user roles"""
        middleware = ClubFilterMiddleware(get_response)
        
        admin_user = User.objects.create_user(username='admin', password='pass')
        viewer_user = User.objects.create_user(username='viewer', password='pass')
        
        UserProfile.objects.create(user=admin_user, club=admin_club, role='admin')
        UserProfile.objects.create(user=viewer_user, club=admin_club, role='viewer')

        request_admin = rf.get('/api/clubs/')
        request_admin.META['HTTP_HOST'] = 'testklub.api.gaastats.ie'
        request_admin.user = admin_user
        
        request_viewer = rf.get('/api/clubs/')
        request_viewer.META['HTTP_HOST'] = 'testklub.api.gaastats.ie'
        request_viewer.user = viewer_user
        
        # Both should successfully process
        middleware.process_request(request_admin)
        middleware.process_request(request_viewer)
        
        assert request_admin.club.id == admin_club.id
        assert request_viewer.club.id == admin_club.id


# Dummy get_response function for middleware tests
def get_response(request):
    """Dummy response for middleware testing"""
    from django.http import HttpResponse
    return HttpResponse("OK")
