"""
URLs de l'application events.
"""
from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_calendar_view, name='calendar'),
    path('list/', views.event_list_view, name='list'),
    path('mes-evenements/', views.my_events_view, name='my_events'),
    path('timeline/', views.event_timeline_view, name='timeline'),
    path('stats/', views.event_stats_view, name='stats'),
    path('create/', views.event_create_view, name='create'),
    path('<int:pk>/', views.event_detail_view, name='detail'),
    path('<int:pk>/update/', views.event_update_view, name='update'),
    path('<int:pk>/delete/', views.event_delete_view, name='delete'),
    path('<int:pk>/valider/', views.event_validate_view, name='validate'),
]
