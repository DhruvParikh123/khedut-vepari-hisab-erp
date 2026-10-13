import json
from decimal import Decimal
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.core import serializers
from .models import (
    FirmSetting, Trader, FarmerBill, FarmerBillItem,
    TraderBill, TraderBillItem, GSTInvoice, PartyPayment,
    GeneralLedger, Expense
)


def api_login_required(view_func):
    """Decorator for JSON API endpoints ensuring the user is authenticated."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'સત્ર સમાપ્ત થયેલ છે. કૃપા કરીને ફરી લૉગ ઇન કરો. (Login required)'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def get_current_settings():
    return FirmSetting.get_settings()


def calculate_balances():
    st = get_current_settings()
    init_cash = Decimal(st.initial_cash or 0)
    init_bank = Decimal(st.initial_bank or 0)

    # Cash Calculations
    # Farmer Bill paid directly
    farmer_bills_cash_paid = FarmerBill.objects.filter(payment_mode='cash').aggregate(s=Sum('paid_amount'))['s'] or Decimal(0)
    farmer_payments_cash = PartyPayment.objects.filter(party_type='farmer', payment_mode='cash').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    trader_payments_cash = PartyPayment.objects.filter(party_type='trader', payment_mode='cash').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    ledger_cash_jama = GeneralLedger.objects.filter(entry_type='jama', payment_mode='cash').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    ledger_cash_udhar = GeneralLedger.objects.filter(entry_type='udhar', payment_mode='cash').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    expense_cash = Expense.objects.filter(payment_mode='cash').aggregate(s=Sum('amount'))['s'] or Decimal(0)

    cash_balance = (init_cash + trader_payments_cash + ledger_cash_jama) - (farmer_bills_cash_paid + farmer_payments_cash + ledger_cash_udhar + expense_cash)

    # Bank Calculations
    farmer_bills_bank_paid = FarmerBill.objects.filter(payment_mode='bank').aggregate(s=Sum('paid_amount'))['s'] or Decimal(0)
    farmer_payments_bank = PartyPayment.objects.filter(party_type='farmer', payment_mode='bank').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    trader_payments_bank = PartyPayment.objects.filter(party_type='trader', payment_mode='bank').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    ledger_bank_jama = GeneralLedger.objects.filter(entry_type='jama', payment_mode='bank').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    ledger_bank_udhar = GeneralLedger.objects.filter(entry_type='udhar', payment_mode='bank').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    expense_bank = Expense.objects.filter(payment_mode='bank').aggregate(s=Sum('amount'))['s'] or Decimal(0)

    bank_balance = (init_bank + trader_payments_bank + ledger_bank_jama) - (farmer_bills_bank_paid + farmer_payments_bank + ledger_bank_udhar + expense_bank)

    return {
        'cash_balance': cash_balance,
        'bank_balance': bank_balance,
    }


def login_view(request):
    """Authentication view for logging in users."""
    if request.user.is_authenticated:
        return redirect('billing:index')

    st = get_current_settings()
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')
        next_post = request.POST.get('next', '')

        if not username or not password:
            messages.error(request, "કૃપા કરીને યુઝરનેમ અને પાસવર્ડ બંને દાખલ કરો.")
            return render(request, 'billing/login.html', {
                'st': st,
                'next': next_post or next_url,
                'username': username
            })

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(30 * 86400)

                messages.success(request, f"સ્વાગત છે, {user.first_name or user.username}! સફળતાપૂર્વક લૉગ ઇન થયા છો.")
                redirect_target = next_post or next_url
                if redirect_target and redirect_target.startswith('/'):
                    return redirect(redirect_target)
                return redirect('billing:index')
            else:
                messages.error(request, "આ એકાઉન્ટ નિષ્ક્રિય છે. કૃપા કરીને એડમિનનો સંપર્ક કરો.")
        else:
            messages.error(request, "ખોટું યુઝરનેમ અથવા પાસવર્ડ! કૃપા કરીને ફરી પ્રયાસ કરો.")
            return render(request, 'billing/login.html', {
                'st': st,
                'next': next_post or next_url,
                'username': username
            })

    return render(request, 'billing/login.html', {
        'st': st,
        'next': next_url
    })


def logout_view(request):
    """View to log out the authenticated user."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "તમે સફળતાપૂર્વક લૉગ આઉટ થયા છો. (Logged out successfully)")
    return redirect('billing:login')


