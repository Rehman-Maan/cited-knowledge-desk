from django.urls import path

from apps.retrieval import views

app_name = "retrieval"

urlpatterns = [
    path("search/", views.retrieval_search, name="search"),
]
