from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from ..auth import rate_limit, start_new_session_for
from ..models import User


@require_http_methods(["GET", "POST"])
@rate_limit("registrations", redirect_to="new_registration")
def new(request):
    user = User(email_address="")
    errors = []
    if request.method == "POST":
        user.email_address = request.POST.get("user[email_address]", "")
        password = request.POST.get("user[password]", "")
        errors = user.validate(password, request.POST.get("user[password_confirmation]", ""), password_required=True)
        if not errors:
            user.set_password(password)
            user.save()
            start_new_session_for(request, user)
            messages.success(request, "Conta criada.")
            return redirect("root")
    return render(request, "finance/registrations/new.html", {"user": user, "errors": errors}, status=422 if errors else 200)
