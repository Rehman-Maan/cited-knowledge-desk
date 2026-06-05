from functools import wraps
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect

from apps.workspaces.models import WorkspaceMembership

GUEST_SESSION_KEY = "guest_mode"


def is_guest_request(request) -> bool:
    return bool(request.user.is_authenticated and request.session.get(GUEST_SESSION_KEY))


def start_guest_session(request):
    User = get_user_model()
    username = f"guest_{uuid4().hex[:10]}"
    user = User.objects.create_user(username=username, email="")
    user.set_unusable_password()
    user.save(update_fields=["password"])
    workspace = WorkspaceMembership.objects.select_related("workspace").get(user=user).workspace
    workspace.name = "Guest Workspace"
    workspace.save(update_fields=["name"])
    login(request, user)
    request.session[GUEST_SESSION_KEY] = True
    return user


def guest_restricted(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_guest_request(request):
            messages.info(request, "Guest access is limited to Dashboard, Documents, and Chat.")
            return redirect("workspaces:dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper
