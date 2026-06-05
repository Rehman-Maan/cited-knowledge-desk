from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.documents.forms import DocumentUploadForm
from apps.documents.models import Document
from apps.documents.services import create_document, get_document_for_user, retry_document_ingestion
from apps.workspaces.models import WorkspaceMembership
from apps.workspaces.services import get_user_workspaces, user_can_administer_workspace


def _selected_workspace(request):
    workspaces = get_user_workspaces(request.user)
    selected_slug = request.GET.get("workspace")
    workspace = None

    if selected_slug:
        workspace = workspaces.filter(slug=selected_slug).first()

    return workspace or workspaces.first()


@login_required
def document_list(request):
    workspace = _selected_workspace(request)
    documents = Document.objects.none()
    membership = None
    can_upload = False

    if workspace:
        documents = Document.objects.filter(workspace=workspace).select_related("uploaded_by")
        membership = WorkspaceMembership.objects.filter(workspace=workspace, user=request.user).first()
        can_upload = user_can_administer_workspace(request.user, workspace)

    return render(
        request,
        "documents/document_list.html",
        {
            "workspace": workspace,
            "documents": documents,
            "membership": membership,
            "can_upload": can_upload,
        },
    )


@login_required
def document_upload(request):
    workspace = _selected_workspace(request)
    if workspace is None:
        messages.error(request, "Create a workspace before uploading documents.")
        return redirect("workspaces:dashboard")

    if not user_can_administer_workspace(request.user, workspace):
        raise PermissionDenied("Only workspace admins can upload documents.")

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = create_document(
                workspace=workspace,
                user=request.user,
                title=form.cleaned_data["title"],
                file=form.cleaned_data["file"],
            )
            messages.success(request, "Document uploaded.")
            return redirect(document.get_absolute_url())
    else:
        form = DocumentUploadForm()

    return render(
        request,
        "documents/document_upload.html",
        {
            "form": form,
            "workspace": workspace,
        },
    )


@login_required
def document_detail(request, pk):
    document = get_document_for_user(request.user, pk)
    can_retry = (
        document.status == Document.Status.FAILED
        and user_can_administer_workspace(request.user, document.workspace)
    )
    return render(
        request,
        "documents/document_detail.html",
        {
            "document": document,
            "chunks": document.chunks.all()[:8],
            "can_retry": can_retry,
        },
    )


@login_required
@require_POST
def document_retry(request, pk):
    document = get_document_for_user(request.user, pk)
    try:
        retry_document_ingestion(document=document, user=request.user)
    except PermissionError as exc:
        raise PermissionDenied(str(exc)) from exc

    messages.success(request, "Document queued for ingestion retry.")
    return redirect(document.get_absolute_url())
