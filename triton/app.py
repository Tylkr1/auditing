from flask import Flask, render_template, redirect, url_for, flash, session
from dotenv import load_dotenv
import os
from models import db
from auth.routes import auth_bp
from routes.auditor import auditor_bp
from routes.company import company_bp
from auth.decorators import login_required, role_required

load_dotenv()

ROLE_REDIRECTS = {
    "superadmin": "/superadmin-dashboard",
    "admin": "/company/dashboard",
    "auditor": "/auditor/dashboard",
    "employee": "/company/dashboard",
}


def create_app(config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI="sqlite:///triton.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_SECRET_KEY=os.getenv("SECRET_KEY"),  # Use same key for CSRF
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(auditor_bp)
    app.register_blueprint(company_bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the database and create tables."""
        with app.app_context():
            db.create_all()
            print("Database initialized.")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed the database with initial data."""
        from models import Company, User
        with app.app_context():
            # Create initial company if it doesn't exist
            company = Company.query.filter_by(portal_id="platform").first()
            if not company:
                company = Company(name="Platform", portal_id="platform")
                db.session.add(company)
                db.session.flush()

            # Create superadmin user if it doesn't exist
            user = User.query.filter_by(email="owner@example.com").first()
            if not user:
                user = User(company_id=company.id, email="owner@example.com", role="superadmin")
                user.set_password("SuperSecurePassword123")
                db.session.add(user)

            db.session.commit()
            print("Database seeded with initial company and superadmin user.")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/superadmin-dashboard")
    @login_required
    @role_required("superadmin")
    def superadmin_dashboard():
        return render_template(
            "dashboard.html",
            title="Superadmin Dashboard",
            role=session.get("role"),
            company_name=session.get("company_name"),
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