def register_view(request):
    """View to register a new user in the system."""
    if request.user.is_authenticated:
        return redirect('billing:index')

    st = get_current_settings()

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        context = {
            'st': st,
            'full_name': full_name,
            'username': username,
            'email': email,
        }

        # Validations
        if not username or not password or not confirm_password:
            messages.error(request, "કૃપા કરીને યુઝરનેમ અને પાસવર્ડ બંને વિગતો દાખલ કરો.")
            return render(request, 'billing/register.html', context)

        if len(username) < 3:
            messages.error(request, "યુઝરનેમ ઓછામાં ઓછું 3 અક્ષરનું હોવું જોઈએ.")
            return render(request, 'billing/register.html', context)

        if len(password) < 4:
            messages.error(request, "પાસવર્ડ ઓછામાં ઓછો 4 અક્ષરનો હોવો જોઈએ.")
            return render(request, 'billing/register.html', context)

        if password != confirm_password:
            messages.error(request, "બંને પાસવર્ડ મેળ ખાતા નથી! કૃપા કરીને ફરી તપાસો.")
            return render(request, 'billing/register.html', context)

        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, f"'{username}' નામથી એકાઉન્ટ પહેલેથી જ હાજર છે. કૃપા કરીને બીજું યુઝરનેમ પસંદ કરો.")
            return render(request, 'billing/register.html', context)

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name
            )
            # Log in the user immediately
            login(request, user)
            messages.success(request, f"અભિનંદન! નવું એકાઉન્ટ '{user.username}' સફળતાપૂર્વક બની ગયું છે.")
            return redirect('billing:index')
        except Exception as e:
            messages.error(request, f"એકાઉન્ટ બનાવતી વખતે ભૂલ આવી: {str(e)}")
            return render(request, 'billing/register.html', context)

    return render(request, 'billing/register.html', {'st': st})


@login_required
def index_view(request):
    """Unified application view containing all features in one cohesive, responsive interface matching khedut_vepari_hisab_gst_corrected.html but powered by Django database."""
    st = get_current_settings()
    traders = Trader.objects.all().order_by('name')
    farmer_bills = FarmerBill.objects.all().order_by('-date', '-id')[:20]
    trader_bills = TraderBill.objects.all().order_by('-date', '-id')[:20]
    gst_bills = GSTInvoice.objects.all().order_by('-date', '-id')[:20]
    ledger_entries = GeneralLedger.objects.all().order_by('-date', '-id')[:20]
    expenses = Expense.objects.all().order_by('-date', '-id')[:20]
    payments = PartyPayment.objects.all().order_by('-date', '-id')[:20]
    farmers = FarmerBill.objects.values_list('farmer_name', flat=True).distinct().order_by('farmer_name')

    balances = calculate_balances()
    today = timezone.now().date()

    # Next bill numbers
    today_str = today.strftime("%y%m%d")
    next_fb_no = f"FB-{today_str}-{FarmerBill.objects.count() + 1}"
    next_tb_no = f"TB-{today_str}-{TraderBill.objects.count() + 1}"
    next_gst_no = f"GST-{today_str}-{GSTInvoice.objects.count() + 1}"

    total_liquidity = balances['cash_balance'] + balances['bank_balance']
    farmer_bills_count = FarmerBill.objects.count()
    trader_bills_count = TraderBill.objects.count()
    gst_bills_count = GSTInvoice.objects.count()
    total_farmer_purchases = FarmerBill.objects.aggregate(s=Sum('total_amount'))['s'] or Decimal(0)
    total_trader_sales = TraderBill.objects.aggregate(s=Sum('total_amount'))['s'] or Decimal(0)

    context = {
        'st': st,
        'traders': traders,
        'farmers': farmers,
        'farmer_bills': farmer_bills,
        'trader_bills': trader_bills,
        'gst_bills': gst_bills,
        'ledger_entries': ledger_entries,
        'expenses': expenses,
        'payments': payments,
        'cash_balance': balances['cash_balance'],
        'bank_balance': balances['bank_balance'],
        'total_liquidity': total_liquidity,
        'farmer_bills_count': farmer_bills_count,
        'trader_bills_count': trader_bills_count,
        'gst_bills_count': gst_bills_count,
        'total_farmer_purchases': total_farmer_purchases,
        'total_trader_sales': total_trader_sales,
        'today': today.isoformat(),
        'next_fb_no': next_fb_no,
        'next_tb_no': next_tb_no,
        'next_gst_no': next_gst_no,
    }
    return render(request, 'billing/index.html', context)


