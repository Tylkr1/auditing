from datetime import datetime
from dateutil.relativedelta import relativedelta
from models import Audit


def calculate_valid_until(audit_date, duration_months):
    """Calculate the valid_until date based on audit_date and duration in months."""
    return audit_date + relativedelta(months=duration_months)


def get_remaining_days(valid_until):
    """Calculate remaining days until expiration."""
    if valid_until is None:
        return None
    today = datetime.utcnow().date()
    return (valid_until - today).days


def is_expired(valid_until):
    """Check if an audit is expired."""
    remaining = get_remaining_days(valid_until)
    return remaining is not None and remaining < 0


def expires_soon(valid_until, days=30):
    """Check if an audit expires within the specified number of days."""
    remaining = get_remaining_days(valid_until)
    return remaining is not None and 0 <= remaining <= days


def get_audit_status(valid_until):
    """Get the status of an audit: 'expired', 'expiring', 'valid'."""
    if is_expired(valid_until):
        return 'expired'
    elif expires_soon(valid_until):
        return 'expiring'
    else:
        return 'valid'


def get_status_badge_class(status):
    """Get Bootstrap badge class for audit status."""
    status_classes = {
        'expired': 'badge bg-danger',
        'expiring': 'badge bg-warning text-dark',
        'valid': 'badge bg-success'
    }
    return status_classes.get(status, 'badge bg-secondary')


def get_status_color(status):
    """Get color for status display."""
    status_colors = {
        'expired': '#dc3545',  # red
        'expiring': '#ffc107',  # yellow
        'valid': '#28a745'  # green
    }
    return status_colors.get(status, '#6c757d')  # gray