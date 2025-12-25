# # Add to tiffin_app/views.py

# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.db.models import Sum, Count, F
# from django.http import JsonResponse, HttpResponse
# from datetime import date, timedelta
# from decimal import Decimal
# import csv
# from .expense_models_addon import DailyExpense, ExpenseItem, ExpenseCategory, CommonExpenseItem

# @login_required
# def expense_dashboard(request):
#     """Daily expense entry dashboard"""
#     tenant = request.user.profile.tenant
#     today = date.today()
    
#     # Get or create today's expense
#     selected_date = request.GET.get('date', today.isoformat())
    
#     daily_expenses = DailyExpense.objects.filter(
#         tenant=tenant,
#         date=selected_date
#     ).prefetch_related('items')
    
#     categories = ExpenseCategory.objects.filter(tenant=tenant, is_active=True)
    
#     # Quick stats
#     this_month = DailyExpense.objects.filter(
#         tenant=tenant,
#         date__year=today.year,
#         date__month=today.month
#     ).aggregate(total=Sum('total_amount'))['total'] or 0
    
#     context = {
#         'daily_expenses': daily_expenses,
#         'categories': categories,
#         'selected_date': selected_date,
#         'this_month_total': this_month,
#     }
#     return render(request, 'tiffin_app/expenses/dashboard.html', context)


# @login_required
# def expense_add_item(request, expense_id):
#     """Add item to daily expense"""
#     expense = get_object_or_404(DailyExpense, pk=expense_id, tenant=request.user.profile.tenant)
    
#     if request.method == 'POST':
#         item = ExpenseItem.objects.create(
#             daily_expense=expense,
#             item_name=request.POST['item_name'],
#             quantity=Decimal(request.POST['quantity']),
#             unit=request.POST['unit'],
#             rate=Decimal(request.POST['rate']),
#             notes=request.POST.get('notes', '')
#         )
        
#         # Update common item
#         common_item, created = CommonExpenseItem.objects.get_or_create(
#             tenant=expense.tenant,
#             category=expense.category,
#             name=item.item_name,
#             defaults={'default_unit': item.unit}
#         )
#         common_item.last_rate = item.rate
#         common_item.usage_count += 1
#         common_item.save()
        
#         return redirect('expense_dashboard')
    
#     return redirect('expense_dashboard')


# @login_required
# def expense_create_entry(request):
#     """Create new daily expense entry"""
#     if request.method == 'POST':
#         tenant = request.user.profile.tenant
        
#         expense = DailyExpense.objects.create(
#             tenant=tenant,
#             date=request.POST['date'],
#             category_id=request.POST.get('category'),
#             notes=request.POST.get('notes', ''),
#             created_by=request.user
#         )
        
#         return JsonResponse({'success': True, 'expense_id': expense.id})
    
#     return JsonResponse({'success': False})


# @login_required
# def expense_monthly_report(request):
#     """Monthly expense report - Date-wise and Item-wise"""
#     tenant = request.user.profile.tenant
    
#     # Get month/year from request or use current
#     year = int(request.GET.get('year', date.today().year))
#     month = int(request.GET.get('month', date.today().month))
    
#     # Date-wise report
#     date_wise = DailyExpense.objects.filter(
#         tenant=tenant,
#         date__year=year,
#         date__month=month
#     ).values('date', 'category__name').annotate(
#         total=Sum('total_amount'),
#         items_count=Count('items')
#     ).order_by('date')
    
#     # Item-wise report
#     item_wise = ExpenseItem.objects.filter(
#         daily_expense__tenant=tenant,
#         daily_expense__date__year=year,
#         daily_expense__date__month=month
#     ).values('item_name', 'unit').annotate(
#         total_qty=Sum('quantity'),
#         total_amount=Sum('total'),
#         avg_rate=Sum('total') / Sum('quantity'),
#         times_purchased=Count('id')
#     ).order_by('-total_amount')
    
#     # Category-wise totals
#     category_wise = DailyExpense.objects.filter(
#         tenant=tenant,
#         date__year=year,
#         date__month=month
#     ).values('category__name', 'category__icon').annotate(
#         total=Sum('total_amount')
#     ).order_by('-total')
    
#     # Grand total
#     grand_total = DailyExpense.objects.filter(
#         tenant=tenant,
#         date__year=year,
#         date__month=month
#     ).aggregate(total=Sum('total_amount'))['total'] or 0
    
#     context = {
#         'year': year,
#         'month': month,
#         'date_wise': date_wise,
#         'item_wise': item_wise,
#         'category_wise': category_wise,
#         'grand_total': grand_total,
#     }
    
#     return render(request, 'tiffin_app/expenses/monthly_report.html', context)


