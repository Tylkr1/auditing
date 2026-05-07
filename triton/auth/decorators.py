from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id") or not session.get("company_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            role = session.get("role")
            if role not in allowed_roles:
                flash("You do not have permission to view that page.", "danger")
                return redirect(url_for("auth.login"))

            return view(*args, **kwargs)

        return wrapped_view

    return decorator
