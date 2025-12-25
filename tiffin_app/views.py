import json
from datetime import date
from decimal import Decimal
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from .models import (
    Customer, Dish, DishPortion, Meal, MealDishPortion,
    DailyEntry, OrderMeal, OrderMealCustom, Payment,
    ExpenseCategory, ExpenseItem
)

from .forms_expenses import ExpenseCategoryForm, ExpenseItemForm

# If you have these expense views in separate file, comment these out OR remove duplicates.
# from .expense_views_addon import (
#     expense_dashboard, expense_create_entry, expense_add_item, expense_delete_item,
#     expense_monthly_report, expense_download_csv
# )

# ---------------- helpers ----------------
def _tenant(request):
    return request.user.profile.tenant

def _to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _to_bool(v, default=False):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "on")


# ---------------- permissions ----------------
def require_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, "profile") or request.user.profile.role != "ADMIN":
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect("daily_entry_list" if hasattr(request.user, "profile") else "login")
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------- auth ----------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.profile.role == "ADMIN":
            return redirect("dashboard")
        return redirect("daily_entry_list")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            if user.profile.role == "ADMIN":
                return redirect("dashboard")
            return redirect("daily_entry_list")
        messages.error(request, "Invalid username or password")

    return render(request, "tiffin_app/login.html")


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect("login")


# ---------------- dashboard ----------------
@login_required
@require_admin
def dashboard(request):
    tenant = _tenant(request)
    today = date.today()

    context = {
        "total_customers": Customer.objects.filter(tenant=tenant, is_active=True).count(),
        "total_dishes": Dish.objects.filter(tenant=tenant, is_active=True).count(),
        "total_meals": Meal.objects.filter(tenant=tenant, is_active=True).count(),
        "today_orders": DailyEntry.objects.filter(tenant=tenant, entry_date=today).count(),
    }
    return render(request, "tiffin_app/dashboard.html", context)


# ---------------- customers ----------------
@login_required
@require_admin
def customer_list(request):
    tenant = _tenant(request)
    search = request.GET.get("search", "")

    customers = Customer.objects.filter(tenant=tenant)
    if search:
        customers = customers.filter(
            Q(name__icontains=search)
            | Q(contact_number__icontains=search)
            | Q(delivery_location__icontains=search)
        )

    return render(request, "tiffin_app/customers/list.html", {"customers": customers, "search": search})


@login_required
@require_admin
def customer_add(request):
    if request.method == "POST":
        tenant = _tenant(request)
        Customer.objects.create(
            tenant=tenant,
            name=request.POST["name"],
            contact_number=request.POST.get("contact_number", ""),
            email=request.POST.get("email") or None,
            delivery_location=request.POST["delivery_location"],
            address=request.POST.get("address", ""),
            is_active=request.POST.get("is_active") == "on",
        )
        messages.success(request, "Customer added successfully")
        return redirect("customer_list")

    return render(request, "tiffin_app/customers/form.html")


@login_required
@require_admin
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, tenant=_tenant(request))

    if request.method == "POST":
        customer.name = request.POST["name"]
        customer.contact_number = request.POST.get("contact_number", "")
        customer.email = request.POST.get("email") or None
        customer.delivery_location = request.POST["delivery_location"]
        customer.address = request.POST.get("address", "")
        customer.is_active = request.POST.get("is_active") == "on"
        customer.save()
        messages.success(request, "Customer updated successfully")
        return redirect("customer_list")

    return render(request, "tiffin_app/customers/form.html", {"customer": customer})


@login_required
@require_admin
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk, tenant=_tenant(request))
    customer.delete()
    messages.success(request, "Customer deleted successfully")
    return redirect("customer_list")


# ---------------- dishes ----------------
@login_required
def dish_list(request):
    tenant = _tenant(request)
    search = request.GET.get("search", "")

    dishes = Dish.objects.filter(tenant=tenant)
    if search:
        dishes = dishes.filter(name__icontains=search)

    return render(
        request,
        "tiffin_app/dishes/list.html",
        {"dishes": dishes, "search": search, "is_admin": request.user.profile.role == "ADMIN"},
    )


