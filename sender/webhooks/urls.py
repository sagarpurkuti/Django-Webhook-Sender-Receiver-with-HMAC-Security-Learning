from django.urls import path

from .views import send_webhook


urlpatterns = [
    path("send/", send_webhook, name="send-webhook"),
]
