# Tiffin Service Management System

A comprehensive multi-tenant Django web application for managing tiffin (lunch box) delivery services with role-based access, daily order management, sticker printing, and payment tracking.

## Features

### Multi-Tenant Support
- Each client has their own tenant with custom branding (logo, colors)
- Automatic fallback to system defaults when tenant branding is not configured
- Separate data isolation per tenant

### Role-Based Access Control
- **ADMIN**: Full access to all features
  - Dashboard with key metrics
  - Customer management
  - Dish and portion management
  - Meal template configuration
  - Daily order entry
  - Sticker printing
  - Payment tracking
  - Comprehensive reports

- **MANAGER**: Limited access for daily operations
  - Daily order entry
  - Sticker printing
  - View-only access to dishes

### Core Functionality

#### 1. Customer Management
- Add, edit, delete customers
- Track contact information and delivery locations
- Active/inactive status management

#### 2. Dish Management
- Categorized dishes (Bhaji, Dal, Rice, Chapati, Other)
- Meal category assignment (Lunch/Dinner/Both)
- Food type classification (Veg/Non-Veg)
- Availability tracking
- Portion management with sizes and pricing

#### 3. Meal Templates
- Pre-configured meal packages (₹45, ₹50, ₹80, ₹90, ₹100)
- Template items that auto-populate orders
- Customizable "show bhaji on sticker" option
- Default quantities for each dish in the meal

#### 4. Daily Entry System
- Date and meal type (Lunch/Dinner) based orders
- Quick order creation by selecting customer
- Add multiple meals to an order
- Customize items per meal (add/remove/modify)
- Support for manual dish names
- Real-time total calculation

#### 5. Print Stickers
- Generate delivery stickers with customer info
- Configurable layout (8/10/12 stickers per page)
- Conditional bhaji display based on meal configuration
- Custom colors for lunch vs dinner stickers
- Print-optimized CSS

#### 6. Payment Management
- Monthly payment tracking
- Customer-wise raised vs received amounts
- Outstanding balance calculation
- Multiple payment methods (Cash/UPI/Bank)
- Payment history per customer

#### 7. Reports & Analytics
- Date range based reporting
- Total orders and revenue
- Lunch vs Dinner breakdown
- Top customers by spending
- Outstanding amount tracking

## Technology Stack

- **Backend**: Django 5.0 (Python)
- **Frontend**: Django Templates (HTML), Vanilla JavaScript, CSS3
- **Database**: SQLite (easily switchable to PostgreSQL/MySQL)
- **Styling**: Custom CSS with modern design patterns

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Extract and Navigate
```bash
unzip tiffin_project.zip
cd tiffin_project
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Create Superuser
```bash
python manage.py createsuperuser
```
Follow the prompts to create an admin account.

### Step 6: Create Initial Data

Access Django admin at http://localhost:8000/admin/ and create:

1. **Tenant**: Your business/client tenant with branding
2. **UserProfile**: Link your superuser to the tenant with ADMIN role
3. **(Optional)** Create sample customers, dishes, and meals

### Step 7: Run Development Server
```bash
python manage.py runserver
```

Visit http://localhost:8000/ to access the application.

## Default Credentials

After creating a superuser, you can log in at:
- URL: http://localhost:8000/login
- Username: (your superuser username)
- Password: (your superuser password)

## Project Structure

```
tiffin_project/
├── tiffin_project/          # Django project settings
│   ├── settings.py          # Main configuration
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI configuration
├── tiffin_app/              # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View logic
│   ├── urls.py              # App URL patterns
│   ├── admin.py             # Django admin configuration
│   ├── context_processors.py  # Template context processors
│   └── migrations/          # Database migrations
├── templates/               # HTML templates
│   └── tiffin_app/
│       ├── base.html        # Base template
│       ├── login.html       # Login page
│       ├── dashboard.html   # Admin dashboard
│       ├── customers/       # Customer templates
│       ├── dishes/          # Dish templates
│       ├── meals/           # Meal templates
│       ├── daily_entry/     # Daily entry templates
│       ├── payments/        # Payment templates
│       └── reports/         # Report templates
├── static/                  # Static files
│   └── tiffin_app/
│       ├── css/
│       │   └── style.css    # Main stylesheet
│       ├── js/
│       │   └── main.js      # JavaScript functions
│       └── img/
│           └── default_logo.png
├── manage.py                # Django management script
└── requirements.txt         # Python dependencies
```

## Usage Guide

### For Admins

1. **Setup Master Data**:
   - Add customers with delivery locations
   - Create dishes with categories and portions
   - Configure meal templates with default items

2. **Daily Operations**:
   - Navigate to "Daily Entry"
   - Select date and meal type (Lunch/Dinner)
   - Create orders for customers
   - Add meals and customize items as needed

3. **Print Stickers**:
   - Go to "Print Stickers"
   - Select date, meal type, and layout
   - Click "Generate" then "Print"

4. **Manage Payments**:
   - Access "Payments" dashboard
   - View monthly summaries
   - Record payments from customers

5. **View Reports**:
   - Use "Reports" to analyze business metrics
   - Filter by date range
   - View top customers and revenue breakdown

### For Managers

1. **Daily Order Entry**:
   - Login redirects to Daily Entry
   - Create and manage orders for the day

2. **Print Stickers**:
   - Access from navigation
   - Generate stickers for delivery

3. **View Dishes** (Read-only):
   - Reference dish information and portions

## Customization

### Tenant Branding

In Django admin, configure tenant with:
- **Logo**: Upload custom logo image
- **Primary Color**: Main brand color (hex format, e.g., #2c3e50)
- **Lunch Sticker Color**: Background color for lunch stickers
- **Dinner Sticker Color**: Background color for dinner stickers

If not set, system uses default values.

### Meal Configuration

Create meal templates that match your pricing:
- Set price (₹45, ₹50, ₹80, ₹90, ₹100, etc.)
- Add default items (dishes with portions)
- Configure whether to show bhaji names on stickers

### Sticker Customization

Modify `/static/tiffin_app/css/style.css` under `.sticker` classes to:
- Change layout and sizing
- Adjust fonts and colors
- Customize print appearance

## Database Models

### Core Models
- **Tenant**: Business/client configuration
- **UserProfile**: User role and tenant association
- **Customer**: Customer information
- **Dish**: Food items with categories
- **DishPortion**: Size variants for dishes
- **Meal**: Meal packages with pricing
- **MealDishPortion**: Template items for meals
- **DailyEntry**: Orders by date and meal type
- **OrderMeal**: Meals in an order
- **OrderMealCustom**: Customized items per meal
- **Payment**: Payment records

## Security Notes

**Important for Production**:

1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Configure `ALLOWED_HOSTS`
4. Use PostgreSQL/MySQL instead of SQLite
5. Set up proper media file serving
6. Enable HTTPS
7. Configure email backend for notifications

## Troubleshooting

### Static Files Not Loading
```bash
python manage.py collectstatic
```

### Database Issues
```bash
python manage.py migrate --run-syncdb
```

### Permission Denied
Ensure user has UserProfile linked to a tenant with appropriate role.

## Support & Contribution

This is a template project. Customize according to your business requirements.

## License

This project is provided as-is for educational and commercial use.

## Version

1.0.0 - Initial Release

---

**Built with Django Templates + Vanilla JS + Clean CSS**

No heavy frameworks, just clean, maintainable code that works.
