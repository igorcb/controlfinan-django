from django.http import HttpResponse
from django.urls import path

from finance.views import current_accounts, dashboards, passwords, registrations, sessions

urlpatterns = [
    path("session/new", sessions.new, name="new_session"),
    path("session", sessions.new, name="session"),
    path("session/destroy", sessions.destroy, name="destroy_session"),
    path("registration/new", registrations.new, name="new_registration"),
    path("registration", registrations.new, name="registration"),
    path("passwords/new", passwords.new, name="new_password"),
    path("passwords", passwords.new, name="passwords"),
    path("passwords/<str:token>/edit", passwords.edit, name="edit_password"),
    path("current_accounts", current_accounts.index, name="current_accounts"),
    path("current_accounts.json", current_accounts.index, {"fmt": "json"}, name="current_accounts_json"),
    path("current_accounts/new", current_accounts.new, name="new_current_account"),
    path("current_accounts/<int:pk>", current_accounts.show, name="current_account"),
    path("current_accounts/<int:pk>.json", current_accounts.show, {"fmt": "json"}, name="current_account_json"),
    path("current_accounts/<int:pk>/edit", current_accounts.edit, name="edit_current_account"),
    path("current_accounts/<int:pk>/destroy", current_accounts.destroy, name="destroy_current_account"),
    path("dashboard", dashboards.show, name="dashboard"),
    # Legacy daily balance search, now a filter on the listing
    path("search_account", current_accounts.search_account, name="search_account"),
    path("up", lambda request: HttpResponse("OK"), name="health"),
    path("", current_accounts.index, name="root"),
]
