"""
Dashboard URL Configuration
"""

from django.urls import path
from . import views as dashboard_views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', dashboard_views.dashboard_home, name='home'),

    # Matches
    path('matches/', dashboard_views.match_list, name='match_list'),
    path('matches/<int:match_id>/', dashboard_views.match_detail, name='match_detail'),
    path('matches/<int:match_id>/live/', dashboard_views.match_live, name='match_live'),

    # Players
    path('players/', dashboard_views.player_list, name='player_list'),
    path('players/<int:player_id>/', dashboard_views.player_detail, name='player_detail'),

    # Reports
    path('reports/', dashboard_views.reports_index, name='reports_index'),
    path('reports/match/<int:match_id>/', dashboard_views.report_match_pdf, name='report_match_pdf'),
    path('reports/match/<int:match_id>/excel/', dashboard_views.report_match_excel, name='report_match_excel'),
    path('reports/player/<int:player_id>/', dashboard_views.report_player_pdf, name='report_player_pdf'),
    path('reports/player/<int:player_id>/excel/', dashboard_views.report_player_excel, name='report_player_excel'),
    path('reports/season/', dashboard_views.report_season_excel, name='report_season_excel'),
]

# Namespace for reverse URLs
