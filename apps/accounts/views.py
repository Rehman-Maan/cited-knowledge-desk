from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.forms import SignUpForm
from apps.accounts.guest import start_guest_session


def signup(request):
    if request.user.is_authenticated:
        return redirect("workspaces:dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("workspaces:dashboard")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@require_POST
def guest_login(request):
    if request.user.is_authenticated:
        return redirect("workspaces:dashboard")

    start_guest_session(request)
    return redirect("workspaces:dashboard")
