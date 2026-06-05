"""Root URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", include("apps.workspaces.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("admin/", admin.site.urls),
    path("chat/", include("apps.chat.urls")),
    path("documents/", include("apps.documents.urls")),
    path("evaluations/", include("apps.evaluations.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("health/", health_check, name="health-check"),
    path("retrieval/", include("apps.retrieval.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
