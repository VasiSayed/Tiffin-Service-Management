#!/bin/bash

# Tiffin Project Quick Setup Script

echo "================================"
echo "Tiffin Project Quick Setup"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Dependencies installed"

# Run migrations
echo "Setting up database..."
python manage.py makemigrations
python manage.py migrate

echo "✓ Database setup complete"

# Create superuser prompt
echo ""
echo "Now you need to create a superuser account."
echo "This will be your admin login."
echo ""
python manage.py createsuperuser

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Run: python manage.py runserver"
echo "2. Visit: http://localhost:8000/admin"
echo "3. Create a Tenant and link your user via UserProfile"
echo "4. Login at: http://localhost:8000/login"
echo ""
echo "Enjoy your Tiffin Service Management System!"
echo ""
