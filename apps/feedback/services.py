from django.core.exceptions import PermissionDenied

from apps.chat.models import ChatMessage
from apps.feedback.models import AnswerFeedback
from apps.workspaces.services import user_can_administer_workspace


def submit_feedback(*, message: ChatMessage, user, rating: str, failure_tag: str = "", comment: str = ""):
    if message.role != ChatMessage.Role.ASSISTANT:
        raise ValueError("Feedback can only be submitted for assistant messages.")

    if message.session.user_id != user.id:
        raise PermissionDenied("You can only review answers from your own chats.")

    feedback, _ = AnswerFeedback.objects.update_or_create(
        message=message,
        user=user,
        defaults={
            "rating": rating,
            "failure_tag": failure_tag if rating == AnswerFeedback.Rating.DOWN else "",
            "comment": comment,
            "reviewed": False,
        },
    )
    return feedback


def mark_feedback_reviewed(*, feedback: AnswerFeedback, user) -> AnswerFeedback:
    if not user_can_administer_workspace(user, feedback.message.session.workspace):
        raise PermissionDenied("Only workspace admins can review feedback.")

    feedback.reviewed = True
    feedback.save(update_fields=["reviewed"])
    return feedback
