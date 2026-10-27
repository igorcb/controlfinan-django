from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from ..auth import rate_limit
from ..models import User


@require_http_methods(["GET", "POST"])
@rate_limit("passwords", redirect_to="new_password")
def new(request):
    if request.method == "POST":
        user = User.objects.filter(email_address=User.normalize_email(request.POST.get("email_address"))).first()
        if user:
            url = request.build_absolute_uri(reverse("edit_password", args=[user.password_reset_token()]))
            context = {"url": url, "expires_in": "15 minutos"}
            send_mail(
                "Redefinição de senha",
                render_to_string("finance/emails/reset.txt", context),
                None,
                [user.email_address],
                html_message=render_to_string("finance/emails/reset.html", context),
            )
        messages.success(request, "Se o e-mail estiver cadastrado, enviamos as instruções para redefinir a senha.")
        return redirect("new_session")
    return render(request, "finance/passwords/new.html", {"email_address": request.GET.get("email_address", "")})


@require_http_methods(["GET", "POST"])
def edit(request, token):
    user = User.find_by_password_reset_token(token)
    if user is None:
        messages.error(request, "O link de redefinição é inválido ou expirou.")
        return redirect("new_password")
    if request.method == "POST":
        password = request.POST.get("password", "")
        errors = user.validate(password, request.POST.get("password_confirmation", ""), password_required=True)
        if errors:
            messages.error(request, "As senhas não conferem ou têm menos de 6 caracteres.")
            return redirect("edit_password", token=token)
        user.set_password(password)
        user.save()
        user.sessions.all().delete()
        messages.success(request, "Senha redefinida.")
        return redirect("new_session")
    return render(request, "finance/passwords/edit.html", {"token": token})
