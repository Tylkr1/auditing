from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, IntegerField, EmailField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from models import Company, User


class LoginForm(FlaskForm):
    portal_id = StringField('Portal ID', validators=[DataRequired(), Length(min=1, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class SignupForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    role = SelectField('Role', validators=[DataRequired()], choices=[
        ('admin', 'Admin'),
        ('auditor', 'Auditor'),
        ('employee', 'Employee')
    ])


class ProductForm(FlaskForm):
    company_id = SelectField('Company', validators=[DataRequired()], coerce=int)
    name = StringField('Product Name', validators=[DataRequired(), Length(min=1, max=255)])
    serial_number = StringField('Serial Number', validators=[DataRequired(), Length(min=1, max=255)])
    description = TextAreaField('Description', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate company choices - only for auditors/admins
        self.company_id.choices = [(c.id, c.name) for c in Company.query.all()]


class AuditForm(FlaskForm):
    product_id = SelectField('Product', validators=[DataRequired()], coerce=int)
    audit_date = DateField('Audit Date', validators=[DataRequired()])
    duration_months = IntegerField('Duration (Months)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    notes = TextAreaField('Notes', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate product choices based on user's permissions
        # This will be set in the route based on user role
        self.product_id.choices = []