from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("", include("estuairefleet.core.urls", namespace="core")),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("users/", include("estuairefleet.users.urls", namespace="users")),
    path("signals/", include("estuairefleet.signals.urls", namespace="signals")),
    path("fleet/", include("estuairefleet.fleet.urls", namespace="fleet")),
    path("accounts/", include("allauth.urls")),
    path("api/", include("config.api_router")),
    path("api/auth-token/", obtain_auth_token, name="obtain_auth_token"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
