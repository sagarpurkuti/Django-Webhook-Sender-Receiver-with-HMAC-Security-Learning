from django.contrib import admin
from django.urls import include, path

from core.views import hello


urlpatterns = [
    path("admin/", admin.site.urls),

    path("hello/", hello),

    path("webhooks/", include("webhooks.urls")),
]