@login_required
@require_admin
def dish_add(request):
    if request.method == "POST":
        tenant = _tenant(request)
        Dish.objects.create(
            tenant=tenant,
            name=request.POST["name"],
            category=request.POST["category"],
            meal_category=request.POST["meal_category"],
            food_type=request.POST["food_type"],
            availability=request.POST["availability"],
            is_active=request.POST.get("is_active") == "on",
        )
        messages.success(request, "Dish added successfully")
        return redirect("dish_list")

    return render(request, "tiffin_app/dishes/form.html")


@login_required
@require_admin
def dish_edit(request, pk):
    dish = get_object_or_404(Dish, pk=pk, tenant=_tenant(request))

    if request.method == "POST":
        dish.name = request.POST["name"]
        dish.category = request.POST["category"]
        dish.meal_category = request.POST["meal_category"]
        dish.food_type = request.POST["food_type"]
        dish.availability = request.POST["availability"]
        dish.is_active = request.POST.get("is_active") == "on"
        dish.save()
        messages.success(request, "Dish updated successfully")
        return redirect("dish_list")

    return render(request, "tiffin_app/dishes/form.html", {"dish": dish})


@login_required
@require_admin
def dish_delete(request, pk):
    dish = get_object_or_404(Dish, pk=pk, tenant=_tenant(request))
    dish.delete()
    messages.success(request, "Dish deleted successfully")
    return redirect("dish_list")


@login_required
def dish_portions(request, pk):
    dish = get_object_or_404(Dish, pk=pk, tenant=_tenant(request))
    return render(
        request,
        "tiffin_app/dishes/portions.html",
        {"dish": dish, "is_admin": request.user.profile.role == "ADMIN"},
    )


@login_required
@require_admin
def portion_add(request, dish_pk):
    dish = get_object_or_404(Dish, pk=dish_pk, tenant=_tenant(request))

    if request.method == "POST":
        DishPortion.objects.create(
            dish=dish,
            portion_label=request.POST["portion_label"],
            ml=request.POST.get("ml") or None,
            base_price=request.POST.get("base_price") or None,
            is_active=request.POST.get("is_active") == "on",
        )
        messages.success(request, "Portion added successfully")
        return redirect("dish_portions", pk=dish.pk)

    return render(request, "tiffin_app/dishes/portion_form.html", {"dish": dish})


@login_required
@require_admin
def portion_delete(request, pk):
    portion = get_object_or_404(DishPortion, pk=pk, dish__tenant=_tenant(request))
    dish_pk = portion.dish.pk
    portion.delete()
    messages.success(request, "Portion deleted successfully")
    return redirect("dish_portions", pk=dish_pk)


# ---------------- meals ----------------
@login_required
@require_admin
def meal_list(request):
    tenant = _tenant(request)
    meals = Meal.objects.filter(tenant=tenant)
    return render(request, "tiffin_app/meals/list.html", {"meals": meals})


@login_required
@require_admin
def meal_add(request):
    tenant = _tenant(request)
    dishes = Dish.objects.filter(tenant=tenant, is_active=True).order_by("name")

    # normal form post
    if request.method == "POST" and "application/json" not in (request.content_type or ""):
        Meal.objects.create(
            tenant=tenant,
            name=request.POST["name"],
            meal_type=request.POST["meal_type"],
            price=request.POST["price"],
            show_bhaji_on_sticker=request.POST.get("show_bhaji_on_sticker") == "on",
            is_active=request.POST.get("is_active") == "on",
        )
        messages.success(request, "Meal added successfully")
        return redirect("meal_list")

    return render(request, "tiffin_app/meals/form.html", {"dishes": dishes})


