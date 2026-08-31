from django.urls import path

from .views import receive_webhook


urlpatterns = [
    path("events/", receive_webhook, name="receive-webhook"),
]
