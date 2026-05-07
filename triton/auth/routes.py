from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf.csrf import generate_csrf

from models import db, Company, User
from forms import LoginForm, SignupForm
from auth.decorators import login_required, role_required

auth_bp = Blueprint("auth", __name__)

CREATEABLE_ROLES = {"admin", "auditor", "employee"}
ROLE_REDIRECTS = {
    "superadmin": "/superadmin-dashboard",
    "admin": "/company/dashboard",
    "auditor": "/auditor/dashboard",
    "employee": "/company/dashboard",
}


@auth_bp.route("/login", methods=["GET"])
def login():
    form = LoginForm()
    return render_template("login.html", form=form)


@auth_bp.route("/login", methods=["POST"])
def login_post():
    form = LoginForm()
    if form.validate_on_submit():
        portal_id = form.portal_id.data.strip().lower()
        email = form.email.data.strip().lower()
        password = form.password.data

        company = Company.query.filter_by(portal_id=portal_id).first()
        if not company:
            flash("Invalid portal ID or credentials.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email, company_id=company.id).first()
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        session.clear()
        session["user_id"] = user.id
        session["company_id"] = user.company_id
        session["company_name"] = company.name
        session["portal_id"] = company.portal_id
        session["role"] = user.role

        return redirect(ROLE_REDIRECTS.get(user.role, url_for("auth.login")))

    return render_template("login.html", form=form)


@auth_bp.route("/signup", methods=["GET"])
@login_required
@role_required("admin")
def signup():
    form = SignupForm()
    return render_template("signup.html", form=form)


@auth_bp.route("/signup", methods=["POST"])
@login_required
@role_required("admin")
def signup_post():
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        role = form.role.data

        company_id = session.get("company_id")
        if not company_id:
            flash("Unable to determine your company.", "danger")
            return redirect(url_for("auth.login"))

        existing_user = User.query.filter_by(email=email, company_id=company_id).first()
        if existing_user:
            flash("That email is already in use for your company.", "warning")
            return redirect(url_for("auth.signup"))

        new_user = User(
            email=email,
            role=role,
            company_id=company_id,
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash(f"User {email} created successfully.", "success")
        return redirect(url_for("auth.signup"))

    return render_template("signup.html", form=form)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
