import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.chat.models import ChatMessage
from apps.chat.services import create_chat_session
from apps.feedback.models import AnswerFeedback
from apps.feedback.services import submit_feedback
from apps.workspaces.models import Workspace, WorkspaceMembership


def create_assistant_message(username="feedback-owner"):
    user = get_user_model().objects.create_user(username=username, password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    session = create_chat_session(workspace=workspace, user=user)
    message = session.messages.create(
        role=ChatMessage.Role.ASSISTANT,
        content="APPLE is coded as CRRNG. [D1-C1]",
    )
    return user, workspace, session, message


@pytest.mark.django_db
def test_submit_feedback_saves_down_rating_with_review_tag():
    user, _, _, message = create_assistant_message()

    feedback = submit_feedback(
        message=message,
        user=user,
        rating=AnswerFeedback.Rating.DOWN,
        failure_tag=AnswerFeedback.FailureTag.WEAK_CITATION,
        comment="Citation is too broad.",
    )

    assert feedback.rating == AnswerFeedback.Rating.DOWN
    assert feedback.failure_tag == AnswerFeedback.FailureTag.WEAK_CITATION
    assert feedback.comment == "Citation is too broad."
    assert feedback.reviewed is False


@pytest.mark.django_db
def test_submit_feedback_updates_existing_feedback_and_clears_up_tag():
    user, _, _, message = create_assistant_message("feedback-update")
    submit_feedback(
        message=message,
        user=user,
        rating=AnswerFeedback.Rating.DOWN,
        failure_tag=AnswerFeedback.FailureTag.HALLUCINATION,
        comment="Unsupported claim.",
    )

    feedback = submit_feedback(message=message, user=user, rating=AnswerFeedback.Rating.UP)

    assert AnswerFeedback.objects.filter(message=message, user=user).count() == 1
    assert feedback.rating == AnswerFeedback.Rating.UP
    assert feedback.failure_tag == ""
    assert feedback.comment == ""


@pytest.mark.django_db
def test_feedback_cannot_be_submitted_for_someone_elses_chat():
    _, _, _, message = create_assistant_message("feedback-private")
    other_user = get_user_model().objects.create_user(username="feedback-outsider", password="test-pass")

    with pytest.raises(PermissionDenied):
        submit_feedback(message=message, user=other_user, rating=AnswerFeedback.Rating.UP)


@pytest.mark.django_db
def test_feedback_cannot_be_submitted_for_user_message():
    user, _, session, _ = create_assistant_message("feedback-role")
    user_message = session.messages.create(role=ChatMessage.Role.USER, content="Question")

    with pytest.raises(ValueError):
        submit_feedback(message=user_message, user=user, rating=AnswerFeedback.Rating.UP)


@pytest.mark.django_db
def test_feedback_submit_view_redirects_and_persists(client):
    user, _, session, message = create_assistant_message("feedback-view")
    client.force_login(user)

    response = client.post(
        reverse("feedback:submit", kwargs={"message_id": message.pk}),
        {
            "rating": "down",
            "failure_tag": "missing_citation",
            "comment": "The answer needs a citation.",
        },
    )

    feedback = AnswerFeedback.objects.get(message=message, user=user)
    assert response.status_code == 302
    assert response["Location"] == session.get_absolute_url()
    assert feedback.rating == AnswerFeedback.Rating.DOWN
    assert feedback.failure_tag == AnswerFeedback.FailureTag.MISSING_CITATION


@pytest.mark.django_db
def test_chat_page_renders_feedback_controls_for_assistant_answers(client):
    user, _, session, _ = create_assistant_message("feedback-render")
    client.force_login(user)

    response = client.get(session.get_absolute_url())

    assert response.status_code == 200
    assert b'aria-label="Mark helpful"' in response.content
    assert b'aria-label="Send to review"' in response.content
    assert b"Comment optional" in response.content
    assert b"failure-tags" in response.content


@pytest.mark.django_db
def test_workspace_admin_can_review_feedback(client):
    user, workspace, _, message = create_assistant_message("feedback-review")
    feedback = submit_feedback(message=message, user=user, rating=AnswerFeedback.Rating.DOWN)
    client.force_login(user)

    queue_response = client.get(reverse("feedback:review"))
    review_response = client.post(reverse("feedback:mark-reviewed", kwargs={"pk": feedback.pk}))
    feedback.refresh_from_db()

    assert queue_response.status_code == 200
    assert b"APPLE is coded as CRRNG" in queue_response.content
    assert review_response.status_code == 302
    assert feedback.reviewed is True
    assert workspace.created_by == user


@pytest.mark.django_db
def test_workspace_member_cannot_review_feedback(client):
    owner, workspace, _, message = create_assistant_message("feedback-admin-owner")
    member = get_user_model().objects.create_user(username="feedback-member", password="test-pass")
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=member,
        role=WorkspaceMembership.Role.MEMBER,
    )
    feedback = submit_feedback(message=message, user=owner, rating=AnswerFeedback.Rating.DOWN)
    client.force_login(member)

    response = client.post(reverse("feedback:mark-reviewed", kwargs={"pk": feedback.pk}))
    feedback.refresh_from_db()

    assert response.status_code == 403
    assert feedback.reviewed is False