# ------------------- API: FARMER BILL -------------------

@api_login_required
@require_http_methods(["POST"])
def api_save_farmer_bill(request):
    try:
        data = json.loads(request.body)
        bill_no = data.get('no') or f"FB-{int(timezone.now().timestamp())}"
        date_val = data.get('date') or timezone.now().date()
        firm_name = data.get('firm') or get_current_settings().firm_name
        farmer_name = data.get('name', '').strip()
        if not farmer_name:
            return JsonResponse({'success': False, 'error': 'ખેડૂતનું નામ જરૂરી છે.'}, status=400)

        mobile = data.get('mobile', '').strip()
        village = data.get('village', '').strip()
        plot_no = data.get('plot', '').strip()
        bill_type = data.get('kind', 'કાચું')

        bardan = Decimal(str(data.get('bard', 0)))
        lab = Decimal(str(data.get('lab', 0)))
        ded = Decimal(str(data.get('ded', 0)))
        gst_rate = Decimal(str(data.get('vat', 0)))
        paid = Decimal(str(data.get('paid', 0)))
        pay_status = data.get('status', 'due')
        pay_mode = data.get('mode', 'cash')

        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({'success': False, 'error': 'ઓછામાં ઓછી એક માલની વિગત ઉમેરો.'}, status=400)

        base_amt = Decimal(0)
        calculated_items = []
        for it in items_data:
            bags = Decimal(str(it.get('bags', 0)))
            w = Decimal(str(it.get('weight', 0)))
            rate = Decimal(str(it.get('rate', 0)))
            amount = round((w * rate) / Decimal(20), 2)
            base_amt += amount
            calculated_items.append({
                'item_type': it.get('type', 'તમાકુ') or 'તમાકુ',
                'trader_name': it.get('trader', '').strip(),
                'bags': bags,
                'weight': w,
                'rate': rate,
                'amount': amount
            })

        sub = base_amt + bardan + lab - ded
        tax = Decimal(0)
        if bill_type == 'GST':
            tax = round((sub * gst_rate) / Decimal(100), 2)
        total = sub + tax

        paid = min(total, paid)
        if paid >= total:
            pay_status = 'paid'

        bill = FarmerBill.objects.create(
            bill_no=bill_no,
            date=date_val,
            firm_name=firm_name,
            farmer_name=farmer_name,
            mobile=mobile,
            village=village,
            plot_no=plot_no,
            bill_type=bill_type,
            base_amount=base_amt,
            bardan_amount=bardan,
            labor=lab,
            deduction=ded,
            gst_rate=gst_rate,
            tax_amount=tax,
            total_amount=total,
            paid_amount=paid,
            payment_status=pay_status,
            payment_mode=pay_mode,
        )

        for ci in calculated_items:
            FarmerBillItem.objects.create(
                bill=bill,
                item_type=ci['item_type'],
                trader_name=ci['trader_name'],
                bags=ci['bags'],
                weight=ci['weight'],
                rate=ci['rate'],
                amount=ci['amount'],
            )
            # Ensure trader name exists in master
            if ci['trader_name']:
                Trader.objects.get_or_create(name=ci['trader_name'])

        return JsonResponse({'success': True, 'bill_id': bill.id, 'bill_no': bill.bill_no})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_delete_farmer_bill(request, bill_id):
    bill = get_object_or_404(FarmerBill, id=bill_id)
    bill.delete()
    return JsonResponse({'success': True})


