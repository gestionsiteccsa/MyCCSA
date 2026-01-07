"""
URLs de l'application fractionnement.
"""
from django.urls import path
from . import views

app_name = 'fractionnement'

urlpatterns = [
    # Vue principale
    path('', views.fractionnement_view, name='index'),

    # Cycles hebdomadaires
    path('cycles/', views.cycle_list_view, name='cycle_list'),
    path('cycles/create/', views.cycle_create_view, name='cycle_create'),
    path('cycles/<int:pk>/update/', views.cycle_update_view, name='cycle_update'),
    path('cycles/<int:pk>/delete/', views.cycle_delete_view, name='cycle_delete'),

    # Périodes de congés
    path('periodes/', views.periode_list_view, name='periode_list'),
    path('periodes/create/', views.periode_create_view, name='periode_create'),
    path('periodes/<int:pk>/update/', views.periode_update_view, name='periode_update'),
    path('periodes/<int:pk>/delete/', views.periode_delete_view, name='periode_delete'),

    # API JSON
    path('api/calendrier/<int:annee>/', views.api_calendrier_data, name='api_calendrier_data'),
    path('api/calcul/<int:annee>/', views.api_calcul_fractionnement, name='api_calcul_fractionnement'),
]
