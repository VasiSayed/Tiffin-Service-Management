#!/usr/bin/env python
"""
Generate dummy data for Tiffin App testing
Run: python manage.py shell < create_dummy_data.py
"""

from django.contrib.auth.models import User
from tiffin_app.models import (
    Tenant, UserProfile, Customer, Dish, DishPortion, 
    Meal, MealTemplateItem, DailyEntry, DailyEntryItem, Payment
)
from datetime import date, timedelta
from decimal import Decimal

print("🔧 Creating dummy data for testing...")

# Get or create tenant
tenant, created = Tenant.objects.get_or_create(
    name='Demo Tiffin Service',
    defaults={
        'primary_color': '#dc2626',
        'secondary_color': '#f59e0b',
        'lunch_sticker_color': '#ef4444',
        'dinner_sticker_color': '#991b1b',
    }
)
print(f"✓ Tenant: {tenant.name}")

# Get or create admin user
user, created = User.objects.get_or_create(
    username='demo_admin',
    defaults={
        'email': 'admin@demo.com',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    user.set_password('demo123')
    user.save()
    print(f"✓ User created: demo_admin / demo123")
else:
    print(f"✓ User exists: demo_admin")

# Create user profile
profile, created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'tenant': tenant, 'role': 'ADMIN'}
)

# Create customers
customers_data = [
    {'name': 'Rajesh Kumar', 'phone': '9876543210', 'location': 'Andheri East, Mumbai', 'address': 'Flat 402, Sunshine Apartments'},
    {'name': 'Priya Sharma', 'phone': '9876543211', 'location': 'Bandra West, Mumbai', 'address': 'Villa 12, Palm Grove'},
    {'name': 'Amit Patel', 'phone': '9876543212', 'location': 'Powai, Mumbai', 'address': 'Tower B-503, Hiranandani'},
    {'name': 'Sneha Desai', 'phone': '9876543213', 'location': 'Malad West, Mumbai', 'address': '201, Orchid Complex'},
    {'name': 'Vikram Singh', 'phone': '9876543214', 'location': 'Goregaon East, Mumbai', 'address': 'Bungalow 5, Green Park'},
]

customers = []
for data in customers_data:
    customer, created = Customer.objects.get_or_create(
        tenant=tenant,
        phone=data['phone'],
        defaults={
            'name': data['name'],
            'delivery_location': data['location'],
            'address': data['address'],
            'is_active': True
        }
    )
    customers.append(customer)
print(f"✓ Created {len(customers)} customers")

# Create dishes
dishes_data = [
    # BHAJI
    {'name': 'Paneer Butter Masala', 'category': 'BHAJI', 'price': 120},
    {'name': 'Aloo Gobi', 'category': 'BHAJI', 'price': 80},
    {'name': 'Dal Tadka', 'category': 'BHAJI', 'price': 70},
    {'name': 'Palak Paneer', 'category': 'BHAJI', 'price': 110},
    {'name': 'Mix Veg', 'category': 'BHAJI', 'price': 90},
    {'name': 'Chana Masala', 'category': 'BHAJI', 'price': 85},
    
    # ROTI
    {'name': 'Chapati', 'category': 'ROTI', 'price': 8},
    {'name': 'Phulka', 'category': 'ROTI', 'price': 10},
    {'name': 'Paratha', 'category': 'ROTI', 'price': 15},
    
    # RICE
    {'name': 'Jeera Rice', 'category': 'RICE', 'price': 60},
    {'name': 'Plain Rice', 'category': 'RICE', 'price': 50},
    {'name': 'Veg Pulao', 'category': 'RICE', 'price': 80},
    
    # EXTRA
    {'name': 'Papad', 'category': 'EXTRA', 'price': 5},
    {'name': 'Pickle', 'category': 'EXTRA', 'price': 10},
    {'name': 'Salad', 'category': 'EXTRA', 'price': 20},
]

dishes = []
for data in dishes_data:
    dish, created = Dish.objects.get_or_create(
        tenant=tenant,
        name=data['name'],
        category=data['category'],
        defaults={'base_price': data['price']}
    )
    dishes.append(dish)
print(f"✓ Created {len(dishes)} dishes")

# Create meals
lunch_meal, created = Meal.objects.get_or_create(
    tenant=tenant,
    name='Standard Lunch',
    meal_type='LUNCH',
    defaults={
        'price': 150,
        'show_bhaji_on_sticker': True,
        'is_active': True
    }
)

dinner_meal, created = Meal.objects.get_or_create(
    tenant=tenant,
    name='Standard Dinner',
    meal_type='DINNER',
    defaults={
        'price': 140,
        'show_bhaji_on_sticker': True,
        'is_active': True
    }
)
print(f"✓ Created meals: {lunch_meal.name}, {dinner_meal.name}")

# Add template items to lunch
bhaji_dishes = [d for d in dishes if d.category == 'BHAJI'][:3]
roti_dish = next((d for d in dishes if d.name == 'Chapati'), None)
rice_dish = next((d for d in dishes if d.name == 'Jeera Rice'), None)

if roti_dish:
    MealTemplateItem.objects.get_or_create(
        meal=lunch_meal,
        dish=roti_dish,
        defaults={'default_qty': 4}
    )

if rice_dish:
    MealTemplateItem.objects.get_or_create(
        meal=lunch_meal,
        dish=rice_dish,
        defaults={'default_qty': 1}
    )

for bhaji in bhaji_dishes:
    MealTemplateItem.objects.get_or_create(
        meal=lunch_meal,
        dish=bhaji,
        defaults={'default_qty': 1}
    )

print(f"✓ Added template items to {lunch_meal.name}")

# Create daily entries for today
today = date.today()

for customer in customers[:3]:  # First 3 customers get lunch
    entry, created = DailyEntry.objects.get_or_create(
        tenant=tenant,
        customer=customer,
        date=today,
        meal_type='LUNCH',
        defaults={
            'meal': lunch_meal,
            'base_amount': lunch_meal.price,
            'total_amount': lunch_meal.price,
            'status': 'DELIVERED'
        }
    )
    
    # Add items
    if created:
        for item in lunch_meal.template_items.all():
            DailyEntryItem.objects.create(
                daily_entry=entry,
                dish=item.dish,
                quantity=item.default_qty,
                item_price=item.dish.base_price,
                total_price=item.dish.base_price * item.default_qty
            )

print(f"✓ Created {DailyEntry.objects.filter(date=today).count()} daily entries for today")

# Create a payment
if customers:
    payment, created = Payment.objects.get_or_create(
        tenant=tenant,
        customer=customers[0],
        date=today,
        defaults={
            'amount': Decimal('1500.00'),
            'payment_method': 'CASH',
            'notes': 'Monthly advance payment'
        }
    )
    if created:
        print(f"✓ Created payment for {customers[0].name}")

print("\n✅ Dummy data created successfully!")
print("\n📊 Summary:")
print(f"   Customers: {Customer.objects.filter(tenant=tenant).count()}")
print(f"   Dishes: {Dish.objects.filter(tenant=tenant).count()}")
print(f"   Meals: {Meal.objects.filter(tenant=tenant).count()}")
print(f"   Today's Orders: {DailyEntry.objects.filter(tenant=tenant, date=today).count()}")
print(f"   Payments: {Payment.objects.filter(tenant=tenant).count()}")
print("\n🔑 Login: demo_admin / demo123")
