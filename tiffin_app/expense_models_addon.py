# from django.db import models
# from django.contrib.auth.models import User
# from django.core.validators import MinValueValidator
# from decimal import Decimal

# # Add these models to your existing tiffin_app/models.py

# class ExpenseCategory(models.Model):
#     """Categories for expenses like Vegetables, Groceries, Gas, etc."""
#     tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='expense_categories')
#     name = models.CharField(max_length=100)  # Sabji, Grocery, Gas, etc.
#     icon = models.CharField(max_length=50, default='📦')
#     is_active = models.BooleanField(default=True)
    
#     class Meta:
#         verbose_name_plural = 'Expense Categories'
#         ordering = ['name']
    
#     def __str__(self):
#         return f"{self.icon} {self.name}"


# class DailyExpense(models.Model):
#     """Daily expense entry - ek din ka total kharcha"""
#     tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='daily_expenses')
#     date = models.DateField()
#     category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     notes = models.TextField(blank=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-date']
#         unique_together = ['tenant', 'date', 'category']
    
#     def __str__(self):
#         return f"{self.date} - ₹{self.total_amount}"
    
#     def calculate_total(self):
#         """Auto-calculate total from items"""
#         total = self.items.aggregate(
#             total=models.Sum(models.F('quantity') * models.F('rate'))
#         )['total'] or 0
#         self.total_amount = total
#         self.save()
#         return total


# class ExpenseItem(models.Model):
#     """Individual items in daily expense - Tomato, Onion, etc."""
#     UNIT_CHOICES = [
#         ('KG', 'Kilogram'),
#         ('GM', 'Gram'),
#         ('LTR', 'Litre'),
#         ('ML', 'Millilitre'),
#         ('PC', 'Piece'),
#         ('PKT', 'Packet'),
#         ('BOX', 'Box'),
#         ('DOZEN', 'Dozen'),
#     ]
    
#     daily_expense = models.ForeignKey(DailyExpense, on_delete=models.CASCADE, related_name='items')
#     item_name = models.CharField(max_length=100)  # Tomato, Onion, Oil, etc.
#     quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
#     unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')
#     rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
#     total = models.DecimalField(max_digits=10, decimal_places=2)
#     notes = models.CharField(max_length=200, blank=True)
    
#     class Meta:
#         ordering = ['item_name']
    
#     def __str__(self):
#         return f"{self.item_name} - {self.quantity}{self.unit} @ ₹{self.rate}"
    
#     def save(self, *args, **kwargs):
#         # Auto-calculate total
#         self.total = self.quantity * self.rate
#         super().save(*args, **kwargs)
#         # Update parent expense total
#         self.daily_expense.calculate_total()


# class CommonExpenseItem(models.Model):
#     """Commonly used items for quick add - Auto-suggest"""
#     tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, related_name='common_items')
#     category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='common_items')
#     name = models.CharField(max_length=100)
#     default_unit = models.CharField(max_length=10, choices=ExpenseItem.UNIT_CHOICES, default='KG')
#     last_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     usage_count = models.IntegerField(default=0)
    
#     class Meta:
#         ordering = ['-usage_count', 'name']
#         unique_together = ['tenant', 'category', 'name']
    
#     def __str__(self):
#         return f"{self.name} ({self.default_unit})"


