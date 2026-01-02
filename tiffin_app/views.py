import json
from django.db.models import Q
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import render
from .models import DailyEntry, OrderMealCustom  
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from .models import Dish, DailyMenu, DailyMenuItem
from datetime import date as dt_date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.dateparse import parse_date
import json
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, IntegerField
from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_date
from .models import DailyEntry, DailyMenu  # adjust import if needed
from datetime import date as dt_date
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_POST
import json
import csv

from datetime import date
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Value as V, Min
from django.db.models.functions import Lower, Trim, Coalesce
from django.shortcuts import render, redirect
from .models import Customer
from .models import DailyEntry, OrderMealCustom  # adjust import path if different
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
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ExpenseItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from .models import ExpenseCategory, ExpenseItem
from .expense_forms import ExpenseCategoryForm, ExpenseItemForm
from .models import Dish, DailyMenu, DailyMenuItem
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET
from datetime import date
from decimal import Decimal
from functools import wraps
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Prefetch
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from .models import DailyEntry, OrderMealCustom  
from .models import Customer, DailyEntry, DailyMenu, Dish, Meal
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


from django.db.models import Value as V, Case, When, IntegerField
from django.db.models.functions import Lower, Trim, Coalesce

def order_customers_by_location(qs):
    """
    ✅ Sort order:
      1) location blank LAST
      2) location A-Z
      3) Regular (daily_customer=True) first
      4) name A-Z
    """
    loc_raw = Trim(Coalesce("delivery_location", V("")))

    return (
        qs.annotate(_loc_raw=loc_raw, loc_key=Lower(loc_raw))
          .annotate(
              loc_blank=Case(
                  When(_loc_raw="", then=1),
                  default=0,
                  output_field=IntegerField(),
              )
          )
          .order_by("loc_blank", "loc_key", "-daily_customer", "name", "id")
    )


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



@login_required
@require_admin
def customer_list(request):
    tenant = _tenant(request)
    search = request.GET.get("search", "").strip()

    customers = Customer.objects.filter(tenant=tenant)

    if search:
        customers = customers.filter(
            Q(name__icontains=search)
            | Q(contact_number__icontains=search)
            | Q(delivery_location__icontains=search)
        )

    customers = order_customers_by_location(customers)


    return render(
        request,
        "tiffin_app/customers/list.html",
        {"customers": customers, "search": search},
    )



