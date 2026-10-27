from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from ..auth import after_authentication_url, rate_limit, require_authentication, start_new_session_for, terminate_session
from ..models import User


@require_http_methods(["GET", "POST"])
@rate_limit("sessions", redirect_to="new_session")
def new(request):
    if request.method == "POST":
        user = User.authenticate_by(request.POST.get("email_address"), request.POST.get("password"))
        if user:
            start_new_session_for(request, user)
            return redirect(after_authentication_url(request))
        messages.error(request, "E-mail ou senha inválidos.")
        return redirect("new_session")
    return render(request, "finance/sessions/new.html", {"email_address": request.GET.get("email_address", "")})


@require_authentication
@require_POST
def destroy(request):
    terminate_session(request)
    return redirect("new_session")