# @login_required
# def expense_download_csv(request):
#     """Download monthly report as CSV"""
#     tenant = request.user.profile.tenant
#     year = int(request.GET.get('year', date.today().year))
#     month = int(request.GET.get('month', date.today().month))
    
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = f'attachment; filename="expenses_{year}_{month}.csv"'
    
#     writer = csv.writer(response)
#     writer.writerow(['Date', 'Category', 'Item', 'Quantity', 'Unit', 'Rate', 'Total'])
    
#     expenses = DailyExpense.objects.filter(
#         tenant=tenant,
#         date__year=year,
#         date__month=month
#     ).prefetch_related('items')
    
#     for expense in expenses:
#         for item in expense.items.all():
#             writer.writerow([
#                 expense.date,
#                 expense.category.name if expense.category else '-',
#                 item.item_name,
#                 item.quantity,
#                 item.unit,
#                 item.rate,
#                 item.total
#             ])
    
#     return response


# @login_required
# def expense_delete_item(request, item_id):
#     """Delete expense item"""
#     item = get_object_or_404(ExpenseItem, pk=item_id, daily_expense__tenant=request.user.profile.tenant)
#     expense = item.daily_expense
#     item.delete()
#     expense.calculate_total()
#     return redirect('expense_dashboard')


# @login_required
# def expense_get_suggestions(request):
#     """Get item suggestions for autocomplete"""
#     tenant = request.user.profile.tenant
#     category_id = request.GET.get('category')
#     query = request.GET.get('q', '')
    
#     items = CommonExpenseItem.objects.filter(
#         tenant=tenant,
#         category_id=category_id,
#         name__icontains=query
#     )[:10]
    
#     data = [{
#         'name': item.name,
#         'unit': item.default_unit,
#         'last_rate': str(item.last_rate) if item.last_rate else ''
#     } for item in items]
    
#     return JsonResponse({'suggestions': data})




import json
import csv
from decimal import Decimal
from datetime import date as dt_date

from decimal import Decimal
import json
from datetime import date as dt_date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.dateparse import parse_date
from .models import ExpenseCategory, ExpenseItem, DailyExpense
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.dateparse import parse_date

from .models import ExpenseCategory, ExpenseItem, DailyExpense


def _tenant(request):
    # adjust if your tenant is stored differently
    return request.user.profile.tenant



@login_required
def expense_dashboard(request):
    tenant = _tenant(request)
    today = dt_date.today()

    selected_date = parse_date(request.GET.get("date") or "") or today

    categories = ExpenseCategory.objects.filter(tenant=tenant, is_active=True).order_by("name")

    rows = (
        DailyExpense.objects.filter(tenant=tenant, date=selected_date)
        .select_related("item", "item__category")
        .order_by("item__category__name", "item__name", "id")
    )
    print(rows,'my rows')
    # Group rows by category for UI cards
    grouped = {}
    for r in rows:
        cat = r.item.category
        if cat.id not in grouped:
            grouped[cat.id] = {"category": cat, "rows": [], "total": Decimal("0.00")}
        grouped[cat.id]["rows"].append(r)
        grouped[cat.id]["total"] += r.total

    grouped_expenses = list(grouped.values())
    print(grouped_expenses,'my expense')

    # This month total
    this_month_total = (
        DailyExpense.objects.filter(
            tenant=tenant,
            date__year=selected_date.year,
            date__month=selected_date.month
        ).aggregate(s=Sum("total"))["s"] or Decimal("0.00")
    )
    print(this_month_total,"total")

    return render(request, "tiffin_app/expenses/dashboard.html", {
        "categories": categories,
        "selected_date": selected_date.isoformat(),
        "grouped_expenses": grouped_expenses,
        "this_month_total": this_month_total,
    })



