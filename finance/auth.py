"""Authentication like Rails 8's generator: a signed "session_id" cookie pointing to a row in `sessions`."""

from functools import wraps

from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect

from .models import Session

COOKIE = "session_id"
COOKIE_SALT = "session_id"
PERMANENT = 20 * 365 * 24 * 60 * 60  # cookies.permanent


class AuthenticationMiddleware:
    """Loads the session and user for the signed cookie into request.current_session / request.current_user."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_id = request.get_signed_cookie(COOKIE, default=None, salt=COOKIE_SALT)
        session = Session.objects.select_related("user").filter(pk=session_id).first() if session_id else None
        request.current_session = session
        request.current_user = session.user if session else None
        request.cookies_to_set = []
        response = self.get_response(request)
        for action, args in request.cookies_to_set:
            getattr(response, action)(*args[0], **args[1])
        return response


def start_new_session_for(request, user):
    session = Session.objects.create(
        user=user, user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255], ip_address=request.META.get("REMOTE_ADDR")
    )
    request.current_session, request.current_user = session, user
    request.cookies_to_set.append(
        (
            "set_signed_cookie",
            ((COOKIE, session.pk), {"salt": COOKIE_SALT, "max_age": PERMANENT, "httponly": True, "samesite": "Lax"}),
        )
    )
    return session


def terminate_session(request):
    if request.current_session:
        request.current_session.delete()
    request.current_session = request.current_user = None
    request.cookies_to_set.append(("delete_cookie", ((COOKIE,), {"samesite": "Lax"})))


def require_authentication(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.current_user is None:
            request.cookies_to_set.append(
                (
                    "set_signed_cookie",
                    (("return_to", request.build_absolute_uri()), {"salt": "return_to", "httponly": True, "samesite": "Lax"}),
                )
            )
            return redirect("new_session")
        return view(request, *args, **kwargs)

    return wrapper


def after_authentication_url(request):
    url = request.get_signed_cookie("return_to", default=None, salt="return_to")
    if url:
        request.cookies_to_set.append(("delete_cookie", (("return_to",), {"samesite": "Lax"})))
    return url or "/"


def rate_limit(name, to=10, within=180, redirect_to=None):
    """Like Rails `rate_limit to: 10, within: 3.minutes`: counts requests per IP in the cache."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method == "POST":
                key = f"rate-limit:{name}:{request.META.get('REMOTE_ADDR')}"
                if cache.add(key, 1, within) is False and cache.incr(key) > to:
                    messages.error(request, "Tente novamente mais tarde.")
                    return redirect(redirect_to)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def context(request):
    user = getattr(request, "current_user", None)
    return {"authenticated": user is not None, "current_user": user}
