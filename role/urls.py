"""
URLs de l'application role.
"""
from django.urls import path
from . import views

app_name = 'role'

urlpatterns = [
    path('', views.role_list_view, name='list'),
    path('create/', views.role_create_view, name='create'),
    path('update/<int:pk>/', views.role_update_view, name='update'),
    path('delete/<int:pk>/', views.role_delete_view, name='delete'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/role/', views.user_role_view, name='user_role'),
    path('api/check-level/', views.check_level_available, name='check_level'),
]

