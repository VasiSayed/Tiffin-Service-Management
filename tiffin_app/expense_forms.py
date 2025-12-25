from django import forms
from .models import ExpenseCategory, ExpenseItem

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "icon", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Vegetables"}),
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "🥬"}),
        }

class ExpenseItemForm(forms.ModelForm):
    class Meta:
        model = ExpenseItem
        fields = ["category", "name", "default_unit", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Tomato"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "default_unit": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop("tenant", None)
        super().__init__(*args, **kwargs)

        # tenant-scoped categories only
        if self.tenant:
            self.fields["category"].queryset = ExpenseCategory.objects.filter(
                tenant=self.tenant, is_active=True
            ).order_by("name")
