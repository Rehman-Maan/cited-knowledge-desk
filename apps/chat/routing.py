from django.urls import path

from apps.chat import consumers

websocket_urlpatterns = [
    path("ws/chat/<int:session_id>/", consumers.ChatConsumer.as_asgi()),
]
