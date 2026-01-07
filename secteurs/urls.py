"""
URLs de l'application secteurs.
"""
from django.urls import path
from . import views

app_name = 'secteurs'

urlpatterns = [
    path('', views.secteur_list_view, name='list'),
    path('create/', views.secteur_create_view, name='create'),
    path('update/<int:pk>/', views.secteur_update_view, name='update'),
    path('delete/<int:pk>/', views.secteur_delete_view, name='delete'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/secteurs/', views.user_secteurs_view, name='user_secteurs'),
]
