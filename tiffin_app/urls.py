from django.urls import path
from django.shortcuts import render
from . import views

def test_colors_view(request):
    return render(request, 'tiffin_app/test_colors.html')

urlpatterns = [
    # Auth
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Test
    path('test-colors', test_colors_view, name='test_colors'),

    # Customers
    path('customers', views.customer_list, name='customer_list'),
    path('customers/add', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/edit', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete', views.customer_delete, name='customer_delete'),

    # Dishes
    path('dishes', views.dish_list, name='dish_list'),
    path('dishes/add', views.dish_add, name='dish_add'),
    path('dishes/<int:pk>/edit', views.dish_edit, name='dish_edit'),
    path('dishes/<int:pk>/delete', views.dish_delete, name='dish_delete'),
    path('dishes/<int:pk>/portions', views.dish_portions, name='dish_portions'),
    path('dishes/<int:dish_pk>/portions/add', views.portion_add, name='portion_add'),
    path('portions/<int:pk>/delete', views.portion_delete, name='portion_delete'),

    # Meals
    path('meals', views.meal_list, name='meal_list'),
    path('meals/add', views.meal_add, name='meal_add'),
    path('meals/<int:pk>/edit', views.meal_edit, name='meal_edit'),
    path('meals/<int:pk>/delete', views.meal_delete, name='meal_delete'),
    path('meals/<int:pk>', views.meal_detail, name='meal_detail'),
    path('meals/<int:meal_pk>/items/add', views.meal_item_add, name='meal_item_add'),
    path('meal-items/<int:pk>/delete', views.meal_item_delete, name='meal_item_delete'),

    # ✅ Meals Bulk APIs
    path('meals/api/bulk-create/', views.meal_bulk_create, name='meal_bulk_create'),
    path('meals/<int:meal_pk>/items/bulk-add/', views.meal_items_bulk_add, name='meal_items_bulk_add'),

    # Daily Entry
    path('daily-entry', views.daily_entry_list, name='daily_entry_list'),
    path('daily-entry/add', views.daily_entry_add, name='daily_entry_add'),
    path('daily-entry/<int:pk>', views.daily_entry_detail, name='daily_entry_detail'),

    # ✅ single add (existing)
    path('daily-entry/<int:entry_pk>/meals/add', views.order_meal_add, name='order_meal_add'),

    # ✅ bulk add (NEW)
    path('daily-entry/<int:entry_pk>/meals/bulk-add/', views.order_meal_bulk_add, name='order_meal_bulk_add'),

    path('order-meals/<int:pk>/delete', views.order_meal_delete, name='order_meal_delete'),
    path('order-meals/<int:order_meal_pk>/items/add', views.custom_item_add, name='custom_item_add'),
    path('custom-items/<int:pk>/delete', views.custom_item_delete, name='custom_item_delete'),

    # (optional multi-customer create)
    path('daily-entry/api/bulk-create', views.daily_entry_bulk_create, name='daily_entry_bulk_create'),

    # Print Stickers
    path('print-stickers', views.print_stickers, name='print_stickers'),

    # Payments
    path('payments', views.payments, name='payments'),
    path('payments/add', views.payment_add, name='payment_add'),

    # Expenses main (your addon funcs assumed already in views.py or import)
    path('expenses/', views.expense_dashboard, name='expense_dashboard'),
    path('expenses/create/', views.expense_create_entry, name='expense_create'),
    path('expenses/<int:expense_id>/add-item/', views.expense_add_item, name='expense_add_item'),
    path('expenses/item/<int:item_id>/delete/', views.expense_delete_item, name='expense_delete_item'),
    path('expenses/report/', views.expense_monthly_report, name='expense_report'),
    path('expenses/download/', views.expense_download_csv, name='expense_download'),

    # ✅ Categories / Items
    path('expenses/categories/', views.expense_category_list, name='expense_category_list'),
    path('expenses/categories/add/', views.expense_category_create, name='expense_category_create'),
    path('expenses/categories/<int:pk>/edit/', views.expense_category_edit, name='expense_category_edit'),
    path('expenses/categories/<int:pk>/delete/', views.expense_category_delete, name='expense_category_delete'),

    path('expenses/items/', views.expense_item_list, name='expense_item_list'),
    path('expenses/items/add/', views.expense_item_create, name='expense_item_create'),
    path('expenses/items/<int:pk>/edit/', views.expense_item_edit, name='expense_item_edit'),
    path('expenses/items/<int:pk>/delete/', views.expense_item_delete, name='expense_item_delete'),

    path('expenses/api/items/', views.expense_items_api, name='expense_items_api'),


    path("api/daily-entries/summary-by-customer/", views.daily_entries_summary_by_customer_api,
        name="daily_entries_summary_by_customer_api"),

    path("api/daily-entries/by-customer/<int:customer_id>/", views.daily_entries_by_customer_api,
        name="daily_entries_by_customer_api"),



    path("daily-menu/", views.daily_menu_page, name="daily_menu_page"),
    path("daily-menu/api/get/", views.daily_menu_get_api, name="daily_menu_get_api"),
    path("daily-menu/api/save/", views.daily_menu_save_api, name="daily_menu_save_api"),
    path("daily-menu/list/", views.daily_menu_list, name="daily_menu_list"),


    path("customers/by-location/", views.customers_by_location, name="customers_by_location"),
    path("customers/by-location/list/", views.customers_by_location_list, name="customers_by_location_list"),
    
    # Reports
    path('reports', views.reports, name='reports'),
    path("reports/customer/<int:customer_id>/", views.report_customer_detail, name="report_customer_detail"),
    path("api/reports/customer/<int:customer_id>/entries/", views.report_customer_entries_api, name="report_customer_entries_api"),
]
