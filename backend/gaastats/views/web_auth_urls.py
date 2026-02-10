"""
URL Configuration for Web Dashboard Authentication
"""

from django.urls import path
from . import web_auth as web_auth
from . import auth as api_auth

urlpatterns = [
    # Web dashboard auth (session-based, for HTML templates)
    path('login/', web_auth.login_user, name='login'),
    path('logout/', web_auth.logout_user, name='logout'),

    # REST API auth (token-based, for iPad app)
    path('token/', api_auth.GenerateAuthToken.as_view(), name='token'),
]
