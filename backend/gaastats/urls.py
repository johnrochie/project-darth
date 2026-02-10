"""
URL Configuration for GAA Stats App

Supports subdomain-based routing for multi-tenant clubs
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('gaastats.views.api_urls')),

    # Web dashboard (templates)
    path('', TemplateView.as_view(template_name='dashboard/home.html'), name='dashboard_home'),
    path('dashboard/', include('gaastats.views.dashboard_urls')),
    path('reports/', include('gaastats.views.reports_urls')),

    # Auth endpoints (for web dashboard)
    path('auth/', include('gaastats.views.auth_urls')),

    # Social auth (X/Twitter OAuth)
    # path('auth/', include('social_django.urls', namespace='social')), # TODO: Remove in phase 2, use /api/auth/ instead

    # Static files in development
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
