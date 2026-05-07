from flask import Blueprint, render_template, session, flash, redirect, url_for
from models import Product, Audit
from auth.decorators import login_required, role_required
from services.audit_service import get_remaining_days, get_audit_status, get_status_badge_class

company_bp = Blueprint('company', __name__, url_prefix='/company')


@company_bp.route('/dashboard')
@login_required
@role_required('admin', 'auditor', 'employee')
def dashboard():
    """Company dashboard showing their products and audit status."""
    company_id = session.get('company_id')

    # Get all products for this company
    products = Product.query.filter_by(company_id=company_id).order_by(Product.name).all()

    # Add audit status information
    for product in products:
        if product.audits:
            latest_audit = product.audits[0]  # Already ordered by audit_date desc
            product.latest_audit = latest_audit
            product.status = get_audit_status(latest_audit.valid_until)
            product.remaining_days = get_remaining_days(latest_audit.valid_until)
            product.status_badge = get_status_badge_class(product.status)
        else:
            product.latest_audit = None
            product.status = 'no_audit'
            product.remaining_days = None
            product.status_badge = 'badge bg-secondary'

    return render_template('company/dashboard.html', products=products)


@company_bp.route('/products/<int:product_id>')
@login_required
@role_required('admin', 'auditor', 'employee')
def product_detail(product_id):
    """View product details and audit history."""
    company_id = session.get('company_id')

    product = Product.query.filter_by(id=product_id, company_id=company_id).first_or_404()

    # Add status to each audit
    for audit in product.audits:
        audit.status = get_audit_status(audit.valid_until)
        audit.remaining_days = get_remaining_days(audit.valid_until)
        audit.status_badge = get_status_badge_class(audit.status)

    return render_template('company/product_detail.html', product=product)