# ------------------- API: TRADER BILL -------------------

@api_login_required
@require_http_methods(["GET"])
def api_get_trader_unbilled_items(request):
    trader_name = request.GET.get('trader', '').strip()
    if not trader_name:
        return JsonResponse({'items': []})

    # Find farmer bill items assigned to this trader
    items = FarmerBillItem.objects.filter(trader_name=trader_name).select_related('bill').order_by('-bill__date', '-bill__id')
    result = []
    for item in items:
        result.append({
            'item_id': item.id,
            'bill_id': item.bill.id,
            'bill_no': item.bill.bill_no,
            'date': item.bill.date.isoformat(),
            'farmer_name': item.bill.farmer_name,
            'village': item.bill.village,
            'item_type': item.item_type,
            'bags': float(item.bags),
            'weight': float(item.weight),
            'rate': float(item.rate),
            'amount': float(item.amount),
        })
    return JsonResponse({'items': result})


@api_login_required
@require_http_methods(["POST"])
def api_save_trader_bill(request):
    try:
        data = json.loads(request.body)
        bill_no = data.get('no') or f"TB-{int(timezone.now().timestamp())}"
        date_val = data.get('date') or timezone.now().date()
        st = get_current_settings()
        firm_name = data.get('firm') or st.firm_name
        trader_name = data.get('trader', '').strip()
        if not trader_name:
            return JsonResponse({'success': False, 'error': 'વેપારીનું નામ પસંદ કરો.'}, status=400)

        bill_type = data.get('kind', 'કાચું')
        mode = data.get('mode', 'auto')

        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({'success': False, 'error': 'માલની વિગત જરૂરી છે.'}, status=400)

        base_amt = Decimal(0)
        total_bags = Decimal(0)
        calc_items = []
        for it in items_data:
            bags = Decimal(str(it.get('bags', 0)))
            w = Decimal(str(it.get('weight', 0)))
            rate = Decimal(str(it.get('rate', 0)))
            amt = round((w * rate) / Decimal(20), 2)
            base_amt += amt
            total_bags += bags
            calc_items.append({
                'farmer_name': it.get('farmer_name', ''),
                'item_type': it.get('type', 'તમાકુ') or 'તમાકુ',
                'bags': bags,
                'weight': w,
                'rate': rate,
                'amount': amt,
            })

        comm_rate = Decimal(str(data.get('comm_rate', st.commission_rate)))
        comm = round((base_amt * comm_rate) / Decimal(100), 2)
        market_fee = round(total_bags * Decimal(str(st.market_fee_rate)), 2)
        bardan = round(total_bags * Decimal(str(st.bardan_rate)), 2)
        labor = Decimal(str(data.get('lab', 0)))
        rent = Decimal(str(data.get('rent', 0)))
        gst_rate = Decimal(str(data.get('vat', 0)))

        sub = base_amt + comm + market_fee + bardan + labor + rent
        tax = Decimal(0)
        if bill_type == 'GST':
            tax = round((sub * gst_rate) / Decimal(100), 2)
        total = sub + tax

        tb = TraderBill.objects.create(
            bill_no=bill_no,
            date=date_val,
            firm_name=firm_name,
            trader_name=trader_name,
            bill_type=bill_type,
            mode=mode,
            base_amount=base_amt,
            commission_rate=comm_rate,
            commission_amount=comm,
            market_fee=market_fee,
            bardan_amount=bardan,
            labor=labor,
            rent=rent,
            gst_rate=gst_rate,
            tax_amount=tax,
            total_amount=total,
        )

        for it in calc_items:
            TraderBillItem.objects.create(
                bill=tb,
                farmer_name=it['farmer_name'],
                item_type=it['item_type'],
                trader_name=trader_name,
                bags=it['bags'],
                weight=it['weight'],
                rate=it['rate'],
                amount=it['amount'],
            )

        Trader.objects.get_or_create(name=trader_name)

        return JsonResponse({'success': True, 'bill_id': tb.id, 'bill_no': tb.bill_no})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_delete_trader_bill(request, bill_id):
    bill = get_object_or_404(TraderBill, id=bill_id)
    bill.delete()
    return JsonResponse({'success': True})


