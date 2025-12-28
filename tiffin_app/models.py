from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from django.core.exceptions import ValidationError
from django.db.models import Q

class Tenant(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='tenant_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, null=True, blank=True, help_text="Hex color e.g. #2c3e50")
    secondary_color = models.CharField(max_length=7, null=True, blank=True, help_text="Hex color e.g. #3498db")
    lunch_sticker_color = models.CharField(max_length=7, null=True, blank=True, help_text="Hex color e.g. #1f2937")
    dinner_sticker_color = models.CharField(max_length=7, null=True, blank=True, help_text="Hex color e.g. #111827")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_logo_url(self):
        if self.logo:
            return self.logo.url
        return '/static/tiffin_app/img/default_logo.png'
    
    def get_primary_color(self):
        return self.primary_color or '#2c3e50'
    
    def get_secondary_color(self):
        return self.secondary_color or '#3498db'
    
    def get_accent_color(self):
        return self.get_secondary_color()
    
    def get_lunch_sticker_color(self):
        return self.lunch_sticker_color or '#1f2937'
    
    def get_dinner_sticker_color(self):
        return self.dinner_sticker_color or '#111827'


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MANAGER')
    
    def __str__(self):
        return f"{self.user.username} - {self.role} ({self.tenant.name})"


class Customer(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(null=True, blank=True)
    delivery_location = models.CharField(max_length=500)
    daily_customer = models.BooleanField(default=True)  
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.delivery_location}"


class Dish(models.Model):
    CATEGORY_CHOICES = [
        ('BHAJI', 'Bhaji'),
        ('DAL', 'Dal'),
        ('RICE', 'Rice'),
        ('CHAPATI', 'Chapati'),
        ('OTHER', 'Other'),
    ]
    
    MEAL_CATEGORY_CHOICES = [
        ('LUNCH', 'Lunch'),
        ('DINNER', 'Dinner'),
        ('BOTH', 'Both'),
    ]
    
    FOOD_TYPE_CHOICES = [
        ('VEG', 'Veg'),
        ('NON_VEG', 'Non-Veg'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('NOT_AVAILABLE', 'Not Available'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    meal_category = models.CharField(max_length=10, choices=MEAL_CATEGORY_CHOICES)
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES, default='VEG')
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='AVAILABLE')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Dishes'
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class DishPortion(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='portions')
    portion_label = models.CharField(max_length=100)
    ml = models.IntegerField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['ml']
    
    def __str__(self):
        return f"{self.dish.name} - {self.portion_label}"


class Meal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('LUNCH', 'Lunch'),
        ('DINNER', 'Dinner'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    show_bhaji_on_sticker = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class MealDishPortion(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='template_items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    portion = models.ForeignKey(DishPortion, on_delete=models.SET_NULL, null=True, blank=True)
    default_qty = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    def __str__(self):
        portion_str = f" ({self.portion.portion_label})" if self.portion else ""
        return f"{self.meal.name}: {self.dish.name}{portion_str} x{self.default_qty}"




class DailyEntry(models.Model):
    MEAL_TYPE_CHOICES = [
        ('LUNCH', 'Lunch'),
        ('DINNER', 'Dinner'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='daily_entries')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    entry_date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES)

    menu = models.ForeignKey(
        "DailyMenu",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_entries",
    )

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-entry_date', 'customer__name']
        verbose_name_plural = 'Daily Entries'
        unique_together = ['customer', 'entry_date', 'meal_type']

    def __str__(self):
        return f"{self.customer.name} - {self.entry_date} ({self.meal_type})"

    def calculate_total(self):
        total = sum(meal.total_price for meal in self.order_meals.all())
        self.total_amount = total
        self.save()
        return total


class DailyMenu(models.Model):
    MEAL_TYPE_CHOICES = [
        ("LUNCH", "Lunch"),
        ("DINNER", "Dinner"),
        ("BOTH", "Both"),  # ✅ NEW
    ]

    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE, related_name="daily_menus")
    date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES)

    # ✅ optional label; allow NULL so multiple unnamed menus are possible
    menu_name = models.CharField(max_length=80, blank=True, null=True, default=None)

    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "meal_type", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "date", "meal_type", "menu_name"],
                condition=Q(menu_name__isnull=False) & ~Q(menu_name=""),
                name="uniq_menu_by_name",
            )
        ]

    def save(self, *args, **kwargs):
        # normalize blank -> None (so multiple unnamed menus allowed)
        self.menu_name = (self.menu_name or "").strip() or None
        self.notes = (self.notes or "").strip()
        super().save(*args, **kwargs)

    def __str__(self):
        label = self.menu_name or f"Menu #{self.id}"
        return f"{self.tenant.name} - {self.date} ({self.meal_type}) - {label}"


