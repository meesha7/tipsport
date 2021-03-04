# -*- coding: utf-8 -*-
"""

"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index.index, name='index'),
    path('bets/', views.bets.list_bets, name='list_bets'),
    path('bet/<int:id_bet>/', views.bets.view_bet, name='view_bet'),
    path('stats/', views.stats.stats, name='stats'),
    path('stats/overview/', views.stats.stats_overview, name='stats_overview'),
    path('stats/counts/', views.stats.stats_counts, name='stats_counts'),
    path('stats/results/', views.stats.stats_results, name='stats_results'),
    path('stats/sport/<str:sport>/', views.stats.stats_sport, name='stats_sport'),
    path('stats/sport/', views.stats.stats_sport, name='stats_sport'),
    path('stats/history/', views.stats.stats_history, name='stats_history'),
]