@login_required
@require_admin
@transaction.atomic
def meal_bulk_create(request):
    tenant = _tenant(request)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)
    if "application/json" not in (request.content_type or ""):
        return JsonResponse({"success": False, "error": "Send JSON"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    name = (payload.get("name") or "").strip()
    meal_type = (payload.get("meal_type") or "").strip()
    price_raw = payload.get("price")

    show_bhaji = _to_bool(payload.get("show_bhaji_on_sticker"), default=True)
    is_active = _to_bool(payload.get("is_active"), default=True)
    items = payload.get("items") or []

    if not name:
        return JsonResponse({"success": False, "error": "Meal name required"}, status=400)
    if meal_type not in ("LUNCH", "DINNER"):
        return JsonResponse({"success": False, "error": "Invalid meal_type"}, status=400)

    try:
        price = Decimal(str(price_raw))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid price"}, status=400)

    meal = Meal.objects.create(
        tenant=tenant,
        name=name,
        meal_type=meal_type,
        price=price,
        show_bhaji_on_sticker=show_bhaji,
        is_active=is_active,
    )

    if items:
        dish_ids = []
        for r in items:
            did = _to_int(r.get("dish_id"))
            if did:
                dish_ids.append(did)
        dish_ids = list(set(dish_ids))

        dish_map = {d.id: d for d in Dish.objects.filter(tenant=tenant, is_active=True, id__in=dish_ids)}

        rows = []
        for idx, r in enumerate(items, start=1):
            dish_id = _to_int(r.get("dish_id"))
            if not dish_id or dish_id not in dish_map:
                return JsonResponse({"success": False, "error": f"Dish not found row #{idx}"}, status=400)

            qty = _to_int(r.get("default_qty")) or 1
            if qty <= 0:
                qty = 1

            rows.append(MealDishPortion(meal=meal, dish=dish_map[dish_id], portion=None, default_qty=qty))

        MealDishPortion.objects.bulk_create(rows)

    return JsonResponse({"success": True, "meal_id": meal.id})


@login_required
@require_admin
@transaction.atomic
def meal_items_bulk_add(request, meal_pk):
    tenant = _tenant(request)
    meal = get_object_or_404(Meal, pk=meal_pk, tenant=tenant)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)
    if "application/json" not in (request.content_type or ""):
        return JsonResponse({"success": False, "error": "Send JSON"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    items = payload.get("items") or []
    if not items:
        return JsonResponse({"success": False, "error": "No items"}, status=400)

    dish_ids = []
    for r in items:
        did = _to_int(r.get("dish_id"))
        if did:
            dish_ids.append(did)
    dish_ids = list(set(dish_ids))

    dish_map = {d.id: d for d in Dish.objects.filter(tenant=tenant, is_active=True, id__in=dish_ids)}

    rows = []
    for idx, r in enumerate(items, start=1):
        dish_id = _to_int(r.get("dish_id"))
        if not dish_id or dish_id not in dish_map:
            return JsonResponse({"success": False, "error": f"Dish not found row #{idx}"}, status=400)

        qty = _to_int(r.get("default_qty")) or 1
        if qty <= 0:
            qty = 1

        rows.append(MealDishPortion(meal=meal, dish=dish_map[dish_id], portion=None, default_qty=qty))

    MealDishPortion.objects.bulk_create(rows)
    return JsonResponse({"success": True, "added": len(rows)})


@login_required
@require_admin
def meal_edit(request, pk):
    meal = get_object_or_404(Meal, pk=pk, tenant=_tenant(request))

    if request.method == "POST":
        meal.name = request.POST["name"]
        meal.meal_type = request.POST["meal_type"]
        meal.price = request.POST["price"]
        meal.show_bhaji_on_sticker = request.POST.get("show_bhaji_on_sticker") == "on"
        meal.is_active = request.POST.get("is_active") == "on"
        meal.save()
        messages.success(request, "Meal updated successfully")
        return redirect("meal_list")

    return render(request, "tiffin_app/meals/form.html", {"meal": meal})


@login_required
@require_admin
def meal_delete(request, pk):
    meal = get_object_or_404(Meal, pk=pk, tenant=_tenant(request))
    meal.delete()
    messages.success(request, "Meal deleted successfully")
    return redirect("meal_list")


@login_required
@require_admin
def meal_detail(request, pk):
    tenant = _tenant(request)
    meal = get_object_or_404(Meal, pk=pk, tenant=tenant)
    dishes = Dish.objects.filter(tenant=tenant, is_active=True)
    return render(request, "tiffin_app/meals/detail.html", {"meal": meal, "dishes": dishes})


@login_required
@require_admin
def meal_item_add(request, meal_pk):
    meal = get_object_or_404(Meal, pk=meal_pk, tenant=_tenant(request))

    if request.method == "POST":
        dish = get_object_or_404(Dish, pk=request.POST["dish"])
        portion = None
        if request.POST.get("portion"):
            portion = get_object_or_404(DishPortion, pk=request.POST["portion"])

        MealDishPortion.objects.create(
            meal=meal,
            dish=dish,
            portion=portion,
            default_qty=request.POST.get("default_qty", 1),
        )
        messages.success(request, "Item added to meal template")

    return redirect("meal_detail", pk=meal.pk)


@login_required
@require_admin
def meal_item_delete(request, pk):
    item = get_object_or_404(MealDishPortion, pk=pk, meal__tenant=_tenant(request))
    meal_pk = item.meal.pk
    item.delete()
    messages.success(request, "Item removed from meal template")
    return redirect("meal_detail", pk=meal_pk)


# ---------------- daily entry ----------------
@login_required
def daily_entry_list(request):
    tenant = _tenant(request)
    entry_date = request.GET.get("date", str(date.today()))
    meal_type = request.GET.get("meal_type", "LUNCH")

    entries = (
        DailyEntry.objects.filter(tenant=tenant, entry_date=entry_date, meal_type=meal_type)
        .select_related("customer")
    )

    return render(
        request,
        "tiffin_app/daily_entry/list.html",
        {"entries": entries, "entry_date": entry_date, "meal_type": meal_type},
    )


@login_required
def daily_entry_add(request):
    tenant = _tenant(request)

    if request.method == "POST":
        customer = get_object_or_404(Customer, pk=request.POST["customer"], tenant=tenant)
        entry_date = request.POST["entry_date"]
        meal_type = request.POST["meal_type"]

        entry, created = DailyEntry.objects.get_or_create(
            tenant=tenant, customer=customer, entry_date=entry_date, meal_type=meal_type
        )

        if created:
            messages.success(request, "Order created successfully")
        else:
            messages.info(request, "Order already exists, opening it")

        return redirect("daily_entry_detail", pk=entry.pk)

    customers = Customer.objects.filter(tenant=tenant, is_active=True)
    return render(
        request,
        "tiffin_app/daily_entry/form.html",
        {"customers": customers, "today": str(date.today())},
    )


@login_required
def daily_entry_detail(request, pk):
    tenant = _tenant(request)
    entry = get_object_or_404(DailyEntry, pk=pk, tenant=tenant)
    meals = Meal.objects.filter(tenant=tenant, meal_type=entry.meal_type, is_active=True)
    dishes = Dish.objects.filter(tenant=tenant, is_active=True)

    return render(
        request,
        "tiffin_app/daily_entry/detail.html",
        {"entry": entry, "meals": meals, "dishes": dishes},
    )


@login_required
@transaction.atomic
def order_meal_bulk_add(request, entry_pk):
    tenant = _tenant(request)
    entry = get_object_or_404(DailyEntry, pk=entry_pk, tenant=tenant)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)
    if "application/json" not in (request.content_type or ""):
        return JsonResponse({"success": False, "error": "Send JSON"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    rows = payload.get("rows") or []
    if not isinstance(rows, list) or not rows:
        return JsonResponse({"success": False, "error": "No rows"}, status=400)

    meal_ids = []
    for r in rows:
        mid = _to_int(r.get("meal_id"))
        if mid:
            meal_ids.append(mid)
    meal_ids = list(set(meal_ids))

    meals_qs = (
        Meal.objects.filter(
            tenant=tenant,
            is_active=True,
            id__in=meal_ids,
            meal_type=entry.meal_type,
        ).prefetch_related("template_items__dish", "template_items__portion")
    )
    meal_map = {m.id: m for m in meals_qs}

    created_count = 0

    for idx, r in enumerate(rows, start=1):
        meal_id = _to_int(r.get("meal_id"))
        qty = _to_int(r.get("qty")) or 1
        if qty <= 0:
            qty = 1

        if not meal_id or meal_id not in meal_map:
            return JsonResponse({"success": False, "error": f"Invalid meal in row #{idx}"}, status=400)

        meal = meal_map[meal_id]

        order_meal = OrderMeal.objects.create(
            daily_entry=entry,
            meal=meal,
            qty=qty,
            unit_price=meal.price,
        )
        created_count += 1

        tmpl_items = meal.template_items.all()
        if tmpl_items:
            custom_rows = []
            for t in tmpl_items:
                custom_rows.append(
                    OrderMealCustom(
                        order_meal=order_meal,
                        dish=t.dish,
                        dish_name=t.dish.name,
                        portion=t.portion,
                        qty=t.default_qty,
                        source="TEMPLATE",
                    )
                )
            OrderMealCustom.objects.bulk_create(custom_rows)

    entry.calculate_total()
    return JsonResponse({"success": True, "created": created_count})


@login_required
def order_meal_add(request, entry_pk):
    entry = get_object_or_404(DailyEntry, pk=entry_pk, tenant=_tenant(request))

    if request.method == "POST":
        meal = get_object_or_404(Meal, pk=request.POST["meal"], tenant=entry.tenant)
        qty = int(request.POST.get("qty", 1))

        order_meal = OrderMeal.objects.create(
            daily_entry=entry,
            meal=meal,
            qty=qty,
            unit_price=meal.price,
        )

        template_items = list(meal.template_items.select_related("dish", "portion").all())
        bulk_custom = []
        for t in template_items:
            bulk_custom.append(
                OrderMealCustom(
                    order_meal=order_meal,
                    dish=t.dish,
                    dish_name=t.dish.name,
                    portion=t.portion,
                    qty=t.default_qty,
                    source="TEMPLATE",
                )
            )
        if bulk_custom:
            OrderMealCustom.objects.bulk_create(bulk_custom)

        entry.calculate_total()
        messages.success(request, "Meal added to order")

    return redirect("daily_entry_detail", pk=entry.pk)


@login_required
def order_meal_delete(request, pk):
    order_meal = get_object_or_404(OrderMeal, pk=pk, daily_entry__tenant=_tenant(request))
    entry_pk = order_meal.daily_entry.pk
    order_meal.delete()

    entry = DailyEntry.objects.get(pk=entry_pk)
    entry.calculate_total()

    messages.success(request, "Meal removed from order")
    return redirect("daily_entry_detail", pk=entry_pk)


@login_required
def custom_item_add(request, order_meal_pk):
    tenant = _tenant(request)
    order_meal = get_object_or_404(OrderMeal, pk=order_meal_pk, daily_entry__tenant=tenant)

    if request.method == "POST":
        dish_name = request.POST.get("manual_name")
        dish = None
        portion = None

        if request.POST.get("dish"):
            dish = get_object_or_404(Dish, pk=request.POST["dish"])
            dish_name = dish.name

        if request.POST.get("portion"):
            portion = get_object_or_404(DishPortion, pk=request.POST["portion"])

        OrderMealCustom.objects.create(
            order_meal=order_meal,
            dish=dish,
            dish_name=dish_name,
            portion=portion,
            qty=request.POST.get("qty", 1),
            source="CUSTOM",
        )
        messages.success(request, "Custom item added")

    return redirect("daily_entry_detail", pk=order_meal.daily_entry.pk)


@login_required
def custom_item_delete(request, pk):
    item = get_object_or_404(OrderMealCustom, pk=pk, order_meal__daily_entry__tenant=_tenant(request))
    entry_pk = item.order_meal.daily_entry.pk
    item.delete()
    messages.success(request, "Item removed")
    return redirect("daily_entry_detail", pk=entry_pk)


# optional multi customer create (keep if you want)
@login_required
@transaction.atomic
def daily_entry_bulk_create(request):
    tenant = _tenant(request)

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)
    if "application/json" not in (request.content_type or ""):
        return JsonResponse({"success": False, "error": "Send JSON"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    entry_date = parse_date(payload.get("entry_date") or "")
    meal_type = (payload.get("meal_type") or "").strip()
    customer_ids = payload.get("customer_ids") or []

    if not entry_date:
        return JsonResponse({"success": False, "error": "Invalid entry_date"}, status=400)
    if meal_type not in ("LUNCH", "DINNER"):
        return JsonResponse({"success": False, "error": "Invalid meal_type"}, status=400)
    if not isinstance(customer_ids, list) or not customer_ids:
        return JsonResponse({"success": False, "error": "Select at least 1 customer"}, status=400)

    ids = []
    for x in customer_ids:
        xid = _to_int(x)
        if xid:
            ids.append(xid)
    ids = list(set(ids))
    if not ids:
        return JsonResponse({"success": False, "error": "Invalid customers"}, status=400)

    customers = Customer.objects.filter(tenant=tenant, is_active=True, id__in=ids)
    cust_ids = list(customers.values_list("id", flat=True))
    if not cust_ids:
        return JsonResponse({"success": False, "error": "No valid customers found"}, status=400)

    existing = DailyEntry.objects.filter(
        tenant=tenant, entry_date=entry_date, meal_type=meal_type, customer_id__in=cust_ids
    )
    existing_map = {e.customer_id: e for e in existing}

    to_create = []
    for cid in cust_ids:
        if cid not in existing_map:
            to_create.append(DailyEntry(tenant=tenant, customer_id=cid, entry_date=entry_date, meal_type=meal_type))

    if to_create:
        DailyEntry.objects.bulk_create(to_create)

    all_entries = DailyEntry.objects.filter(
        tenant=tenant, entry_date=entry_date, meal_type=meal_type, customer_id__in=cust_ids
    ).select_related("customer").order_by("customer__name")

    results = [{"entry_id": e.id, "customer_id": e.customer_id, "customer_name": e.customer.name} for e in all_entries]
    return JsonResponse({"success": True, "count": len(results), "entries": results})

from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Prefetch

from .models import DailyEntry, OrderMealCustom  # adjust import path if needed


def _chunk_list(lst, n):
    if not n or n <= 0:
        return [lst]
    return [lst[i : i + n] for i in range(0, len(lst), n)]


@login_required
def print_stickers(request):
    tenant = _tenant(request)

    entry_date = request.GET.get("date") or str(date.today())
    meal_type = (request.GET.get("meal_type") or "LUNCH").upper()

    # per_page safe
    try:
        per_page = int(request.GET.get("per_page") or 10)
    except Exception:
        per_page = 10
    if per_page not in (6, 8, 10):
        per_page = 10

    # ✅ Prefetch ONLY custom items (source=CUSTOM)
    custom_items_qs = (
        OrderMealCustom.objects.filter(source="CUSTOM")
        .select_related("dish", "portion")
        .order_by("dish_name", "id")
    )

    entries = (
        DailyEntry.objects.filter(
            tenant=tenant,
            entry_date=entry_date,
            meal_type=meal_type,
        )
        .select_related("customer")
        .prefetch_related(
            "order_meals__meal",
            Prefetch("order_meals__custom_items", queryset=custom_items_qs),
        )
    )

    sticker_data = []
    for entry in entries:
        meal_groups = []

        for om in entry.order_meals.all():
            # ✅ now om.custom_items already contains ONLY CUSTOM because of Prefetch queryset
            custom_items = list(om.custom_items.all())

            # ✅ optional: skip meals with no CUSTOM items (so template items won't show at all)
            if not custom_items:
                continue

            meal_groups.append(
                {
                    "order_meal": om,
                    "meal_label": str(om),  # e.g. "Maharaja Meal x2"
                    "custom_items": custom_items,  # ONLY CUSTOM rows
                }
            )

        sticker_data.append({"entry": entry, "meal_groups": meal_groups})

    sticker_pages = _chunk_list(sticker_data, per_page)

    return render(
        request,
        "tiffin_app/print_stickers.html",
        {
            "sticker_data": sticker_data,     # kept (if template uses it)
            "sticker_pages": sticker_pages,   # for per-page printing
            "entry_date": entry_date,
            "meal_type": meal_type,
            "per_page": per_page,
        },
    )

# ---------------- payments ----------------
@login_required
@require_admin
def payments(request):
    tenant = _tenant(request)
    month = request.GET.get("month", date.today().strftime("%Y-%m"))

    year, month_num = map(int, month.split("-"))

    customers = Customer.objects.filter(tenant=tenant, is_active=True)
    customer_data = []

    total_raised = Decimal("0")
    total_received = Decimal("0")

    for customer in customers:
        raised = (
            DailyEntry.objects.filter(customer=customer, entry_date__year=year, entry_date__month=month_num)
            .aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0")
        )

        received = (
            Payment.objects.filter(customer=customer, payment_date__year=year, payment_date__month=month_num)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )

        last_payment = Payment.objects.filter(customer=customer).order_by("-payment_date").first()

        customer_data.append(
            {"customer": customer, "raised": raised, "received": received, "balance": raised - received, "last_payment": last_payment}
        )

        total_raised += raised
        total_received += received

    context = {
        "customer_data": customer_data,
        "total_raised": total_raised,
        "total_received": total_received,
        "outstanding": total_raised - total_received,
        "month": month,
    }
    return render(request, "tiffin_app/payments/dashboard.html", context)


@login_required
@require_admin
def payment_add(request):
    tenant = _tenant(request)

    if request.method == "POST":
        customer = get_object_or_404(Customer, pk=request.POST["customer"], tenant=tenant)
        Payment.objects.create(
            tenant=tenant,
            customer=customer,
            payment_date=request.POST["payment_date"],
            amount=request.POST["amount"],
            method=request.POST["method"],
            note=request.POST.get("note", ""),
        )
        messages.success(request, "Payment recorded successfully")
        return redirect("payments")

    customers = Customer.objects.filter(tenant=tenant, is_active=True)
    return render(request, "tiffin_app/payments/form.html", {"customers": customers, "today": str(date.today())})


# ---------------- reports ----------------
@login_required
@require_admin
def reports(request):
    tenant = _tenant(request)
    start_date = request.GET.get("start_date", str(date.today().replace(day=1)))
    end_date = request.GET.get("end_date", str(date.today()))

    entries = DailyEntry.objects.filter(tenant=tenant, entry_date__gte=start_date, entry_date__lte=end_date)

    total_orders = entries.count()
    total_revenue = entries.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    total_received = (
        Payment.objects.filter(tenant=tenant, payment_date__gte=start_date, payment_date__lte=end_date)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    lunch_count = entries.filter(meal_type="LUNCH").count()
    dinner_count = entries.filter(meal_type="DINNER").count()

    lunch_revenue = entries.filter(meal_type="LUNCH").aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    dinner_revenue = entries.filter(meal_type="DINNER").aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    top_customers = (
        Customer.objects.filter(orders__entry_date__gte=start_date, orders__entry_date__lte=end_date, tenant=tenant)
        .annotate(order_count=Count("orders"), total_spent=Sum("orders__total_amount"))
        .order_by("-total_spent")[:10]
    )

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_received": total_received,
        "outstanding": total_revenue - total_received,
        "lunch_count": lunch_count,
        "dinner_count": dinner_count,
        "lunch_revenue": lunch_revenue,
        "dinner_revenue": dinner_revenue,
        "top_customers": top_customers,
    }
    return render(request, "tiffin_app/reports/dashboard.html", context)


# ---------------- expenses: categories + items + API ----------------
@login_required
def expense_category_list(request):
    tenant = _tenant(request)
    qs = ExpenseCategory.objects.filter(tenant=tenant).order_by("name")
    return render(request, "tiffin_app/expenses/categories/list.html", {"categories": qs})


@login_required
def expense_category_create(request):
    tenant = _tenant(request)
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, "Category created.")
            return redirect("expense_category_list")
    else:
        form = ExpenseCategoryForm()
    return render(request, "tiffin_app/expenses/categories/form.html", {"form": form, "title": "Add Category"})


@login_required
def expense_category_edit(request, pk):
    tenant = _tenant(request)
    obj = get_object_or_404(ExpenseCategory, pk=pk, tenant=tenant)
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("expense_category_list")
    else:
        form = ExpenseCategoryForm(instance=obj)
    return render(request, "tiffin_app/expenses/categories/form.html", {"form": form, "title": "Edit Category"})


@login_required
def expense_category_delete(request, pk):
    tenant = _tenant(request)
    obj = get_object_or_404(ExpenseCategory, pk=pk, tenant=tenant)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Category deleted.")
        return redirect("expense_category_list")
    return render(request, "tiffin_app/expenses/categories/delete.html", {"category": obj})


@login_required
def expense_item_list(request):
    tenant = _tenant(request)
    qs = ExpenseItem.objects.filter(tenant=tenant).select_related("category").order_by("category__name", "name")
    return render(request, "tiffin_app/expenses/items/list.html", {"items": qs})


@login_required
def expense_item_create(request):
    tenant = _tenant(request)
    if request.method == "POST":
        form = ExpenseItemForm(request.POST, tenant=tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = tenant
            obj.save()
            messages.success(request, "Item created.")
            return redirect("expense_item_list")
    else:
        form = ExpenseItemForm(tenant=tenant)
    return render(request, "tiffin_app/expenses/items/form.html", {"form": form, "title": "Add Item"})


@login_required
def expense_item_edit(request, pk):
    tenant = _tenant(request)
    obj = get_object_or_404(ExpenseItem, pk=pk, tenant=tenant)
    if request.method == "POST":
        form = ExpenseItemForm(request.POST, instance=obj, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated.")
            return redirect("expense_item_list")
    else:
        form = ExpenseItemForm(instance=obj, tenant=tenant)
    return render(request, "tiffin_app/expenses/items/form.html", {"form": form, "title": "Edit Item"})


@login_required
def expense_item_delete(request, pk):
    tenant = _tenant(request)
    obj = get_object_or_404(ExpenseItem, pk=pk, tenant=tenant)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Item deleted.")
        return redirect("expense_item_list")
    return render(request, "tiffin_app/expenses/items/delete.html", {"item": obj})


@require_GET
@login_required
def expense_items_api(request):
    tenant = _tenant(request)
    category_id = request.GET.get("category_id")

    qs = ExpenseItem.objects.filter(tenant=tenant, is_active=True)
    if category_id:
        qs = qs.filter(category_id=category_id)

    qs = qs.select_related("category").order_by("name")

    data = [{
        "id": i.id,
        "name": i.name,
        "default_unit": i.default_unit,
        "category_id": i.category_id,
    } for i in qs]

    return JsonResponse({"success": True, "items": data})




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