class DailyMenuItem(models.Model):
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name="items")
    dish = models.ForeignKey("Dish", on_delete=models.SET_NULL, null=True, blank=True)
    dish_name = models.CharField(max_length=200, blank=True)
    qty = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["daily_menu", "dish"],
                condition=Q(dish__isnull=False),
                name="uniq_menu_item_menu_dish",
            ),
            models.UniqueConstraint(
                fields=["daily_menu", "dish_name"],
                condition=Q(dish__isnull=True) & ~Q(dish_name=""),
                name="uniq_menu_item_menu_dishname",
            ),
        ]

    def clean(self):
        dn = (self.dish_name or "").strip()
        if not self.dish and not dn:
            raise ValidationError("Select a dish OR enter dish_name.")
        self.dish_name = dn

    def save(self, *args, **kwargs):
        self.full_clean()

        # auto create dish if dish_name is typed
        if self.dish is None and self.dish_name:
            tenant = self.daily_menu.tenant
            name = self.dish_name.strip()

            existing = Dish.objects.filter(tenant=tenant, name__iexact=name).first()
            if existing:
                self.dish = existing
            else:
                # ✅ if menu is BOTH, dish meal_category should also support BOTH
                meal_cat = self.daily_menu.meal_type  # LUNCH/DINNER/BOTH

                self.dish = Dish.objects.create(
                    tenant=tenant,
                    name=name,
                    category="OTHER",
                    meal_category=meal_cat,  # ✅ now can be BOTH (ensure Dish supports)
                    food_type="VEG",
                    availability="AVAILABLE",
                    is_active=True,
                )

            self.dish_name = ""

        super().save(*args, **kwargs)

    def __str__(self):
        label = self.dish.name if self.dish_id else self.dish_name
        return f"{self.daily_menu.date} {self.daily_menu.meal_type}: {label} x{self.qty}"


class OrderMeal(models.Model):
    daily_entry = models.ForeignKey(DailyEntry, on_delete=models.CASCADE, related_name='order_meals')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE)
    qty = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def total_price(self):
        return self.unit_price * self.qty
    
    def __str__(self):
        return f"{self.meal.name} x{self.qty}"


class OrderMealCustom(models.Model):
    SOURCE_CHOICES = [
        ('TEMPLATE', 'Template'),
        ('CUSTOM', 'Custom'),
    ]
    
    order_meal = models.ForeignKey(OrderMeal, on_delete=models.CASCADE, related_name='custom_items')
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL, null=True, blank=True)
    dish_name = models.CharField(max_length=200)  # Can be manual or from dish
    portion = models.ForeignKey(DishPortion, on_delete=models.SET_NULL, null=True, blank=True)
    qty = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='TEMPLATE')
    
    def __str__(self):
        portion_str = f" ({self.portion.portion_label})" if self.portion else ""
        return f"{self.dish_name}{portion_str} x{self.qty}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
        ('BANK', 'Bank Transfer'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.customer.name} - ₹{self.amount} ({self.payment_date})"


class ExpenseCategory(models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE, related_name="expense_categories")
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="📦")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="uniq_exp_cat_tenant_name")
        ]

    def __str__(self):
        return f"{self.icon} {self.name}"


class ExpenseItem(models.Model):
    UNIT_CHOICES = [
        ("KG", "Kilogram"),
        ("GM", "Gram"),
        ("LTR", "Litre"),
        ("ML", "Millilitre"),
        ("MTR", "Meter"),
        ("PC", "Piece"),
        ("PKT", "Packet"),
        ("BOX", "Box"),
        ("DOZEN", "Dozen"),
    ]

    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE, related_name="expense_items")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=100)
    default_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default="KG")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "category", "name"], name="uniq_item_tenant_cat_name")
        ]

    def __str__(self):
        return f"{self.name} ({self.default_unit})"


class DailyExpense(models.Model):
    tenant = models.ForeignKey("Tenant", on_delete=models.CASCADE, related_name="daily_expenses")
    date = models.DateField()

    # ✅ FK of ExpenseItem (as you asked)
    item = models.ForeignKey(ExpenseItem, on_delete=models.PROTECT, related_name="daily_rows")

    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit = models.CharField(max_length=10, choices=ExpenseItem.UNIT_CHOICES, default="KG")
    rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    notes = models.CharField(max_length=200, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "item__category__name", "item__name", "id"]

    def save(self, *args, **kwargs):
        self.total = (self.quantity * self.rate).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.item.name} - ₹{self.total}"