@login_required
@require_admin
def customer_add(request):
    if request.method == "POST":
        tenant = _tenant(request)
        meal_preference = request.POST.get("meal_preference") or "BOTH"

        Customer.objects.create(
            tenant=tenant,
            name=request.POST["name"],
            contact_number=request.POST.get("contact_number", ""),
            email=request.POST.get("email") or None,
            delivery_location=request.POST["delivery_location"],
            meal_preference=meal_preference,  # ✅ NEW
            daily_customer=request.POST.get("daily_customer") == "on",
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
        customer.meal_preference = request.POST.get("meal_preference") or "BOTH"
        customer.delivery_location = request.POST["delivery_location"]
        customer.daily_customer = request.POST.get("daily_customer") == "on"  # ✅ ADD
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
    if meal_type not in ("LUNCH", "DINNER", "BOTH"):
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


def _compact_items(items, max_items=5):
    items = [x for x in items if x]
    if len(items) <= max_items:
        return ", ".join(items) if items else "-"
    return ", ".join(items[:max_items]) + f" +{len(items) - max_items} more"


@login_required
def daily_entry_add(request):
    tenant = _tenant(request)

    # ✅ for GET reload (date/type change)
    entry_date_raw = request.GET.get("entry_date") or str(date.today())
    meal_type = (request.GET.get("meal_type") or "LUNCH").strip().upper()
    selected_menu_id = (request.GET.get("menu_id") or "").strip()

    entry_date_obj = parse_date(entry_date_raw) or date.today()
    entry_date = entry_date_obj.isoformat()

    if request.method == "POST":
        customer = get_object_or_404(Customer, pk=request.POST["customer"], tenant=tenant)
        entry_date_post = request.POST["entry_date"]
        meal_type_post = request.POST["meal_type"]
        menu_id = (request.POST.get("daily_menu") or "").strip()

        entry, created = DailyEntry.objects.get_or_create(
            tenant=tenant,
            customer=customer,
            entry_date=entry_date_post,
            meal_type=meal_type_post,
        )

        if created:
            messages.success(request, "Order created successfully")
        else:
            messages.info(request, "Order already exists, opening it")

        url = reverse("daily_entry_detail", kwargs={"pk": entry.pk})
        if menu_id:
            url = f"{url}?menu_id={menu_id}"
        return redirect(url)

    customers = order_customers_by_location(
    Customer.objects.filter(tenant=tenant, is_active=True)
    )

    allowed_types = [meal_type, "BOTH"] if meal_type in ("LUNCH", "DINNER") else ["BOTH"]

    menus_qs = (
        DailyMenu.objects.filter(tenant=tenant, date=entry_date_obj, meal_type__in=allowed_types)
        .prefetch_related("items__dish")
        .order_by("-id")
    )

    # ✅ Build display label: Menu Name + Items (NO meal_type in label)
    menus = []
    for m in menus_qs:
        item_names = []
        for it in m.items.all():
            if it.dish_id and it.dish:
                item_names.append(it.dish.name)
            elif it.dish_name:
                item_names.append(it.dish_name)

        menu_title = (m.menu_name or "").strip() or f"Menu #{m.id}"
        items_text = _compact_items(item_names, max_items=6)

        # optional: show short notes at end (NOT meal type)
        label = f"{menu_title} — {items_text}"
        if m.notes:
            label += f" ({m.notes[:25]}{'...' if len(m.notes) > 25 else ''})"

        menus.append(
            {
                "id": m.id,
                "label": label,
            }
        )

    return render(
        request,
        "tiffin_app/daily_entry/form.html",
        {
            "customers": customers,
            "today": str(date.today()),
            "entry_date": entry_date,
            "meal_type": meal_type,
            "menus": menus,  # ✅ list of dicts {id,label}
            "selected_menu_id": selected_menu_id,
        },
    )


@login_required
def daily_entry_detail(request, pk):
    tenant = _tenant(request)
    entry = get_object_or_404(DailyEntry, pk=pk, tenant=tenant)

    meals = Meal.objects.filter(
        tenant=tenant,
        is_active=True
    ).filter(
        Q(meal_type=entry.meal_type) | Q(meal_type="BOTH")
    )

    menu_id = (request.GET.get("menu_id") or "").strip()
    selected_menu = None

    # ✅ default all dishes
    dishes_qs = Dish.objects.filter(tenant=tenant, is_active=True)

    # ✅ if menu selected => dishes only from that menu
    if menu_id:
        selected_menu = get_object_or_404(
            DailyMenu,
            pk=menu_id,
            tenant=tenant,
            date=entry.entry_date,
            meal_type__in=[entry.meal_type, "BOTH"],  # ✅ allow BOTH menu for Lunch/Dinner order
        )

        dish_ids = selected_menu.items.values_list("dish_id", flat=True)
        dishes_qs = dishes_qs.filter(id__in=dish_ids)

    return render(
        request,
        "tiffin_app/daily_entry/detail.html",
        {
            "entry": entry,
            "meals": meals,
            "dishes": dishes_qs,
            "selected_menu": selected_menu,
        },
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
        )
        .filter(Q(meal_type=entry.meal_type) | Q(meal_type="BOTH"))
        .prefetch_related("template_items__dish", "template_items__portion")
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
    if meal_type not in ("LUNCH", "DINNER", "BOTH"):
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
    ).select_related("customer").order_by("customer__delivery_location", "customer__name", "id")


    results = [{"entry_id": e.id, "customer_id": e.customer_id, "customer_name": e.customer.name} for e in all_entries]
    return JsonResponse({"success": True, "count": len(results), "entries": results})


from datetime import date
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.shortcuts import render
from .models import DailyEntry, OrderMealCustom, DailyMenu, DailyMenuItem  # ✅ use your actual paths


def _chunk_list(lst, n):
    if not n or n <= 0:
        return [lst]
    return [lst[i : i + n] for i in range(0, len(lst), n)]


