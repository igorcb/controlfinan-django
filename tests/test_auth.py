import re
import time

import time_machine
from django.core import mail
from django.test import Client

from finance.models import Session, User


class TestLogin:
    def test_redirects_guests_to_the_login(self):
        response = Client().get("/current_accounts")
        assert response.status_code == 302
        assert response["Location"] == "/session/new"

    def test_signs_in_and_returns_to_the_requested_page(self, user):
        client = Client()
        client.get("/dashboard")
        response = client.post("/session", {"email_address": "motorista@exemplo.com", "password": "senha123"})
        assert response["Location"] == "http://testserver/dashboard"
        assert Session.objects.filter(user=user).count() == 1
        assert client.get("/dashboard").status_code == 200

    def test_rejects_a_wrong_password(self, user):
        client = Client()
        response = client.post("/session", {"email_address": "motorista@exemplo.com", "password": "errada"}, follow=True)
        assert "E-mail ou senha inválidos." in response.content.decode()

    def test_logout_ends_the_session(self, signed_in, user):
        response = signed_in.post("/session/destroy")
        assert response["Location"] == "/session/new"
        assert not Session.objects.filter(user=user).exists()
        assert signed_in.get("/").status_code == 302

    def test_rate_limits_login_attempts(self, user):
        client = Client()
        for _ in range(10):
            client.post("/session", {"email_address": "x@y.com", "password": "x"})
        response = client.post("/session", {"email_address": "x@y.com", "password": "x"}, follow=True)
        assert "Tente novamente mais tarde." in response.content.decode()

    def test_rejects_a_tampered_cookie(self, user):
        client = Client()
        client.cookies["session_id"] = "1:forjado"
        assert client.get("/").status_code == 302


class TestRegistration:
    def test_creates_the_account_and_signs_in(self):
        client = Client()
        response = client.post(
            "/registration",
            {"user[email_address]": "novo@exemplo.com", "user[password]": "123456", "user[password_confirmation]": "123456"},
        )
        assert response["Location"] == "/"
        assert User.objects.filter(email_address="novo@exemplo.com").exists()
        assert "Conta criada." in client.get("/").content.decode()

    def test_shows_the_errors(self, user):
        response = Client().post(
            "/registration",
            {"user[email_address]": "motorista@exemplo.com", "user[password]": "123", "user[password_confirmation]": "456"},
        )
        body = response.content.decode()
        assert response.status_code == 422
        assert "Confirmação da senha não é igual a Senha" in body
        assert "E-mail já está em uso" in body
        assert "Senha é muito curto (mínimo: 6 caracteres)" in body


class TestPasswordReset:
    def request_reset(self, email):
        return Client().post("/passwords", {"email_address": email}, follow=True)

    def reset_link(self):
        return re.search(r"http://testserver(/passwords/[^\s]+/edit)", mail.outbox[-1].body).group(1)

    def test_sends_the_link_by_email(self, user):
        response = self.request_reset("motorista@exemplo.com")
        assert "Se o e-mail estiver cadastrado" in response.content.decode()
        assert mail.outbox[-1].subject == "Redefinição de senha"
        assert "Este link expira em 15 minutos." in mail.outbox[-1].body

    def test_does_not_reveal_unknown_emails(self):
        response = self.request_reset("ninguem@exemplo.com")
        assert "Se o e-mail estiver cadastrado" in response.content.decode()
        assert mail.outbox == []

    def test_sets_a_new_password_and_ends_all_sessions(self, signed_in, user):
        self.request_reset("motorista@exemplo.com")
        response = Client().post(self.reset_link(), {"password": "novasenha", "password_confirmation": "novasenha"})
        assert response["Location"] == "/session/new"
        user.refresh_from_db()
        assert user.check_password("novasenha")
        assert not user.sessions.exists()

    def test_rejects_different_passwords(self, user):
        self.request_reset("motorista@exemplo.com")
        link = self.reset_link()
        response = Client().post(link, {"password": "novasenha", "password_confirmation": "outra"}, follow=True)
        assert "As senhas não conferem ou têm menos de 6 caracteres." in response.content.decode()

    def test_link_expires_after_15_minutes(self, user):
        self.request_reset("motorista@exemplo.com")
        link = self.reset_link()
        with time_machine.travel(time.time() + 16 * 60, tick=False):
            response = Client().get(link, follow=True)
        assert "O link de redefinição é inválido ou expirou." in response.content.decode()