# ------------------- API: GST BILL -------------------

@api_login_required
@require_http_methods(["POST"])
def api_save_gst_bill(request):
    try:
        data = json.loads(request.body)
        bill_no = data.get('no') or f"GST-{int(timezone.now().timestamp())}"
        date_val = data.get('date') or timezone.now().date()
        st = get_current_settings()

        firm_name = data.get('firm') or st.firm_name
        firm_address = data.get('firmAddress') or st.firm_address
        firm_gst = data.get('firmGST') or st.firm_gst

        party_name = data.get('party', '').strip()
        if not party_name:
            return JsonResponse({'success': False, 'error': 'વેપારી / ગ્રાહકનું નામ જરૂરી છે.'}, status=400)

        party_address = data.get('partyAddress', '')
        party_gst = data.get('partyGST', '')
        desc = data.get('desc', 'તમાકુ (Tobacco)')

        bags = Decimal(str(data.get('bags', 0)))
        w = Decimal(str(data.get('weight', 0)))
        price = Decimal(str(data.get('price', 0)))
        base_amt = round((w * price) / Decimal(20), 2)

        gst_rate = Decimal(str(data.get('rate', 0)))
        tax_type = data.get('taxType', 'cgst')
        tax = round((base_amt * gst_rate) / Decimal(100), 2)

        cgst = Decimal(0)
        sgst = Decimal(0)
        igst = Decimal(0)
        if tax_type == 'igst':
            igst = tax
        else:
            cgst = round(tax / Decimal(2), 2)
            sgst = tax - cgst

        total = base_amt + tax

        gst_inv = GSTInvoice.objects.create(
            bill_no=bill_no,
            date=date_val,
            firm_name=firm_name,
            firm_address=firm_address,
            firm_gst=firm_gst,
            party_name=party_name,
            party_address=party_address,
            party_gst=party_gst,
            goods_desc=desc,
            bags=bags,
            weight=w,
            price=price,
            base_amount=base_amt,
            gst_rate=gst_rate,
            tax_type=tax_type,
            tax_amount=tax,
            cgst_amount=cgst,
            sgst_amount=sgst,
            igst_amount=igst,
            total_amount=total,
            bank_name=st.bank_name,
            bank_account=st.bank_account,
            sign_name=st.sign_name,
            sign_gst=st.sign_gst,
        )

        return JsonResponse({'success': True, 'bill_id': gst_inv.id, 'bill_no': gst_inv.bill_no})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_delete_gst_bill(request, bill_id):
    bill = get_object_or_404(GSTInvoice, id=bill_id)
    bill.delete()
    return JsonResponse({'success': True})


# ------------------- API: LEDGER & PAYMENTS -------------------

