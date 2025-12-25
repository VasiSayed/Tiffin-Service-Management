# tiffin_app/forms_expenses.py
from django import forms
from .models import ExpenseCategory, ExpenseItem

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "icon", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "📦"}),
            "is_active": forms.CheckboxInput(attrs={}),
        }

class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ["category", "name", "default_unit", "is_active"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "default_unit": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["category"].queryset = ExpenseCategory.objects.filter(
                tenant=tenant, is_active=True
            ).order_by("name")