@login_required
def print_stickers(request):
    tenant = _tenant(request)

    entry_date = request.GET.get("date") or str(date.today())
    meal_type = (request.GET.get("meal_type") or "LUNCH").upper()

    layout_raw = (request.GET.get("layout") or request.GET.get("per_page") or "35").strip()
    try:
        per_page = int(layout_raw)
    except Exception:
        per_page = 35

    if per_page not in (35, 24, 12, 10, 8, 6):
        per_page = 35

    max_lines = {35: 3, 24: 6, 12: 10}.get(per_page, 999)

    # ✅ Prefetch CUSTOM items
    custom_items_qs = (
        OrderMealCustom.objects.filter(source="CUSTOM")
        .select_related("dish", "portion")
        .order_by("dish_name", "id")
    )

    # ✅ Prefetch DailyMenu items (for entry.menu)
    menu_items_qs = DailyMenuItem.objects.select_related("dish").order_by("id")

    entries = (
        DailyEntry.objects.filter(
            tenant=tenant,
            entry_date=entry_date,
            meal_type=meal_type,
        )
        .select_related("customer", "menu")  # ✅ FIXED: menu
        .prefetch_related(
            "order_meals__meal",
            Prefetch("order_meals__custom_items", queryset=custom_items_qs),
            Prefetch("menu__items", queryset=menu_items_qs),  # ✅ FIXED: menu__items
        )
        .order_by("customer__delivery_location", "customer__name", "id")
    )

    # ✅ Fallback menu (if entry.menu is null): pick tenant+date menu_type OR BOTH
    fallback_menu = (
        DailyMenu.objects.filter(
            tenant=tenant,
            date=entry_date,
        )
        .filter(Q(meal_type=meal_type) | Q(meal_type="BOTH"))
        .prefetch_related(Prefetch("items", queryset=menu_items_qs))
        .order_by(
            # exact meal_type first, then BOTH
            # (Django doesn't have easy bool order; this works with Case if you want,
            # but simple order_by('meal_type') isn't reliable. We'll do small logic below.)
            "id"
        )
    )

    # choose best fallback menu
    fallback_exact = None
    fallback_both = None
    for m in fallback_menu:
        if m.meal_type == meal_type and fallback_exact is None:
            fallback_exact = m
        if m.meal_type == "BOTH" and fallback_both is None:
            fallback_both = m
    fallback_menu_obj = fallback_exact or fallback_both

    sticker_data = []
    for entry in entries:
        items_map = OrderedDict()

        # ✅ 1) Daily Menu items ALWAYS print (entry.menu else fallback)
        menu_obj = entry.menu or fallback_menu_obj
        if menu_obj:
            for mi in menu_obj.items.all():
                name = (getattr(mi, "dish_name", "") or "").strip()
                if not name and getattr(mi, "dish_id", None):
                    name = (mi.dish.name or "").strip()
                if not name:
                    continue

                qty = getattr(mi, "qty", 1) or 1
                try:
                    qty = int(qty)
                except Exception:
                    qty = 1

                items_map[name] = items_map.get(name, 0) + qty

        # ✅ 2) Custom items (optional add-on)
        for om in entry.order_meals.all():
            for ci in om.custom_items.all():
                name = (getattr(ci, "dish_name", "") or "").strip()
                if not name and getattr(ci, "dish_id", None):
                    name = (ci.dish.name or "").strip()
                if not name:
                    continue

                qty = getattr(ci, "qty", 1) or 1
                try:
                    qty = int(qty)
                except Exception:
                    qty = 1

                items_map[name] = items_map.get(name, 0) + qty

        items = [{"dish_name": k, "qty": v} for k, v in items_map.items()]
        items_display = items[:max_lines]
        items_more_count = max(0, len(items) - len(items_display))

        sticker_data.append(
            {
                "entry": entry,
                "items": items,
                "items_display": items_display,
                "items_more_count": items_more_count,
            }
        )

    sticker_pages = _chunk_list(sticker_data, per_page)

    return render(
        request,
        "tiffin_app/print_stickers.html",
        {
            "sticker_pages": sticker_pages,
            "entry_date": entry_date,
            "meal_type": meal_type,
            "per_page": per_page,
        },
    )

@login_required
@require_admin
def payments(request):
    tenant = _tenant(request)
    month = request.GET.get("month", date.today().strftime("%Y-%m"))

    year, month_num = map(int, month.split("-"))

    customers = order_customers_by_location(
    Customer.objects.filter(tenant=tenant, is_active=True)
)

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

    customers = order_customers_by_location(
    Customer.objects.filter(tenant=tenant, is_active=True)
)
    return render(request, "tiffin_app/payments/form.html", {"customers": customers, "today": str(date.today())})


