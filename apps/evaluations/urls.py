from django.urls import path

from apps.evaluations import views

app_name = "evaluations"

urlpatterns = [
    path("", views.run_list, name="list"),
    path("run/", views.start_run, name="run"),
    path("<int:pk>/", views.run_detail, name="detail"),
]
