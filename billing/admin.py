from django.contrib import admin
from .models import (
    FirmSetting, Trader, FarmerBill, FarmerBillItem,
    TraderBill, TraderBillItem, GSTInvoice, PartyPayment,
    GeneralLedger, Expense
)

@admin.register(FirmSetting)
class FirmSettingAdmin(admin.ModelAdmin):
    list_display = ('firm_name', 'bardan_rate', 'market_fee_rate', 'commission_rate', 'initial_cash', 'initial_bank')

@admin.register(Trader)
class TraderAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile', 'village', 'gst_no', 'created_at')
    search_fields = ('name', 'mobile', 'village')

class FarmerBillItemInline(admin.TabularInline):
    model = FarmerBillItem
    extra = 1

@admin.register(FarmerBill)
class FarmerBillAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'date', 'farmer_name', 'village', 'bill_type', 'total_amount', 'paid_amount', 'payment_status')
    list_filter = ('bill_type', 'payment_status', 'date')
    search_fields = ('bill_no', 'farmer_name', 'mobile', 'village')
    inlines = [FarmerBillItemInline]

class TraderBillItemInline(admin.TabularInline):
    model = TraderBillItem
    extra = 1

@admin.register(TraderBill)
class TraderBillAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'date', 'trader_name', 'mode', 'bill_type', 'total_amount')
    list_filter = ('bill_type', 'mode', 'date')
    search_fields = ('bill_no', 'trader_name')
    inlines = [TraderBillItemInline]

@admin.register(GSTInvoice)
class GSTInvoiceAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'date', 'party_name', 'tax_type', 'base_amount', 'tax_amount', 'total_amount')
    list_filter = ('tax_type', 'date')
    search_fields = ('bill_no', 'party_name', 'party_gst')

@admin.register(PartyPayment)
class PartyPaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'party_type', 'party_name', 'amount', 'payment_mode', 'note')
    list_filter = ('party_type', 'payment_mode', 'date')
    search_fields = ('party_name', 'note')

@admin.register(GeneralLedger)
class GeneralLedgerAdmin(admin.ModelAdmin):
    list_display = ('date', 'party_name', 'description', 'entry_type', 'amount', 'payment_mode')
    list_filter = ('entry_type', 'payment_mode', 'date')
    search_fields = ('party_name', 'description')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'amount', 'payment_mode')
    list_filter = ('payment_mode', 'date')
    search_fields = ('title', 'description')
