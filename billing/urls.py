from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Print Views
    path('print/farmer/<int:bill_id>/', views.print_farmer_bill, name='print_farmer_bill'),
    path('print/trader/<int:bill_id>/', views.print_trader_bill, name='print_trader_bill'),
    path('print/gst/<int:bill_id>/', views.print_gst_bill, name='print_gst_bill'),

    # API Endpoints
    path('api/farmer-bill/save/', views.api_save_farmer_bill, name='api_save_farmer_bill'),
    path('api/farmer-bill/delete/<int:bill_id>/', views.api_delete_farmer_bill, name='api_delete_farmer_bill'),

    path('api/trader-bill/unbilled-items/', views.api_get_trader_unbilled_items, name='api_trader_unbilled_items'),
    path('api/trader-bill/save/', views.api_save_trader_bill, name='api_save_trader_bill'),
    path('api/trader-bill/delete/<int:bill_id>/', views.api_delete_trader_bill, name='api_delete_trader_bill'),

    path('api/gst-bill/save/', views.api_save_gst_bill, name='api_save_gst_bill'),
    path('api/gst-bill/delete/<int:bill_id>/', views.api_delete_gst_bill, name='api_delete_gst_bill'),

    path('api/ledger/summary/', views.api_get_ledger_summary, name='api_ledger_summary'),
    path('api/ledger/party-due/', views.api_get_party_due, name='api_party_due'),
    path('api/ledger/save-payment/', views.api_save_payment, name='api_save_payment'),
    path('api/ledger/save-entry/', views.api_save_ledger_entry, name='api_save_ledger_entry'),
    path('api/ledger/delete-entry/<int:entry_id>/', views.api_delete_ledger_entry, name='api_delete_ledger_entry'),

    path('api/daily/summary/', views.api_get_daily_summary, name='api_daily_summary'),

    path('api/expense/save/', views.api_save_expense, name='api_save_expense'),
    path('api/expense/delete/<int:expense_id>/', views.api_delete_expense, name='api_delete_expense'),

    path('api/settings/save/', views.api_save_settings, name='api_save_settings'),
    path('api/trader/add/', views.api_add_trader, name='api_add_trader'),
    path('api/trader/delete/<int:trader_id>/', views.api_delete_trader, name='api_delete_trader'),
]
