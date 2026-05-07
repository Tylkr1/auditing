from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    portal_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    users = db.relationship("User", back_populates="company", cascade="all, delete-orphan")
    products = db.relationship("Product", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.name}>"


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("company_id", "email", name="uq_company_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    company = db.relationship("Company", back_populates="users")
    audits = db.relationship("Audit", back_populates="auditor", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    serial_number = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    company = db.relationship("Company", back_populates="products")
    audits = db.relationship("Audit", back_populates="product", cascade="all, delete-orphan", order_by="Audit.audit_date.desc()")

    def __repr__(self):
        return f"<Product {self.name} ({self.serial_number})>"


class Audit(db.Model):
    __tablename__ = "audits"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    auditor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    audit_date = db.Column(db.Date, nullable=False)
    valid_until = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    product = db.relationship("Product", back_populates="audits")
    auditor = db.relationship("User", back_populates="audits")

    def __repr__(self):
        return f"<Audit {self.product.name} on {self.audit_date}>"
