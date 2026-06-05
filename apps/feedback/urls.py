from django.urls import path

from apps.feedback import views

app_name = "feedback"

urlpatterns = [
    path("", views.feedback_review, name="review"),
    path("messages/<int:message_id>/", views.submit_answer_feedback, name="submit"),
    path("<int:pk>/reviewed/", views.mark_reviewed, name="mark-reviewed"),
]
