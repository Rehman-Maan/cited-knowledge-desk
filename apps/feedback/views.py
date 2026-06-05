from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.guest import guest_restricted, is_guest_request
from apps.chat.models import ChatMessage
from apps.feedback.forms import AnswerFeedbackForm
from apps.feedback.models import AnswerFeedback
from apps.feedback.services import mark_feedback_reviewed, submit_feedback
from apps.workspaces.services import get_user_workspaces, user_can_administer_workspace


@login_required
@require_POST
def submit_answer_feedback(request, message_id):
    message = get_object_or_404(
        ChatMessage.objects.select_related("session", "session__workspace"),
        pk=message_id,
    )
    if is_guest_request(request):
        messages.info(request, "Guest feedback is disabled.")
        return redirect(message.session.get_absolute_url())

    form = AnswerFeedbackForm(request.POST)
    if form.is_valid():
        submit_feedback(
            message=message,
            user=request.user,
            rating=form.cleaned_data["rating"],
            failure_tag=form.cleaned_data["failure_tag"],
            comment=form.cleaned_data["comment"],
        )
        messages.success(request, "Feedback saved.")
    else:
        messages.error(request, "Feedback could not be saved.")

    return redirect(message.session.get_absolute_url())


@login_required
@guest_restricted
def feedback_review(request):
    workspaces = get_user_workspaces(request.user)
    admin_workspace_ids = [
        workspace.id
        for workspace in workspaces
        if user_can_administer_workspace(request.user, workspace)
    ]
    feedback_items = (
        AnswerFeedback.objects.select_related(
            "message",
            "message__session",
            "message__session__workspace",
            "user",
        )
        .prefetch_related("message__citations__document")
        .filter(message__session__workspace_id__in=admin_workspace_ids)
    )

    return render(
        request,
        "feedback/review.html",
        {
            "feedback_items": feedback_items,
        },
    )


@login_required
@require_POST
@guest_restricted
def mark_reviewed(request, pk):
    feedback = get_object_or_404(
        AnswerFeedback.objects.select_related("message", "message__session", "message__session__workspace"),
        pk=pk,
    )
    try:
        mark_feedback_reviewed(feedback=feedback, user=request.user)
    except PermissionDenied:
        raise

    messages.success(request, "Feedback marked reviewed.")
    return redirect("feedback:review")
