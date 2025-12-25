from django.contrib import admin
from .models import *

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role']
    list_filter = ['role', 'tenant']
    search_fields = ['user__username', 'user__email']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_number', 'delivery_location', 'tenant', 'is_active']
    list_filter = ['tenant', 'is_active']
    search_fields = ['name', 'contact_number', 'delivery_location']

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'meal_category', 'food_type', 'availability', 'tenant', 'is_active']
    list_filter = ['category', 'meal_category', 'food_type', 'availability', 'tenant', 'is_active']
    search_fields = ['name']

@admin.register(DishPortion)
class DishPortionAdmin(admin.ModelAdmin):
    list_display = ['dish', 'portion_label', 'ml', 'base_price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['portion_label', 'dish__name']

@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'meal_type', 'price', 'show_bhaji_on_sticker', 'tenant', 'is_active']
    list_filter = ['meal_type', 'tenant', 'is_active']
    search_fields = ['name']

@admin.register(MealDishPortion)
class MealDishPortionAdmin(admin.ModelAdmin):
    list_display = ['meal', 'dish', 'portion', 'default_qty']
    list_filter = ['meal__tenant']
    search_fields = ['meal__name', 'dish__name']

@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'entry_date', 'meal_type', 'total_amount', 'tenant']
    list_filter = ['entry_date', 'meal_type', 'tenant']
    search_fields = ['customer__name']
    date_hierarchy = 'entry_date'

@admin.register(OrderMeal)
class OrderMealAdmin(admin.ModelAdmin):
    list_display = ['daily_entry', 'meal', 'qty', 'unit_price', 'total_price']
    search_fields = ['daily_entry__customer__name', 'meal__name']

@admin.register(OrderMealCustom)
class OrderMealCustomAdmin(admin.ModelAdmin):
    list_display = ['order_meal', 'dish_name', 'qty', 'source']
    list_filter = ['source']
    search_fields = ['dish_name', 'order_meal__daily_entry__customer__name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'payment_date', 'amount', 'method', 'tenant']
    list_filter = ['payment_date', 'method', 'tenant']
    search_fields = ['customer__name']
    date_hierarchy = 'payment_date'


admin.site.register([ExpenseCategory,ExpenseItem,DailyExpense])