@api_login_required
@require_http_methods(["GET"])
def api_get_ledger_summary(request):
    from_date = request.GET.get('from', '')
    to_date = request.GET.get('to', '')
    filter_type = request.GET.get('type', 'all')

    # Get all farmer summaries
    farmer_names = set(FarmerBill.objects.values_list('farmer_name', flat=True))
    farmer_names.update(PartyPayment.objects.filter(party_type='farmer').values_list('party_name', flat=True))

    farmer_list = []
    if filter_type in ['all', 'farmer']:
        for fn in sorted(farmer_names):
            fb_qs = FarmerBill.objects.filter(farmer_name=fn)
            if from_date:
                fb_qs = fb_qs.filter(date__gte=from_date)
            if to_date:
                fb_qs = fb_qs.filter(date__lte=to_date)
            bill_total = fb_qs.aggregate(s=Sum('total_amount'))['s'] or Decimal(0)
            direct_paid = fb_qs.aggregate(s=Sum('paid_amount'))['s'] or Decimal(0)

            pay_qs = PartyPayment.objects.filter(party_type='farmer', party_name=fn)
            if from_date:
                pay_qs = pay_qs.filter(date__gte=from_date)
            if to_date:
                pay_qs = pay_qs.filter(date__lte=to_date)
            extra_paid = pay_qs.aggregate(s=Sum('amount'))['s'] or Decimal(0)

            total_paid = direct_paid + extra_paid
            due = max(Decimal(0), bill_total - total_paid)
            if bill_total > 0 or total_paid > 0:
                farmer_list.append({
                    'name': fn,
                    'bill_total': float(bill_total),
                    'paid_total': float(total_paid),
                    'due': float(due)
                })

    # Get all trader summaries
    trader_names = set(Trader.objects.values_list('name', flat=True))
    trader_names.update(TraderBill.objects.values_list('trader_name', flat=True))

    trader_list = []
    if filter_type in ['all', 'trader']:
        for tn in sorted(trader_names):
            tb_qs = TraderBill.objects.filter(trader_name=tn)
            if from_date:
                tb_qs = tb_qs.filter(date__gte=from_date)
            if to_date:
                tb_qs = tb_qs.filter(date__lte=to_date)
            bill_total = tb_qs.aggregate(s=Sum('total_amount'))['s'] or Decimal(0)

            pay_qs = PartyPayment.objects.filter(party_type='trader', party_name=tn)
            if from_date:
                pay_qs = pay_qs.filter(date__gte=from_date)
            if to_date:
                pay_qs = pay_qs.filter(date__lte=to_date)
            received = pay_qs.aggregate(s=Sum('amount'))['s'] or Decimal(0)
            due = max(Decimal(0), bill_total - received)

            if bill_total > 0 or received > 0:
                trader_list.append({
                    'name': tn,
                    'bill_total': float(bill_total),
                    'received_total': float(received),
                    'due': float(due)
                })

    # Payments list
    pay_qs = PartyPayment.objects.all().order_by('-date', '-id')
    if from_date:
        pay_qs = pay_qs.filter(date__gte=from_date)
    if to_date:
        pay_qs = pay_qs.filter(date__lte=to_date)
    if filter_type in ['farmer', 'trader']:
        pay_qs = pay_qs.filter(party_type=filter_type)

    payments = []
    for p in pay_qs[:50]:
        payments.append({
            'id': p.id,
            'date': p.date.isoformat(),
            'party_type': p.party_type,
            'party_name': p.party_name,
            'amount': float(p.amount),
            'mode': p.payment_mode,
            'note': p.note,
        })

    return JsonResponse({
        'farmers': farmer_list,
        'traders': trader_list,
        'payments': payments,
    })


@api_login_required
@require_http_methods(["GET"])
def api_get_party_due(request):
    ptype = request.GET.get('type')
    name = request.GET.get('name', '').strip()
    if not name:
        return JsonResponse({'due': 0.0})

    if ptype == 'farmer':
        bill_total = FarmerBill.objects.filter(farmer_name=name).aggregate(s=Sum('total_amount'))['s'] or Decimal(0)
        direct_paid = FarmerBill.objects.filter(farmer_name=name).aggregate(s=Sum('paid_amount'))['s'] or Decimal(0)
        extra_paid = PartyPayment.objects.filter(party_type='farmer', party_name=name).aggregate(s=Sum('amount'))['s'] or Decimal(0)
        due = max(Decimal(0), bill_total - (direct_paid + extra_paid))
        return JsonResponse({'due': float(due)})
    else:
        bill_total = TraderBill.objects.filter(trader_name=name).aggregate(s=Sum('total_amount'))['s'] or Decimal(0)
        received = PartyPayment.objects.filter(party_type='trader', party_name=name).aggregate(s=Sum('amount'))['s'] or Decimal(0)
        due = max(Decimal(0), bill_total - received)
        return JsonResponse({'due': float(due)})


