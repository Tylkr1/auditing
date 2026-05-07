# Triton Auditing Management System

A professional auditing platform built with Flask, SQLAlchemy, and Bootstrap for managing product audits and compliance tracking.

## Features

### Auditor Portal
- Create and manage products for companies
- Schedule and conduct audits with automatic expiration calculation
- Dashboard with audit status overview, expiring audits, and products needing re-audit
- Search and filter products
- Comprehensive audit history

### Company Portal
- View all products and their audit status
- Real-time status indicators (Valid, Expiring, Expired)
- Detailed audit history per product
- Secure access limited to company's own data

### Security Features
- CSRF protection with Flask-WTF
- Role-based access control (superadmin, admin, auditor, employee)
- Portal ID authentication system
- Secure password hashing
- Input validation and sanitization

## Technology Stack

- **Backend**: Flask 2.3.3, SQLAlchemy 3.0.5
- **Frontend**: Bootstrap 5.1.3, Jinja2 templates
- **Security**: Flask-WTF 1.1.1, Werkzeug security
- **Database**: SQLite (development), PostgreSQL (production recommended)
- **Date Handling**: python-dateutil for audit expiration logic

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.8 or higher** - Download from [python.org](https://python.org)
- **Git** - Download from [git-scm.com](https://git-scm.com)
- **Virtual Environment** (recommended) - Python's built-in `venv` module

## Installation

### 1. Clone the Repository

Open your terminal/command prompt and navigate to where you want to store the project:

```bash
# Navigate to your desired directory
cd /path/to/your/projects

# Clone the repository
git clone https://github.com/yourusername/triton-auditing.git

# Navigate into the project directory
cd triton-auditing
```

Replace `yourusername` with the actual GitHub username and repository name.

### 2. Create a Virtual Environment

Create and activate a Python virtual environment to isolate dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` at the beginning of your command prompt after activation.

### 3. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- Flask and Flask extensions
- SQLAlchemy for database operations
- Flask-WTF for form handling and CSRF protection
- python-dotenv for environment variable management
- python-dateutil for date calculations

### 4. Environment Configuration

Create a `.env` file in the root directory for sensitive configuration:

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` to set your secret key:

```env
# Generate a secure random secret key
SECRET_KEY=your-super-secure-random-secret-key-here-change-this-in-production
```

**Important**: Never commit your `.env` file to version control. It's already in `.gitignore`.

### 5. Database Setup

Initialize and seed the database:

```bash
# Initialize database tables
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import db; db.create_all(); print('Database initialized')"

# Seed with initial data (creates platform company and superadmin)
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from models import Company, User, db
    company = Company(name='Platform', portal_id='platform')
    db.session.add(company)
    db.session.flush()
    user = User(company_id=company.id, email='owner@example.com', role='superadmin')
    user.set_password('SuperSecurePassword123')
    db.session.add(user)
    db.session.commit()
    print('Database seeded successfully')
"
```

### 6. Run the Application

Start the development server:

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000/`

## Database Models

### Company
- `portal_id`: Unique identifier for login (string, indexed, required)
- `name`: Company display name
- `created_at`: Timestamp of creation
- Relationships: Users, Products

### User
- `email`: User email address (unique per company)
- `password_hash`: Securely hashed password
- `role`: User role (superadmin, admin, auditor, employee)
- `created_at`: Timestamp of creation
- Relationships: Company, Audits (for auditors)

### Product
- `name`: Product name
- `serial_number`: Unique product identifier
- `description`: Optional product description
- `created_at`: Timestamp of creation
- Relationships: Company, Audits

### Audit
- `audit_date`: Date when audit was performed
- `valid_until`: Expiration date of the audit
- `notes`: Optional audit notes/comments
- `created_at`: Timestamp of creation
- Relationships: Product, Auditor (User)

## Authentication

Users authenticate using a three-factor system:
- **Portal ID**: Company identifier (e.g., "acme-corp")
- **Email**: User email address
- **Password**: Secure password

### User Roles

- **superadmin**: Full system access, can manage all companies
- **admin**: Company administration, user management, auditing
- **auditor**: Product and audit management within assigned scope
- **employee**: Read-only access to company's product audit status

## Audit Logic

### Expiration Calculation
- Valid until date calculated using `dateutil.relativedelta(months=duration)`
- Example: Audit on 2024-01-15 with 12 months duration → Valid until 2025-01-15

### Status Determination
Status is calculated dynamically (not stored in database):
- **Valid**: `valid_until > today`
- **Expiring**: `today < valid_until <= today + 30 days`
- **Expired**: `valid_until <= today`

### Remaining Days
- Calculated as: `(valid_until - datetime.utcnow().date()).days`
- Negative values indicate expired audits

## API Endpoints

### Authentication Routes
- `GET/POST /login` - User login with portal ID
- `GET/POST /signup` - Create new users (admin only)
- `POST /logout` - User logout

### Auditor Routes (`/auditor`)
- `GET /dashboard` - Auditor dashboard with overview
- `GET/POST /products/create` - Create new product
- `GET /products` - List/search/filter products
- `GET/POST /audits/create` - Create new audit
- `GET /audits/<id>` - View detailed audit information

### Company Routes (`/company`)
- `GET /dashboard` - Company product overview
- `GET /products/<id>` - Product audit history

## Project Structure

```
triton/
├── app.py                 # Main Flask application and configuration
├── models.py             # SQLAlchemy database models
├── requirements.txt      # Python dependencies
├── README.md             # This documentation
├── .env.example          # Environment variables template
├── forms/                # WTForms form definitions
│   └── __init__.py      # Login, signup, product, audit forms
├── routes/               # Flask blueprints
│   ├── auditor.py       # Auditor portal routes
│   └── company.py       # Company portal routes
├── services/             # Business logic services
│   └── audit_service.py # Audit expiration and status calculations
├── templates/            # Jinja2 HTML templates
│   ├── base.html        # Base template with Bootstrap
│   ├── index.html       # Landing page
│   ├── login.html       # Login form
│   ├── signup.html      # User creation form
│   ├── auditor/         # Auditor portal templates
│   └── company/         # Company portal templates
├── static/               # Static assets
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── auth/                 # Authentication system
│   ├── __init__.py      # Empty
│   ├── routes.py        # Auth routes (login/signup/logout)
│   └── decorators.py    # login_required, role_required decorators
└── instance/             # Database files (auto-generated)
    └── triton.db        # SQLite database
```

## Usage Guide

### First Login
After setup, use these credentials to access the system:

- **Portal ID**: `platform`
- **Email**: `owner@example.com`
- **Password**: `SuperSecurePassword123`
- **Role**: `superadmin`

### Creating Companies and Users
1. Log in as superadmin
2. Use the signup form to create admin users for new companies
3. Admins can then create additional users (auditors, employees) for their company

### Auditor Workflow
1. **Create Products**: Add products for companies with name, serial number, description
2. **Schedule Audits**: Select products, set audit date and duration
3. **Monitor Status**: Use dashboard to track expiring and expired audits
4. **Search & Filter**: Find products by name, serial, or company

### Company Portal
1. **View Products**: See all company products with current audit status
2. **Status Indicators**:
   - 🟢 Green: Valid audit
   - 🟡 Yellow: Expires within 30 days
   - 🔴 Red: Expired audit
3. **Audit History**: Click products to see complete audit timeline

## Development

### Adding New Features
1. Define database models in `models.py`
2. Create WTForms in `forms/__init__.py`
3. Add routes in appropriate blueprint (`routes/`)
4. Create Jinja2 templates in `templates/`
5. Update navigation in `base.html` if needed

### Database Migrations
For production deployments, use Flask-Migrate:

```bash
pip install flask-migrate
flask db init
flask db migrate -m "Add new feature"
flask db upgrade
```

### Testing
Run the application and test all user roles:
- Create products and audits as auditor
- View company portal as employee
- Test search and filter functionality
- Verify authorization restrictions

## Security Considerations

### Production Deployment
- Use HTTPS with SSL certificates
- Set strong, unique `SECRET_KEY`
- Use PostgreSQL instead of SQLite
- Implement rate limiting
- Add session timeout configuration
- Regular security audits

### Password Policies
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, symbols
- No common passwords
- Regular password rotation

### Access Control
- Principle of least privilege
- Regular review of user roles
- Audit logging for sensitive operations
- Secure session management

## Troubleshooting

### Common Issues

**Database Errors**
```bash
# Reset database
rm instance/triton.db
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app import db; db.create_all()"
```

**Import Errors**
- Ensure virtual environment is activated
- Check `pip list` shows all required packages
- Verify Python version compatibility

**Template Errors**
- Check Jinja2 syntax in templates
- Verify Bootstrap CDN connectivity
- Clear browser cache

**Authentication Issues**
- Verify portal ID matches database exactly
- Check user role permissions
- Clear session cookies if needed

### Getting Help
- Check Flask and SQLAlchemy documentation
- Review error logs in terminal
- Test with default superadmin credentials
- Verify all prerequisites are installed

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit changes: `git commit -am 'Add feature'`
5. Push to branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is provided as-is for educational and development purposes. See LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release with complete auditing management system
- Multi-tenant company support
- Role-based access control
- Bootstrap responsive UI
- CSRF protection and validation
- Dynamic audit expiration logic