@login_required
@transaction.atomic
def expense_create_entry(request):
    tenant = _tenant(request)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)

    def to_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    # ---------------------------
    # JSON mode
    # ---------------------------
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        d = parse_date(payload.get("date") or "")
        rows = payload.get("rows") or []

        if not d:
            return JsonResponse({"success": False, "error": "Invalid date"}, status=400)
        if not isinstance(rows, list) or len(rows) == 0:
            return JsonResponse({"success": False, "error": "At least 1 row required"}, status=400)

        # ✅ cast category ids to int
        cat_ids = {to_int(r.get("category_id")) for r in rows}
        cat_ids.discard(None)

        cats = ExpenseCategory.objects.filter(tenant=tenant, is_active=True, id__in=cat_ids)
        cat_map = {c.id: c for c in cats}

        objects = []
        for idx, r in enumerate(rows, start=1):
            cat_id = to_int(r.get("category_id"))
            item_id = to_int(r.get("item_id"))

            unit = (r.get("unit") or "KG").strip()
            notes = (r.get("notes") or "").strip()

            if not cat_id or cat_id not in cat_map:
                return JsonResponse({"success": False, "error": f"Invalid category in row #{idx}"}, status=400)

            if not item_id:
                return JsonResponse({"success": False, "error": f"Item required in row #{idx}"}, status=400)

            try:
                qty = Decimal(str(r.get("quantity") or "0"))
                rate = Decimal(str(r.get("rate") or "0"))
            except Exception:
                return JsonResponse({"success": False, "error": f"Invalid qty/rate in row #{idx}"}, status=400)

            if qty <= 0 or rate <= 0:
                return JsonResponse({"success": False, "error": f"Qty/Rate must be > 0 in row #{idx}"}, status=400)

            item = get_object_or_404(
                ExpenseItem,
                tenant=tenant,
                is_active=True,
                id=item_id,
                category_id=cat_id,
            )

            line_total = (qty * rate).quantize(Decimal("0.01"))
            objects.append(DailyExpense(
                tenant=tenant,
                date=d,
                item=item,
                quantity=qty,
                total=line_total, 
                unit=unit,
                rate=rate,
                notes=notes,
                created_by=request.user
            ))

        DailyExpense.objects.bulk_create(objects)
        return JsonResponse({"success": True, "created": len(objects)})

    return JsonResponse({"success": False, "error": "Send JSON"}, status=400)



@login_required
def expense_add_item(request, expense_id):
    """
    ✅ Keep your existing URL, but meaning change:
    expense_id here will be treated as CATEGORY ID (for backward compatibility).
    POST form: item_name, quantity, unit, rate, notes, date(optional)
    """
    tenant = _tenant(request)
    if request.method != "POST":
        return redirect("expense_dashboard")

    cat = get_object_or_404(ExpenseCategory, tenant=tenant, is_active=True, id=expense_id)

    d = parse_date(request.POST.get("date") or "") or dt_date.today()
    name = (request.POST.get("item_name") or "").strip()
    unit = (request.POST.get("unit") or "KG").strip()
    notes = (request.POST.get("notes") or "").strip()

    try:
        qty = Decimal(str(request.POST.get("quantity") or "0"))
        rate = Decimal(str(request.POST.get("rate") or "0"))
    except Exception:
        return redirect(f"{'/expenses/'}?date={d.isoformat()}")

    if not name or qty <= 0 or rate <= 0:
        return redirect(f"{'/expenses/'}?date={d.isoformat()}")

    item, _ = ExpenseItem.objects.get_or_create(
        tenant=tenant, category=cat, name=name, defaults={"default_unit": unit}
    )

    DailyExpense.objects.create(
        tenant=tenant, date=d, item=item, quantity=qty, unit=unit, rate=rate, notes=notes, created_by=request.user
    )

    return redirect(f"{'/expenses/'}?date={d.isoformat()}")


@login_required
def expense_delete_item(request, item_id):
    """
    ✅ Keep your existing URL:
    item_id will delete a DailyExpense ROW (not master item).
    """
    tenant = _tenant(request)
    row = get_object_or_404(DailyExpense, id=item_id, tenant=tenant)
    d = row.date.isoformat()
    if request.method == "POST":
        row.delete()
    return redirect(f"{'/expenses/'}?date={d}")


@login_required
def expense_monthly_report(request):
    tenant = _tenant(request)
    today = dt_date.today()

    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    qs = DailyExpense.objects.filter(tenant=tenant, date__year=year, date__month=month).select_related("item", "item__category")

    # Date-wise totals (date + category)
    date_wise = (
        qs.values("date", "item__category__name", "item__category__icon")
        .annotate(total=Sum("total"), rows_count=Count("id"))
        .order_by("date", "item__category__name")
    )

    # Item-wise totals
    item_wise_raw = (
        qs.values("item__name", "unit")
        .annotate(total_qty=Sum("quantity"), total_amount=Sum("total"), times_purchased=Count("id"))
        .order_by("-total_amount")
    )

    # Compute avg_rate in python (safe)
    item_wise = []
    for r in item_wise_raw:
        tq = r["total_qty"] or Decimal("0.00")
        ta = r["total_amount"] or Decimal("0.00")
        avg = (ta / tq).quantize(Decimal("0.01")) if tq and tq != 0 else Decimal("0.00")
        r["avg_rate"] = avg
        item_wise.append(r)

    # Category-wise totals
    category_wise = (
        qs.values("item__category__name", "item__category__icon")
        .annotate(total=Sum("total"))
        .order_by("-total")
    )

    grand_total = qs.aggregate(s=Sum("total"))["s"] or Decimal("0.00")

    return render(request, "tiffin_app/expenses/monthly_report.html", {
        "year": year,
        "month": month,
        "date_wise": date_wise,
        "item_wise": item_wise,
        "category_wise": category_wise,
        "grand_total": grand_total,
    })


