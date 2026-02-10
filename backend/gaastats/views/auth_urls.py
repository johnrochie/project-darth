"""
URL Configuration for Authentication (Web Dashboard)
"""

from django.urls import path
from .auth import (
    auth_login, auth_register, auth_logout, auth_me,
    password_reset, password_reset_confirm
)

urlpatterns = [
    path('login/', auth_login, name='login'),
    path('register/', auth_register, name='register'),
    path('logout/', auth_logout, name='logout'),
    path('me/', auth_me, name='me'),
    path('password-reset/', password_reset, name='password_reset'),
    path('password-reset-confirm/<str:token>/<str:uid>/', password_reset_confirm, name='password_reset_confirm'),
]
