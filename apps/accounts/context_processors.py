from apps.accounts.guest import is_guest_request


def guest_mode(request):
    return {"is_guest_mode": is_guest_request(request)}
