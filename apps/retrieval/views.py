from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.guest import guest_restricted
from apps.retrieval.forms import RetrievalSearchForm
from apps.workspaces.services import get_user_workspaces
from services.retrieval.vector_search import search_similar_chunks


@login_required
@guest_restricted
def retrieval_search(request):
    workspaces = get_user_workspaces(request.user)
    selected_slug = request.GET.get("workspace")
    workspace = None

    if selected_slug:
        workspace = workspaces.filter(slug=selected_slug).first()

    workspace = workspace or workspaces.first()
    form = RetrievalSearchForm(request.GET or None)
    results = []

    if workspace and form.is_valid():
        results = search_similar_chunks(
            workspace=workspace,
            query=form.cleaned_data["q"],
            top_k=form.cleaned_data["top_k"],
        )

    return render(
        request,
        "retrieval/search.html",
        {
            "form": form,
            "workspace": workspace,
            "results": results,
        },
    )