@api_login_required
@require_http_methods(["POST"])
def api_save_payment(request):
    try:
        data = json.loads(request.body)
        party_type = data.get('type')
        name = data.get('name', '').strip()
        amt = Decimal(str(data.get('amount', 0)))
        date_val = data.get('date') or timezone.now().date()
        mode = data.get('mode', 'cash')
        note = data.get('note', '')

        if not name or amt <= 0:
            return JsonResponse({'success': False, 'error': 'નામ અને માન્ય રકમ દાખલ કરો.'}, status=400)

        payment = PartyPayment.objects.create(
            party_type=party_type,
            party_name=name,
            date=date_val,
            amount=amt,
            payment_mode=mode,
            note=note,
        )

        return JsonResponse({'success': True, 'id': payment.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_save_ledger_entry(request):
    try:
        data = json.loads(request.body)
        date_val = data.get('date') or timezone.now().date()
        party = data.get('party', '').strip()
        desc = data.get('desc', '').strip()
        etype = data.get('type', 'jama')
        amt = Decimal(str(data.get('amount', 0)))
        account = data.get('account', 'cash')

        if not amt or amt <= 0:
            return JsonResponse({'success': False, 'error': 'માન્ય રકમ દાખલ કરો.'}, status=400)

        entry = GeneralLedger.objects.create(
            date=date_val,
            party_name=party or 'અન્ય',
            description=desc or ('જમા' if etype == 'jama' else 'ઉધાર'),
            entry_type=etype,
            amount=amt,
            payment_mode=account,
        )

        return JsonResponse({'success': True, 'id': entry.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_delete_ledger_entry(request, entry_id):
    entry = get_object_or_404(GeneralLedger, id=entry_id)
    entry.delete()
    return JsonResponse({'success': True})


# ------------------- API: DAILY HISAB -------------------

@api_login_required
@require_http_methods(["GET"])
def api_get_daily_summary(request):
    date_val = request.GET.get('date') or timezone.now().date().isoformat()

    # Day's General Ledger
    day_gl = GeneralLedger.objects.filter(date=date_val)
    gl_jama = day_gl.filter(entry_type='jama').aggregate(s=Sum('amount'))['s'] or Decimal(0)
    gl_udhar = day_gl.filter(entry_type='udhar').aggregate(s=Sum('amount'))['s'] or Decimal(0)

    # Day's Trader Payments (Received Income)
    trader_pays = PartyPayment.objects.filter(party_type='trader', date=date_val)
    trader_inc = trader_pays.aggregate(s=Sum('amount'))['s'] or Decimal(0)

    # Day's Farmer Payments (Given Payouts)
    farmer_pays = PartyPayment.objects.filter(party_type='farmer', date=date_val)
    farmer_out = farmer_pays.aggregate(s=Sum('amount'))['s'] or Decimal(0)

    # Day's Farmer Bills directly paid
    farmer_bills_paid = FarmerBill.objects.filter(date=date_val, payment_status='paid').aggregate(s=Sum('paid_amount'))['s'] or Decimal(0)

    # Day's Expenses
    day_exp = Expense.objects.filter(date=date_val)
    exp_total = day_exp.aggregate(s=Sum('amount'))['s'] or Decimal(0)

    total_income = gl_jama + trader_inc
    total_payout = gl_udhar + farmer_out + farmer_bills_paid
    net_change = total_income - total_payout - exp_total

    # List items
    transactions = []
    for g in day_gl:
        transactions.append({
            'label': f"{g.party_name} - {g.description}",
            'kind': 'જમા' if g.entry_type == 'jama' else 'ઉધાર',
            'amount': float(g.amount),
            'mode': g.payment_mode,
        })
    for tp in trader_pays:
        transactions.append({
            'label': f"વેપારી પાસેથી આવેલ: {tp.party_name}",
            'kind': 'જમા',
            'amount': float(tp.amount),
            'mode': tp.payment_mode,
        })
    for fp in farmer_pays:
        transactions.append({
            'label': f"ખેડૂતને ચુકવણી: {fp.party_name}",
            'kind': 'ઉધાર',
            'amount': float(fp.amount),
            'mode': fp.payment_mode,
        })
    for fb in FarmerBill.objects.filter(date=date_val, paid_amount__gt=0):
        transactions.append({
            'label': f"ખેડૂત બિલ #{fb.bill_no} ચૂકવણી: {fb.farmer_name}",
            'kind': 'ઉધાર',
            'amount': float(fb.paid_amount),
            'mode': fb.payment_mode,
        })
    for e in day_exp:
        transactions.append({
            'label': f"ખર્ચ: {e.title} ({e.description})",
            'kind': 'ખર્ચ',
            'amount': float(e.amount),
            'mode': e.payment_mode,
        })

    balances = calculate_balances()

    return JsonResponse({
        'date': str(date_val),
        'income': float(total_income),
        'payout': float(total_payout),
        'expense': float(exp_total),
        'net_change': float(net_change),
        'cash_balance': float(balances['cash_balance']),
        'bank_balance': float(balances['bank_balance']),
        'transactions': transactions,
    })


# ------------------- API: EXPENSES -------------------

@api_login_required
@require_http_methods(["POST"])
def api_save_expense(request):
    try:
        data = json.loads(request.body)
        date_val = data.get('date') or timezone.now().date()
        title = data.get('name', '').strip()
        desc = data.get('desc', '').strip()
        amt = Decimal(str(data.get('amount', 0)))
        account = data.get('account', 'cash')

        if not title or amt <= 0:
            return JsonResponse({'success': False, 'error': 'ખર્ચનું નામ અને રકમ આપો.'}, status=400)

        exp = Expense.objects.create(
            date=date_val,
            title=title,
            description=desc,
            amount=amt,
            payment_mode=account,
        )

        return JsonResponse({'success': True, 'id': exp.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_delete_expense(request, expense_id):
    exp = get_object_or_404(Expense, id=expense_id)
    exp.delete()
    return JsonResponse({'success': True})


# ------------------- API: SETTINGS & TRADERS -------------------

@api_login_required
@require_http_methods(["POST"])
def api_save_settings(request):
    try:
        data = json.loads(request.body)
        st = get_current_settings()
        st.firm_name = data.get('firm', st.firm_name)
        st.bardan_rate = Decimal(str(data.get('bard', st.bardan_rate)))
        st.market_fee_rate = Decimal(str(data.get('market', st.market_fee_rate)))
        st.commission_rate = Decimal(str(data.get('comm', st.commission_rate)))
        st.initial_cash = Decimal(str(data.get('cash', st.initial_cash)))
        st.initial_bank = Decimal(str(data.get('bank', st.initial_bank)))
        st.firm_address = data.get('firmAddress', st.firm_address)
        st.firm_gst = data.get('firmGST', st.firm_gst)
        st.bank_name = data.get('bankName', st.bank_name)
        st.bank_account = data.get('bankAccount', st.bank_account)
        st.sign_name = data.get('signName', st.sign_name)
        st.sign_gst = data.get('signGST', st.sign_gst)
        st.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_add_trader(request):
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'વેપારીનું નામ જરૂરી છે.'}, status=400)

        trader, created = Trader.objects.get_or_create(
            name=name,
            defaults={
                'mobile': data.get('mobile', ''),
                'village': data.get('village', ''),
                'gst_no': data.get('gst_no', ''),
            }
        )
        return JsonResponse({'success': True, 'id': trader.id, 'name': trader.name, 'created': created})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["POST"])
def api_delete_trader(request, trader_id):
    trader = get_object_or_404(Trader, id=trader_id)
    trader.delete()
    return JsonResponse({'success': True})


# ------------------- PRINT VIEWS -------------------

@login_required
def print_farmer_bill(request, bill_id):
    bill = get_object_or_404(FarmerBill, id=bill_id)
    st = get_current_settings()
    return render(request, 'billing/print_farmer_bill.html', {'bill': bill, 'st': st})


@login_required
def print_trader_bill(request, bill_id):
    bill = get_object_or_404(TraderBill, id=bill_id)
    st = get_current_settings()
    return render(request, 'billing/print_trader_bill.html', {'bill': bill, 'st': st})


@login_required
def print_gst_bill(request, bill_id):
    bill = get_object_or_404(GSTInvoice, id=bill_id)
    st = get_current_settings()
    return render(request, 'billing/print_gst_bill.html', {'bill': bill, 'st': st})
