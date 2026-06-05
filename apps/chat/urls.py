from django.urls import path

from apps.chat import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_home, name="home"),
    path("sessions/", views.create_session, name="create-session"),
    path("sessions/<int:pk>/", views.session_detail, name="detail"),
    path("sessions/<int:pk>/ask/", views.ask, name="ask"),
]
