"""
URLs de l'application accounts.
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path(
        'password-reset/<str:token>/',
        views.password_reset_confirm_view,
        name='password_reset_confirm'
    ),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password-change/', views.password_change_view, name='password_change'),
    path(
        'notifications-settings/',
        views.notifications_settings_view,
        name='notifications_settings'
    ),
]
