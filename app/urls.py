"""
Configuration des URLs principales du projet.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("secteurs/", include("secteurs.urls")),
    path("roles/", include("role.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("events/", include("events.urls")),
    path("fractionnement/", include("fractionnement.urls")),
    path("", include("home.urls")),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

# Handlers d'erreur personnalisés
handler404 = 'app.views.handler404'
handler500 = 'app.views.handler500'
handler403 = 'app.views.handler403'
handler400 = 'app.views.handler400'
