from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.guest import guest_restricted
from apps.evaluations.forms import EvaluationRunForm
from apps.evaluations.models import EvaluationRun
from apps.evaluations.services import run_evaluation
from apps.workspaces.services import get_user_workspaces, user_can_administer_workspace


@login_required
@guest_restricted
def run_list(request):
    workspaces = get_user_workspaces(request.user)
    admin_workspace_ids = [
        workspace.id
        for workspace in workspaces
        if user_can_administer_workspace(request.user, workspace)
    ]
    runs = EvaluationRun.objects.select_related("workspace", "created_by").filter(
        workspace_id__in=admin_workspace_ids
    )
    workspace = workspaces.filter(id__in=admin_workspace_ids).first()
    return render(
        request,
        "evaluations/run_list.html",
        {
            "runs": runs,
            "workspace": workspace,
            "form": EvaluationRunForm(),
        },
    )


@login_required
@require_POST
@guest_restricted
def start_run(request):
    workspaces = get_user_workspaces(request.user)
    workspace = workspaces.filter(slug=request.POST.get("workspace")).first() or workspaces.first()
    if workspace is None or not user_can_administer_workspace(request.user, workspace):
        raise PermissionDenied("Only workspace admins can run evaluations.")

    form = EvaluationRunForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Evaluation could not be started.")
        return redirect("evaluations:list")

    try:
        run = run_evaluation(
            workspace=workspace,
            user=request.user,
            dataset_path=form.cleaned_data["dataset_path"],
            name=form.cleaned_data["name"],
            top_k=form.cleaned_data["retrieval_top_k"],
        )
    except Exception as exc:
        messages.error(request, f"Evaluation failed: {exc}")
        return redirect("evaluations:list")

    messages.success(request, "Evaluation completed.")
    return redirect(run.get_absolute_url())


@login_required
@guest_restricted
def run_detail(request, pk):
    run = get_object_or_404(
        EvaluationRun.objects.select_related("workspace", "created_by").prefetch_related("results"),
        pk=pk,
    )
    if not user_can_administer_workspace(request.user, run.workspace):
        raise PermissionDenied("Only workspace admins can inspect evaluations.")

    return render(
        request,
        "evaluations/run_detail.html",
        {
            "run": run,
            "results": run.results.all(),
        },
    )
