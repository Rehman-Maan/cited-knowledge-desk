from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.chat.forms import ChatQuestionForm
from apps.chat.models import ChatSession
from apps.chat.services import ask_question, create_chat_session
from apps.feedback.models import AnswerFeedback
from apps.workspaces.services import get_user_workspaces


def _selected_workspace(request):
    workspaces = get_user_workspaces(request.user)
    selected_slug = request.GET.get("workspace")
    workspace = None

    if selected_slug:
        workspace = workspaces.filter(slug=selected_slug).first()

    return workspace or workspaces.first()


def _failure_tag_choices():
    return [[value, label] for value, label in AnswerFeedback.FailureTag.choices]


@login_required
def chat_home(request):
    workspace = _selected_workspace(request)
    sessions = ChatSession.objects.none()
    if workspace:
        sessions = ChatSession.objects.filter(workspace=workspace, user=request.user)

    return render(
        request,
        "chat/session_list.html",
        {
            "workspace": workspace,
            "sessions": sessions,
        },
    )


@login_required
@require_POST
def create_session(request):
    workspace = _selected_workspace(request)
    if workspace is None:
        messages.error(request, "Create a workspace before starting a chat.")
        return redirect("workspaces:dashboard")

    session = create_chat_session(workspace=workspace, user=request.user)
    return redirect(session.get_absolute_url())


@login_required
def session_detail(request, pk):
    session = get_object_or_404(
        ChatSession.objects.select_related("workspace", "user").prefetch_related(
            "messages__citations__document",
            "messages__citations__chunk",
            Prefetch(
                "messages__feedback",
                queryset=AnswerFeedback.objects.filter(user=request.user),
                to_attr="current_user_feedback",
            ),
        ),
        pk=pk,
    )
    if session.user_id != request.user.id:
        raise PermissionDenied("You can only open your own chat sessions.")

    sessions = ChatSession.objects.filter(workspace=session.workspace, user=request.user)

    return render(
        request,
        "chat/session_detail.html",
        {
            "session": session,
            "sessions": sessions,
            "form": ChatQuestionForm(),
            "failure_tags": _failure_tag_choices(),
        },
    )


@login_required
@require_POST
def ask(request, pk):
    session = get_object_or_404(ChatSession, pk=pk, user=request.user)
    form = ChatQuestionForm(request.POST)
    if form.is_valid():
        ask_question(session=session, question=form.cleaned_data["question"])
        return redirect(session.get_absolute_url())

    return render(
        request,
        "chat/session_detail.html",
        {
            "session": session,
            "sessions": ChatSession.objects.filter(workspace=session.workspace, user=request.user),
            "form": form,
            "failure_tags": _failure_tag_choices(),
        },
        status=400,
    )