@login_required
def expense_download_csv(request):
    tenant = _tenant(request)
    today = dt_date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="expenses_{year}_{month}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Category", "Item", "Quantity", "Unit", "Rate", "Total", "Notes"])

    rows = (
        DailyExpense.objects.filter(tenant=tenant, date__year=year, date__month=month)
        .select_related("item", "item__category")
        .order_by("date", "item__category__name", "item__name")
    )

    for r in rows:
        writer.writerow([
            r.date,
            r.item.category.name,
            r.item.name,
            r.quantity,
            r.unit,
            r.rate,
            r.total,
            r.notes or ""
        ])

    return response

# tiffin_app/views.py  (add at bottom)
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ExpenseItem

@require_GET
@login_required
def expense_items_api(request):
    tenant = _tenant(request)
    category_id = request.GET.get("category_id")

    qs = ExpenseItem.objects.filter(tenant=tenant, is_active=True)
    if category_id:
        qs = qs.filter(category_id=category_id)

    qs = qs.order_by("name")

    return JsonResponse({
        "success": True,
        "items": [
            {
                "id": it.id,
                "name": it.name,
                "default_unit": it.default_unit,
                "category_id": it.category_id,
            }
            for it in qs
        ]
    })



from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods

from .models import ExpenseCategory, ExpenseItem
from .expense_forms import ExpenseCategoryForm, ExpenseItemForm

# ✅ Category CRUD
@login_required
def expense_category_list(request):
    tenant = _tenant(request)
    categories = ExpenseCategory.objects.filter(tenant=tenant).order_by("name")
    return render(request, "tiffin_app/expenses/categories/list.html", {"categories": categories})

@login_required
@require_http_methods(["GET", "POST"])
def expense_category_create(request):
    tenant = _tenant(request)

    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, "Category created")
            return redirect("expense_category_list")
    else:
        form = ExpenseCategoryForm()

    return render(request, "tiffin_app/expenses/categories/form.html", {
        "form": form,
        "title": "Add Category",
    })

@login_required
@require_http_methods(["GET", "POST"])
def expense_category_edit(request, pk):
    tenant = _tenant(request)
    category = get_object_or_404(ExpenseCategory, tenant=tenant, pk=pk)

    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated")
            return redirect("expense_category_list")
    else:
        form = ExpenseCategoryForm(instance=category)

    return render(request, "tiffin_app/expenses/categories/form.html", {
        "form": form,
        "title": "Edit Category",
        "category": category,
    })

@login_required
@require_http_methods(["GET", "POST"])
def expense_category_delete(request, pk):
    tenant = _tenant(request)
    category = get_object_or_404(ExpenseCategory, tenant=tenant, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted")
        return redirect("expense_category_list")

    return render(request, "tiffin_app/expenses/categories/delete.html", {"category": category})


# ✅ Item CRUD
@login_required
def expense_item_list(request):
    tenant = _tenant(request)
    items = ExpenseItem.objects.filter(tenant=tenant).select_related("category").order_by("category__name", "name")
    return render(request, "tiffin_app/expenses/items/list.html", {"items": items})

@login_required
@require_http_methods(["GET", "POST"])
def expense_item_create(request):
    tenant = _tenant(request)

    if request.method == "POST":
        form = ExpenseItemForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, "Item created")
            return redirect("expense_item_list")
    else:
        form = ExpenseItemForm(tenant=tenant)

    return render(request, "tiffin_app/expenses/items/form.html", {
        "form": form,
        "title": "Add Item",
    })

@login_required
@require_http_methods(["GET", "POST"])
def expense_item_edit(request, pk):
    tenant = _tenant(request)
    item = get_object_or_404(ExpenseItem, tenant=tenant, pk=pk)

    if request.method == "POST":
        form = ExpenseItemForm(request.POST, instance=item, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated")
            return redirect("expense_item_list")
    else:
        form = ExpenseItemForm(instance=item, tenant=tenant)

    return render(request, "tiffin_app/expenses/items/form.html", {
        "form": form,
        "title": "Edit Item",
        "item": item,
    })

@login_required
@require_http_methods(["GET", "POST"])
def expense_item_delete(request, pk):
    tenant = _tenant(request)
    item = get_object_or_404(ExpenseItem, tenant=tenant, pk=pk)

    if request.method == "POST":
        item.delete()
        messages.success(request, "Item deleted")
        return redirect("expense_item_list")

    return render(request, "tiffin_app/expenses/items/delete.html", {"item": item})



