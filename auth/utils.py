# auth/utils.py

from flask import current_app, session, redirect, url_for
from functools import wraps

def check_credentials(email: str, password: str):
    """
    Stub credential checker: returns a simple user-like object
    if the provided password matches the shared API_TOKEN in config.
    """
    token = current_app.config.get("API_TOKEN")
    if password == token:
        # Return a dummy user object with id and role
        return type("User", (), {"id": 1, "role": "admin"})()
    return None

def login_required(view):
    """
    Decorator that redirects to the login page if no user_id in session.
    """
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped
