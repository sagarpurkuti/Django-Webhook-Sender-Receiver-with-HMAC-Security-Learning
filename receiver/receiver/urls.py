from django.contrib import admin
from django.urls import include, path

from core.views import hello, echo


urlpatterns = [
    path("admin/", admin.site.urls),

    path("hello/", hello),
    path("echo/", echo),

    path("webhooks/", include("webhooks.urls")),
]