# ---------------- reports ----------------
from datetime import date
from decimal import Decimal
from django.db.models import Count, Sum
from django.shortcuts import render, get_object_or_404
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# ✅ your models
from .models import Customer, DailyEntry, Payment


@login_required
@require_admin
def reports(request):
    tenant = _tenant(request)

    # ✅ robust date parsing
    start_raw = request.GET.get("start_date") or str(date.today().replace(day=1))
    end_raw = request.GET.get("end_date") or str(date.today())

    start_obj = parse_date(start_raw) or date.today().replace(day=1)
    end_obj = parse_date(end_raw) or date.today()

    # ✅ if user gave reverse
    if end_obj < start_obj:
        start_obj, end_obj = end_obj, start_obj

    entries = DailyEntry.objects.filter(
        tenant=tenant,
        entry_date__gte=start_obj,
        entry_date__lte=end_obj,
    )

    total_orders = entries.count()
    total_revenue = entries.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    total_received = (
        Payment.objects.filter(
            tenant=tenant,
            payment_date__gte=start_obj,
            payment_date__lte=end_obj,
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )

    lunch_count = entries.filter(meal_type="LUNCH").count()
    dinner_count = entries.filter(meal_type="DINNER").count()

    lunch_revenue = entries.filter(meal_type="LUNCH").aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    dinner_revenue = entries.filter(meal_type="DINNER").aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    # ✅ Top customers in this range (with extra info)
    top_customers = (
        Customer.objects.filter(
            tenant=tenant,
            orders__entry_date__gte=start_obj,
            orders__entry_date__lte=end_obj,
        )
        .annotate(
            order_count=Count("orders", distinct=True),
            total_spent=Sum("orders__total_amount"),
        )
        .order_by("-total_spent")[:10]
    )

    # ✅ add avg per order (python-side)
    for c in top_customers:
        oc = c.order_count or 0
        ts = c.total_spent or Decimal("0")
        c.avg_order_value = (ts / oc) if oc else Decimal("0")

    context = {
        "start_date": start_obj.isoformat(),
        "end_date": end_obj.isoformat(),
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


# ✅ NEW: Customer detail PAGE (DailyEntry objects list)
@login_required
@require_admin
def report_customer_detail(request, customer_id):
    tenant = _tenant(request)

    start_raw = request.GET.get("start_date") or str(date.today().replace(day=1))
    end_raw = request.GET.get("end_date") or str(date.today())

    start_obj = parse_date(start_raw) or date.today().replace(day=1)
    end_obj = parse_date(end_raw) or date.today()

    if end_obj < start_obj:
        start_obj, end_obj = end_obj, start_obj

    customer = get_object_or_404(Customer, tenant=tenant, id=customer_id)

    entries = (
        DailyEntry.objects.filter(
            tenant=tenant,
            customer=customer,
            entry_date__gte=start_obj,
            entry_date__lte=end_obj,
        )
        .select_related("menu")
        .prefetch_related("order_meals__meal")
        .order_by("-entry_date", "meal_type", "-id")
    )

    total_orders = entries.count()
    total_spent = entries.aggregate(s=Sum("total_amount"))["s"] or Decimal("0")

    lunch_count = entries.filter(meal_type="LUNCH").count()
    dinner_count = entries.filter(meal_type="DINNER").count()

    avg_order_value = (total_spent / total_orders) if total_orders else Decimal("0")

    return render(
        request,
        "tiffin_app/reports/customer_detail.html",
        {
            "start_date": start_obj.isoformat(),
            "end_date": end_obj.isoformat(),
            "customer": customer,
            "entries": entries,
            "total_orders": total_orders,
            "total_spent": total_spent,
            "avg_order_value": avg_order_value,
            "lunch_count": lunch_count,
            "dinner_count": dinner_count,
        },
    )


# ✅ NEW: API (same data JSON)
@require_GET
@login_required
@require_admin
def report_customer_entries_api(request, customer_id):
    tenant = _tenant(request)

    start_obj = parse_date(request.GET.get("start_date") or "")
    end_obj = parse_date(request.GET.get("end_date") or "")
    if not start_obj or not end_obj:
        return JsonResponse({"success": False, "error": "start_date and end_date required (YYYY-MM-DD)"}, status=400)
    if end_obj < start_obj:
        start_obj, end_obj = end_obj, start_obj

    customer = get_object_or_404(Customer, tenant=tenant, id=customer_id)

    entries = (
        DailyEntry.objects.filter(
            tenant=tenant,
            customer=customer,
            entry_date__gte=start_obj,
            entry_date__lte=end_obj,
        )
        .select_related("menu")
        .prefetch_related("order_meals__meal")
        .order_by("entry_date", "meal_type", "id")
    )

    out = []
    for e in entries:
        out.append({
            "id": e.id,
            "entry_date": e.entry_date.isoformat(),
            "meal_type": e.meal_type,
            "total_amount": str(e.total_amount),
            "menu": None if not e.menu_id else {
                "id": e.menu_id,
                "menu_name": e.menu.menu_name or f"Menu #{e.menu_id}",
                "meal_type": e.menu.meal_type,
            },
            "order_meals": [
                {
                    "id": om.id,
                    "meal_id": om.meal_id,
                    "meal_name": om.meal.name,
                    "qty": om.qty,
                    "unit_price": str(om.unit_price),
                    "total_price": str(om.total_price),
                }
                for om in e.order_meals.all()
            ],
        })

    total_spent = entries.aggregate(s=Sum("total_amount"))["s"] or Decimal("0")

    return JsonResponse({
        "success": True,
        "start_date": start_obj.isoformat(),
        "end_date": end_obj.isoformat(),
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "delivery_location": customer.delivery_location,
            "contact_number": customer.contact_number,
            "meal_preference": customer.meal_preference,
            "daily_customer": customer.daily_customer,
        },
        "count": len(out),
        "total_spent": str(total_spent),
        "entries": out,
    })



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




@login_required
def daily_menu_page(request):
    """
    HTML page: create/update DailyMenu + Items
    """
    tenant = _tenant(request)

    # (Optional) only admin
    if request.user.profile.role != "ADMIN":
        return JsonResponse({"detail": "Access denied"}, status=403)

    dishes = Dish.objects.filter(tenant=tenant, is_active=True).order_by("name")
    return render(
        request,
        "tiffin_app/daily_menu/form.html",
        {
            "today": dt_date.today().isoformat(),
            "dishes": dishes,
        },
    )


@require_GET
@login_required
def daily_menu_get_api(request):
    tenant = _tenant(request)
    if request.user.profile.role != "ADMIN":
        return JsonResponse({"success": False, "error": "Access denied"}, status=403)

    d = parse_date(request.GET.get("date") or "")
    meal_type = (request.GET.get("meal_type") or "LUNCH").strip().upper()
    menu_id = (request.GET.get("menu_id") or "").strip()

    if not d:
        return JsonResponse({"success": False, "error": "Invalid date"}, status=400)
    if meal_type not in ("LUNCH", "DINNER", "BOTH"):
        return JsonResponse({"success": False, "error": "Invalid meal_type"}, status=400)

    # ✅ if LUNCH/DINNER => include BOTH menus also
    allowed_types = ["BOTH"] if meal_type == "BOTH" else [meal_type, "BOTH"]

    qs = (
        DailyMenu.objects.filter(tenant=tenant, date=d, meal_type__in=allowed_types)
        .prefetch_related("items__dish")
        .order_by("-id")
    )

    menus_list = [
        {"id": m.id, "menu_name": (m.menu_name or f"Menu #{m.id}"), "meal_type": m.meal_type, "notes": (m.notes or "")}
        for m in qs
    ]

    if not menu_id:
        return JsonResponse({"success": True, "menus": menus_list, "menu": None})

    menu = get_object_or_404(DailyMenu, pk=menu_id, tenant=tenant, date=d)
    # ensure selected menu is in allowed types
    if menu.meal_type not in allowed_types:
        return JsonResponse({"success": False, "error": "Menu not allowed for selected meal_type"}, status=400)

    items = []
    for it in menu.items.all():
        items.append(
            {
                "dish_id": it.dish_id,
                "dish_name": it.dish.name if it.dish_id else (it.dish_name or ""),
                "qty": it.qty,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "menus": menus_list,
            "menu": {
                "id": menu.id,
                "date": menu.date.isoformat(),
                "meal_type": menu.meal_type,
                "menu_name": menu.menu_name or "",
                "notes": menu.notes or "",
                "items": items,
            },
        }
    )



@require_POST
@login_required
@transaction.atomic
def daily_menu_save_api(request):
    tenant = _tenant(request)
    if request.user.profile.role != "ADMIN":
        return JsonResponse({"success": False, "error": "Access denied"}, status=403)

    if "application/json" not in (request.content_type or ""):
        return JsonResponse({"success": False, "error": "Send JSON"}, status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    d = parse_date(payload.get("date") or "")
    meal_type = (payload.get("meal_type") or "").strip().upper()
    notes = (payload.get("notes") or "").strip()

    # ✅ normalize name -> None if empty
    raw_name = (payload.get("menu_name") or "").strip()
    menu_name = raw_name if raw_name else None

    menu_id = payload.get("menu_id")  # optional
    rows = payload.get("items") or []

    if not d:
        return JsonResponse({"success": False, "error": "Invalid date"}, status=400)
    if meal_type not in ("LUNCH", "DINNER", "BOTH"):
        return JsonResponse({"success": False, "error": "Invalid meal_type"}, status=400)
    if not isinstance(rows, list) or len(rows) == 0:
        return JsonResponse({"success": False, "error": "At least 1 item required"}, status=400)

    try:
        # ✅ update existing
        if menu_id:
            menu = get_object_or_404(DailyMenu, pk=menu_id, tenant=tenant)

            if menu.date != d:
                return JsonResponse({"success": False, "error": "menu_id does not match date"}, status=400)

            menu.meal_type = meal_type
            menu.notes = notes
            menu.menu_name = menu_name
            menu.save()
            created = False

        # ✅ create new
        else:
            menu = DailyMenu.objects.create(
                tenant=tenant,
                date=d,
                meal_type=meal_type,
                notes=notes,
                menu_name=menu_name,
            )
            created = True

    except IntegrityError:
        return JsonResponse(
            {
                "success": False,
                "error": "Same Menu Name already exists for this Date + Meal Type. Please change Menu Name or select existing menu."
            },
            status=400,
        )

    # replace items
    menu.items.all().delete()

    def to_int(v, default=1):
        try:
            x = int(v)
            return x if x > 0 else default
        except Exception:
            return default

    dish_ids = []
    for r in rows:
        try:
            did = int(r.get("dish_id")) if r.get("dish_id") not in (None, "", "null") else None
        except Exception:
            did = None
        if did:
            dish_ids.append(did)
    dish_ids = list(set(dish_ids))

    dish_map = {
        dobj.id: dobj
        for dobj in Dish.objects.filter(tenant=tenant, is_active=True, id__in=dish_ids)
    }

    items_to_create = []
    for idx, r in enumerate(rows, start=1):
        try:
            did = int(r.get("dish_id")) if r.get("dish_id") not in (None, "", "null") else None
        except Exception:
            did = None

        dish_name = (r.get("dish_name") or "").strip()
        qty = to_int(r.get("qty"), default=1)

        if did:
            if did not in dish_map:
                return JsonResponse({"success": False, "error": f"Invalid dish_id in row #{idx}"}, status=400)
            dish_obj = dish_map[did]
        else:
            if not dish_name:
                return JsonResponse({"success": False, "error": f"Dish required in row #{idx}"}, status=400)

            existing = Dish.objects.filter(tenant=tenant, name__iexact=dish_name).first()
            if existing:
                dish_obj = existing
            else:
                dish_obj = Dish.objects.create(
                    tenant=tenant,
                    name=dish_name,
                    category="OTHER",
                    meal_category=meal_type,  # BOTH ok
                    food_type="VEG",
                    availability="AVAILABLE",
                    is_active=True,
                )

        items_to_create.append(DailyMenuItem(daily_menu=menu, dish=dish_obj, qty=qty))

    DailyMenuItem.objects.bulk_create(items_to_create)

    return JsonResponse(
        {"success": True, "menu_id": menu.id, "created": created, "items_created": len(items_to_create)}
    )



@login_required
@require_admin
def daily_menu_list(request):
    tenant = _tenant(request)

    # ✅ start_date default today
    start_raw = (request.GET.get("start_date") or "").strip()
    end_raw = (request.GET.get("end_date") or "").strip()

    start_date = parse_date(start_raw) or dt_date.today()
    end_date = parse_date(end_raw) if end_raw else None

    # ✅ if only start provided => same day
    if not end_date:
        end_date = start_date

    # ✅ if end < start => swap
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    meal_type = (request.GET.get("meal_type") or "").strip().upper()  # LUNCH/DINNER/BOTH/""
    q = (request.GET.get("q") or "").strip()

    qs = (
        DailyMenu.objects.filter(tenant=tenant, date__range=[start_date, end_date])
        .prefetch_related("items__dish")
        .order_by("date", "meal_type", "id")
    )

    if meal_type in ("LUNCH", "DINNER", "BOTH"):
        qs = qs.filter(meal_type=meal_type)

    if q:
        qs = qs.filter(menu_name__icontains=q)

    menus = []
    for m in qs:
        items = []
        for it in m.items.all():
            if it.dish_id:
                items.append(it.dish.name)
            elif getattr(it, "dish_name", None):
                items.append(it.dish_name)

        menus.append(
            {
                "id": m.id,
                "date": m.date,
                "meal_type": m.meal_type,
                "menu_name": m.menu_name or f"Menu #{m.id}",
                "notes": m.notes or "",
                "items_text": ", ".join(items) if items else "-",
            }
        )

    return render(
        request,
        "tiffin_app/daily_menu/list.html",
        {
            "today": dt_date.today().isoformat(),
            "selected_start_date": start_date.isoformat(),
            "selected_end_date": end_raw,  # keep blank if user didn't enter
            "selected_meal_type": meal_type,  # "" means All
            "q": q,
            "menus": menus,
        },
    )




@login_required
def customers_by_location(request):
    tenant = _tenant(request)

    q = (request.GET.get("q") or "").strip()
    sort = (request.GET.get("sort") or "count_desc").strip()

    # normalize location key: lower(trim(coalesce(delivery_location,"")))
    base = (
        Customer.objects.filter(tenant=tenant)
        .annotate(loc_key=Lower(Trim(Coalesce("delivery_location", V("")))))
    )

    if q:
        base = base.filter(loc_key__contains=q.lower())

    rows = (
        base.values("loc_key")
        .annotate(
            total=Count("id"),
            daily_yes=Count("id", filter=Q(daily_customer=True)),
            daily_no=Count("id", filter=Q(daily_customer=False)),
            sample_display=Min("delivery_location"),
        )
    )

    # sorting
    if sort == "count_asc":
        rows = rows.order_by("total", "loc_key")
    elif sort == "az":
        rows = rows.order_by("loc_key")
    elif sort == "za":
        rows = rows.order_by("-loc_key")
    else:  # count_desc (default)
        rows = rows.order_by("-total", "loc_key")

    # final normalize display text in python (clean)
    out = []
    for r in rows:
        key = (r.get("loc_key") or "").strip()
        display = (r.get("sample_display") or "").strip()
        if not key:
            display = "(No Location)"
            key = ""
        else:
            display = display or key

        out.append(
            {
                "loc_key": key,
                "display": display,
                "total": r["total"],
                "daily_yes": r["daily_yes"],
                "daily_no": r["daily_no"],
                "list_url": f"{request.build_absolute_uri('/').rstrip('/')}"
                           f"{'/customers/by-location/list/?loc_key='}{quote(key)}",
            }
        )

    return render(
        request,
        "tiffin_app/customers/by_location.html",
        {
            "rows": out,
            "q": q,
            "sort": sort,
        },
    )


@login_required
def customers_by_location_list(request):
    tenant = _tenant(request)

    loc_key = (request.GET.get("loc_key") or "").strip().lower()
    if loc_key is None:
        loc_key = ""

    q = (request.GET.get("q") or "").strip()
    daily = (request.GET.get("daily") or "all").strip()  # all | yes | no
    sort = (request.GET.get("sort") or "name_az").strip()

    qs = (
        Customer.objects.filter(tenant=tenant)
        .annotate(loc_key=Lower(Trim(Coalesce("delivery_location", V("")))))
        .filter(loc_key=loc_key)
    )

    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(delivery_location__icontains=q)
            | Q(contact_number__icontains=q) # if exists
        )

    if daily == "yes":
        qs = qs.filter(daily_customer=True)
    elif daily == "no":
        qs = qs.filter(daily_customer=False)

    if sort == "name_za":
        qs = qs.order_by("-name", "id")
    elif sort == "daily_yes_first":
        qs = qs.order_by("-daily_customer", "name", "id")
    else:  # name_az default
        qs = qs.order_by("name", "id")

    # display title
    location_title = "(No Location)" if loc_key == "" else loc_key.upper()

    return render(
        request,
        "tiffin_app/customers/by_location_list.html",
        {
            "location_title": location_title,
            "loc_key": loc_key,
            "customers": qs,
            "q": q,
            "daily": daily,
            "sort": sort,
            "total": qs.count(),
        },
    )



from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_date
from django.db.models import Count, Sum
from django.http import JsonResponse
from datetime import date as dt_date

@require_GET
@login_required
@require_admin
def daily_entries_summary_by_customer_api(request):
    tenant = _tenant(request)

    start = parse_date(request.GET.get("start_date") or "")
    end = parse_date(request.GET.get("end_date") or "")

    if not start or not end:
        return JsonResponse({"success": False, "error": "start_date and end_date required (YYYY-MM-DD)"}, status=400)

    if start > end:
        return JsonResponse({"success": False, "error": "start_date cannot be after end_date"}, status=400)

    qs = (
        DailyEntry.objects.filter(tenant=tenant, entry_date__gte=start, entry_date__lte=end)
        .values(
            "customer_id",
            "customer__name",
            "customer__delivery_location",
            "customer__contact_number",
            "customer__meal_preference",
        )
        .annotate(
            entry_count=Count("id"),
            total_amount=Sum("total_amount"),
        )
        .order_by("-entry_count", "customer__name")
    )

    rows = []
    for r in qs:
        rows.append({
            "customer_id": r["customer_id"],
            "name": r["customer__name"],
            "delivery_location": r["customer__delivery_location"],
            "contact_number": r["customer__contact_number"],
            "meal_preference": r["customer__meal_preference"],
            "entry_count": r["entry_count"],
            "total_amount": str(r["total_amount"] or 0),
            "details_api": f"/api/daily-entries/by-customer/{r['customer_id']}/?start_date={start.isoformat()}&end_date={end.isoformat()}",
        })

    return JsonResponse({
        "success": True,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "rows": rows,
    })


@require_GET
@login_required
@require_admin
def daily_entries_by_customer_api(request, customer_id):
    tenant = _tenant(request)

    start = parse_date(request.GET.get("start_date") or "")
    end = parse_date(request.GET.get("end_date") or "")

    if not start or not end:
        return JsonResponse({"success": False, "error": "start_date and end_date required (YYYY-MM-DD)"}, status=400)

    if start > end:
        return JsonResponse({"success": False, "error": "start_date cannot be after end_date"}, status=400)

    customer = get_object_or_404(Customer, tenant=tenant, id=customer_id)

    entries = (
        DailyEntry.objects.filter(
            tenant=tenant,
            customer=customer,
            entry_date__gte=start,
            entry_date__lte=end,
        )
        .select_related("menu")
        .prefetch_related("order_meals__meal")
        .order_by("entry_date", "meal_type", "id")
    )

    out = []
    for e in entries:
        out.append({
            "id": e.id,
            "entry_date": e.entry_date.isoformat(),
            "meal_type": e.meal_type,
            "total_amount": str(e.total_amount),
            "menu": None if not e.menu_id else {
                "id": e.menu_id,
                "menu_name": e.menu.menu_name or f"Menu #{e.menu_id}",
                "meal_type": e.menu.meal_type,
            },
            "order_meals": [
                {
                    "id": om.id,
                    "meal_id": om.meal_id,
                    "meal_name": om.meal.name,
                    "qty": om.qty,
                    "unit_price": str(om.unit_price),
                    "total_price": str(om.total_price),
                }
                for om in e.order_meals.all()
            ],
        })

    return JsonResponse({
        "success": True,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "delivery_location": customer.delivery_location,
            "meal_preference": customer.meal_preference,
        },
        "count": len(out),
        "entries": out,
    })

