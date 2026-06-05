from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from apps.documents.models import Document
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.services import get_user_workspaces


@login_required
def dashboard(request):
    workspaces = get_user_workspaces(request.user).prefetch_related("memberships").annotate(
        document_count=Count("documents", distinct=True),
        ready_document_count=Count(
            "documents",
            filter=Q(documents__status=Document.Status.READY),
            distinct=True,
        ),
        failed_document_count=Count(
            "documents",
            filter=Q(documents__status=Document.Status.FAILED),
            distinct=True,
        ),
    )
    selected_slug = request.GET.get("workspace")
    selected_workspace = None

    if selected_slug:
        selected_workspace = workspaces.filter(slug=selected_slug).first()

    if selected_workspace is None:
        selected_workspace = workspaces.first()

    membership = None
    if selected_workspace:
        membership = WorkspaceMembership.objects.filter(
            workspace=selected_workspace,
            user=request.user,
        ).first()

    return render(
        request,
        "workspaces/dashboard.html",
        {
            "workspaces": workspaces,
            "selected_workspace": selected_workspace,
            "membership": membership,
        },
    )
