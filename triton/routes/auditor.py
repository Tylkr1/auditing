from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from sqlalchemy import or_, desc
from models import db, Product, Audit, Company, User
from forms import ProductForm, AuditForm
from auth.decorators import login_required, role_required
from services.audit_service import (
    calculate_valid_until, get_remaining_days, get_audit_status,
    get_status_badge_class, is_expired, expires_soon
)
from dateutil.relativedelta import relativedelta
from datetime import datetime

auditor_bp = Blueprint('auditor', __name__, url_prefix='/auditor')


@auditor_bp.route('/dashboard')
@login_required
@role_required('auditor', 'admin', 'superadmin')
def dashboard():
    """Auditor dashboard showing recent audits, expiring audits, and products needing re-audit."""
    user_id = session.get('user_id')
    company_id = session.get('company_id')
    role = session.get('role')

    # Base query for products - auditors see all, others see their company's
    if role in ['superadmin', 'admin']:
        products_query = Product.query
    else:
        products_query = Product.query.filter_by(company_id=company_id)

    # Recent audits (last 10)
    recent_audits = Audit.query.join(Product).filter(
        Product.company_id.in_([p.company_id for p in products_query.all()])
    ).order_by(desc(Audit.created_at)).limit(10).all()

    # Expiring audits (next 30 days)
    today = datetime.utcnow().date()
    expiring_date = today + relativedelta(days=30)
    expiring_audits = Audit.query.join(Product).filter(
        Product.company_id.in_([p.company_id for p in products_query.all()]),
        Audit.valid_until <= expiring_date,
        Audit.valid_until >= today
    ).order_by(Audit.valid_until).all()

    # Products needing re-audit (expired or no audits)
    products_needing_audit = []
    for product in products_query.all():
        if not product.audits or is_expired(product.audits[0].valid_until if product.audits else None):
            products_needing_audit.append(product)

    # Add status info to audits
    for audit in recent_audits + expiring_audits:
        audit.status = get_audit_status(audit.valid_until)
        audit.remaining_days = get_remaining_days(audit.valid_until)
        audit.status_badge = get_status_badge_class(audit.status)

    return render_template('auditor/dashboard.html',
                         recent_audits=recent_audits,
                         expiring_audits=expiring_audits,
                         products_needing_audit=products_needing_audit)


@auditor_bp.route('/products')
@login_required
@role_required('auditor', 'admin', 'superadmin')
def products():
    """List all products with search and filter."""
    role = session.get('role')
    company_id = session.get('company_id')

    # Base query
    query = Product.query

    if role not in ['superadmin', 'admin']:
        query = query.filter_by(company_id=company_id)

    # Search functionality
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            or_(Product.name.ilike(f'%{search}%'),
                Product.serial_number.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%'))
        )

    # Company filter for superadmin/admin
    company_filter = request.args.get('company', type=int)
    if company_filter and role in ['superadmin', 'admin']:
        query = query.filter_by(company_id=company_filter)

    products_list = query.order_by(Product.created_at.desc()).all()

    # Add latest audit info
    for product in products_list:
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

    companies = Company.query.all() if role in ['superadmin', 'admin'] else []

    return render_template('auditor/products.html',
                         products=products_list,
                         companies=companies,
                         search=search,
                         selected_company=company_filter)


@auditor_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('auditor', 'admin', 'superadmin')
def create_product():
    """Create a new product."""
    form = ProductForm()
    role = session.get('role')
    company_id = session.get('company_id')

    # Restrict company choices based on role
    if role not in ['superadmin', 'admin']:
        form.company_id.choices = [(company_id, session.get('company_name'))]
        form.company_id.data = company_id

    if form.validate_on_submit():
        product = Product(
            company_id=form.company_id.data,
            name=form.name.data,
            serial_number=form.serial_number.data,
            description=form.description.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created successfully!', 'success')
        return redirect(url_for('auditor.products'))

    return render_template('auditor/create_product.html', form=form)


@auditor_bp.route('/audits/create', methods=['GET', 'POST'])
@login_required
@role_required('auditor', 'admin', 'superadmin')
def create_audit():
    """Create a new audit for a product."""
    form = AuditForm()
    role = session.get('role')
    company_id = session.get('company_id')

    # Populate product choices based on role
    products_query = Product.query
    if role not in ['superadmin', 'admin']:
        products_query = products_query.filter_by(company_id=company_id)

    form.product_id.choices = [(p.id, f"{p.name} ({p.serial_number})") for p in products_query.all()]

    if form.validate_on_submit():
        valid_until = calculate_valid_until(form.audit_date.data, form.duration_months.data)

        audit = Audit(
            product_id=form.product_id.data,
            auditor_id=session.get('user_id'),
            audit_date=form.audit_date.data,
            valid_until=valid_until,
            notes=form.notes.data
        )
        db.session.add(audit)
        db.session.commit()
        flash('Audit created successfully!', 'success')
        return redirect(url_for('auditor.dashboard'))

    return render_template('auditor/create_audit.html', form=form)


@auditor_bp.route('/audits/<int:audit_id>')
@login_required
@role_required('auditor', 'admin', 'superadmin')
def audit_detail(audit_id):
    """View audit details."""
    role = session.get('role')
    company_id = session.get('company_id')

    audit = Audit.query.get_or_404(audit_id)

    # Check permissions
    if role not in ['superadmin', 'admin'] and audit.product.company_id != company_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('auditor.dashboard'))

    audit.status = get_audit_status(audit.valid_until)
    audit.remaining_days = get_remaining_days(audit.valid_until)
    audit.status_badge = get_status_badge_class(audit.status)

    return render_template('auditor/audit_detail.html', audit=audit)