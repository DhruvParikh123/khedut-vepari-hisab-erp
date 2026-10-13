from django.db import models
from django.utils import timezone


class FirmSetting(models.Model):
    firm_name = models.CharField(max_length=200, default="શ્રી ખેડૂત એન્ટરપ્રાઇઝ", verbose_name="પેઢીનું નામ")
    firm_address = models.TextField(blank=True, default="", verbose_name="પેઢીનું સરનામું")
    firm_gst = models.CharField(max_length=30, blank=True, default="", verbose_name="પેઢીનો GST નંબર")
    bardan_rate = models.DecimalField(max_digits=10, decimal_places=2, default=15.00, verbose_name="બારદાન દર (દર બેગ ₹)")
    market_fee_rate = models.DecimalField(max_digits=10, decimal_places=2, default=3.00, verbose_name="માર્કેટ ફી દર (દર બેગ ₹)")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.50, verbose_name="કમિશન દર (%)")
    initial_cash = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="પ્રારંભિક રોકડ બેલેન્સ ₹")
    initial_bank = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="પ્રારંભિક બેંક બેલેન્સ ₹")
    bank_name = models.CharField(max_length=150, blank=True, default="", verbose_name="બેંકનું નામ")
    bank_account = models.CharField(max_length=60, blank=True, default="", verbose_name="બેંક ખાતા નંબર")
    sign_name = models.CharField(max_length=150, blank=True, default="", verbose_name="સહી કરનારનું નામ")
    sign_gst = models.CharField(max_length=30, blank=True, default="", verbose_name="સહી કરનારનો GST નંબર")

    class Meta:
        verbose_name = "પેઢી સેટિંગ"
        verbose_name_plural = "પેઢી સેટિંગ્સ"

    def __str__(self):
        return self.firm_name or "પેઢી સેટિંગ"

    @classmethod
    def get_settings(cls):
        setting, _ = cls.objects.get_or_create(id=1)
        return setting


class Trader(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="વેપારીનું નામ")
    mobile = models.CharField(max_length=20, blank=True, default="", verbose_name="મોબાઇલ")
    village = models.CharField(max_length=100, blank=True, default="", verbose_name="ગામ/શહેર")
    gst_no = models.CharField(max_length=30, blank=True, default="", verbose_name="GST નંબર")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="બનાવ્યા તારીખ")

    class Meta:
        ordering = ['name']
        verbose_name = "વેપારી"
        verbose_name_plural = "વેપારીઓ"

    def __str__(self):
        return self.name


class FarmerBill(models.Model):
    BILL_TYPES = [
        ('કાચું', 'કાચું બિલ'),
        ('GST', 'GST બિલ'),
    ]
    PAY_STATUS = [
        ('due', 'બાકી'),
        ('paid', 'ચૂકવેલ'),
    ]

    bill_no = models.CharField(max_length=50, unique=True, verbose_name="બિલ નંબર")
    date = models.DateField(default=timezone.now, verbose_name="તારીખ")
    firm_name = models.CharField(max_length=200, blank=True, default="", verbose_name="પેઢીનું નામ")
    farmer_name = models.CharField(max_length=150, verbose_name="ખેડૂતનું નામ")
    mobile = models.CharField(max_length=20, blank=True, default="", verbose_name="મોબાઇલ")
    village = models.CharField(max_length=100, blank=True, default="", verbose_name="ગામ")
    plot_no = models.CharField(max_length=50, blank=True, default="", verbose_name="પ્લોટ નંબર")
    bill_type = models.CharField(max_length=10, choices=BILL_TYPES, default='કાચું', verbose_name="બિલ પ્રકાર")

    base_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="માલ કુલ ₹")
    bardan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="બારદાન ₹")
    labor = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="મજૂરી ₹")
    deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="કપાત ₹")
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="GST %")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="GST ₹")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="કુલ રકમ ₹")

    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="ચૂકવેલ રકમ ₹")
    payment_status = models.CharField(max_length=10, choices=PAY_STATUS, default='due', verbose_name="ચૂકવણી સ્થિતિ")
    payment_mode = models.CharField(max_length=10, choices=[('cash', 'રોકડ'), ('bank', 'બેંક')], default='cash', verbose_name="ચુકવણી માધ્યમ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "ખેડૂત બિલ"
        verbose_name_plural = "ખેડૂત બિલો"

    def __str__(self):
        return f"{self.bill_no} - {self.farmer_name} (₹{self.total_amount})"

    @property
    def due_amount(self):
        return max(0, float(self.total_amount) - float(self.paid_amount))

    @property
    def total_bags(self):
        return sum(item.bags for item in self.items.all())

    @property
    def total_weight(self):
        return sum(item.weight for item in self.items.all())


class FarmerBillItem(models.Model):
    bill = models.ForeignKey(FarmerBill, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=100, default="તમાકુ", verbose_name="માલની જાત")
    trader_name = models.CharField(max_length=150, blank=True, default="", verbose_name="વેપારી")
    bags = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="બેગ / બોરી")
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="વજન (કિ.ગ્રા.)")
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ભાવ પ્રતિ મણ (20 કિ.ગ્રા.)")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="રકમ ₹")

    def save(self, *args, **kwargs):
        # Calculation: (weight * rate) / 20
        self.amount = round((self.weight * self.rate) / 20, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_type} - {self.weight}kg @ ₹{self.rate}/20kg = ₹{self.amount}"


class TraderBill(models.Model):
    BILL_TYPES = [
        ('કાચું', 'કાચું બિલ'),
        ('GST', 'GST બિલ'),
    ]
    MODES = [
        ('auto', 'ખેડૂત બિલ પરથી ઓટોમેટિક'),
        ('manual', 'મેન્યુઅલ'),
    ]

    bill_no = models.CharField(max_length=50, unique=True, verbose_name="બિલ નંબર")
    date = models.DateField(default=timezone.now, verbose_name="તારીખ")
    firm_name = models.CharField(max_length=200, blank=True, default="", verbose_name="પેઢીનું નામ")
    trader_name = models.CharField(max_length=150, verbose_name="વેપારીનું નામ")
    bill_type = models.CharField(max_length=10, choices=BILL_TYPES, default='કાચું', verbose_name="બિલ પ્રકાર")
    mode = models.CharField(max_length=10, choices=MODES, default='auto', verbose_name="બનાવવાની રીત")

    base_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="માલ કુલ ₹")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.50, verbose_name="કમિશન %")
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="કમિશન ₹")
    market_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="માર્કેટ ફી ₹")
    bardan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="બારદાન ₹")
    labor = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="મજૂરી ₹")
    rent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="ભાડું ₹")
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="GST %")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="GST ₹")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="કુલ બિલ ₹")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "વેપારી બિલ"
        verbose_name_plural = "વેપારી બિલો"

    def __str__(self):
        return f"{self.bill_no} - {self.trader_name} (₹{self.total_amount})"

    @property
    def total_bags(self):
        return sum(item.bags for item in self.items.all())

    @property
    def total_weight(self):
        return sum(item.weight for item in self.items.all())


class TraderBillItem(models.Model):
    bill = models.ForeignKey(TraderBill, on_delete=models.CASCADE, related_name='items')
    farmer_bill = models.ForeignKey(FarmerBill, null=True, blank=True, on_delete=models.SET_NULL, related_name='trader_bill_items')
    farmer_name = models.CharField(max_length=150, blank=True, default="", verbose_name="ખેડૂતનું નામ")
    item_type = models.CharField(max_length=100, default="તમાકુ", verbose_name="માલની જાત")
    trader_name = models.CharField(max_length=150, blank=True, default="", verbose_name="વેપારી")
    bags = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="બેગ")
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="વજન (કિ.ગ્રા.)")
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ભાવ પ્રતિ મણ (20 કિ.ગ્રા.)")
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="રકમ ₹")

    def save(self, *args, **kwargs):
        self.amount = round((self.weight * self.rate) / 20, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_type} - {self.weight}kg @ ₹{self.rate} = ₹{self.amount}"


class GSTInvoice(models.Model):
    TAX_TYPES = [
        ('cgst', 'CGST + SGST'),
        ('igst', 'IGST'),
    ]

    bill_no = models.CharField(max_length=50, unique=True, verbose_name="GST બિલ નંબર")
    date = models.DateField(default=timezone.now, verbose_name="તારીખ")
    firm_name = models.CharField(max_length=200, verbose_name="પેઢીનું નામ")
    firm_address = models.TextField(blank=True, default="", verbose_name="પેઢીનું સરનામું")
    firm_gst = models.CharField(max_length=30, blank=True, default="", verbose_name="પેઢીનો GSTIN")

    party_name = models.CharField(max_length=150, verbose_name="વેપારી / ગ્રાહકનું નામ")
    party_address = models.TextField(blank=True, default="", verbose_name="સરનામું")
    party_gst = models.CharField(max_length=30, blank=True, default="", verbose_name="ગ્રાહકનો GSTIN")

    goods_desc = models.CharField(max_length=150, default="તમાકુ (Tobacco)", verbose_name="માલનો પ્રકાર")
    bags = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="બેગ")
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="વજન (કિ.ગ્રા.)")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ભાવ પ્રતિ મણ ₹")
    base_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="કુલ માલ રકમ ₹")

    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="GST દર %")
    tax_type = models.CharField(max_length=10, choices=TAX_TYPES, default='cgst', verbose_name="GST પ્રકાર")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="કુલ GST ₹")
    cgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="CGST ₹")
    sgst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="SGST ₹")
    igst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IGST ₹")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="કુલ રકમ ₹")

    bank_name = models.CharField(max_length=150, blank=True, default="", verbose_name="બેંકનું નામ")
    bank_account = models.CharField(max_length=60, blank=True, default="", verbose_name="બેંક ખાતા નંબર")
    sign_name = models.CharField(max_length=150, blank=True, default="", verbose_name="સહી કરનારનું નામ")
    sign_gst = models.CharField(max_length=30, blank=True, default="", verbose_name="સહી કરનાર GSTIN")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "GST ઇન્વોઇસ"
        verbose_name_plural = "GST ઇન્વોઇસ"

    def __str__(self):
        return f"{self.bill_no} - {self.party_name} (₹{self.total_amount})"


class PartyPayment(models.Model):
    PARTY_TYPES = [
        ('farmer', 'ખેડૂત'),
        ('trader', 'વેપારી'),
    ]
    MODES = [
        ('cash', 'રોકડ'),
        ('bank', 'બેંક'),
    ]

    party_type = models.CharField(max_length=10, choices=PARTY_TYPES, verbose_name="પાર્ટી પ્રકાર")
    party_name = models.CharField(max_length=150, verbose_name="પાર્ટીનું નામ")
    date = models.DateField(default=timezone.now, verbose_name="તારીખ")
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="રકમ ₹")
    payment_mode = models.CharField(max_length=10, choices=MODES, default='cash', verbose_name="ચુકવણી માધ્યમ")
    note = models.CharField(max_length=255, blank=True, default="", verbose_name="નોંધ/વિગત")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "પાર્ટી ચુકવણી / જમા"
        verbose_name_plural = "પાર્ટી ચુકવણી / જમા"

    def __str__(self):
        direction = "ચૂકવ્યા" if self.party_type == 'farmer' else "આવ્યા"
        return f"{self.date} - {self.party_name} ({self.get_party_type_display()}) {direction} ₹{self.amount}"


class GeneralLedger(models.Model):
    TYPES = [
        ('jama', 'જમા (આવક)'),
        ('udhar', 'ઉધાર (ચૂકવણી)'),
    ]
    MODES = [
        ('cash', 'રોકડ'),
        ('bank', 'બેંક'),
    ]

    date = models.DateField(default=timezone.now, verbose_name="તારીખ")
    party_name = models.CharField(max_length=150, verbose_name="પાર્ટી / ખાતાનું નામ")
    description = models.CharField(max_length=255, verbose_name="વિગત")
    entry_type = models.CharField(max_length=10, choices=TYPES, verbose_name="પ્રકાર")
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="રકમ ₹")
    payment_mode = models.CharField(max_length=10, choices=MODES, default='cash', verbose_name="માધ્યમ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "સામાન્ય ખાતાવહી નોંધ"
        verbose_name_plural = "સામાન્ય ખાતાવહી નોંધો"

    def __str__(self):
        return f"{self.date} - {self.party_name} ({self.get_entry_type_display()}) ₹{self.amount}"


class Expense(models.Model):
    MODES = [
        ('cash', 'રોકડ'),
        ('bank', 'બેંક'),
    ]

    date = models.DateField(default=timezone.now, verbose_name="તારીખ")
    title = models.CharField(max_length=150, verbose_name="ખર્ચનું નામ")
    description = models.CharField(max_length=255, blank=True, default="", verbose_name="વિગત")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="રકમ ₹")
    payment_mode = models.CharField(max_length=10, choices=MODES, default='cash', verbose_name="ચૂકવણી માધ્યમ")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "ખર્ચ"
        verbose_name_plural = "ખર્ચાઓ"

    def __str__(self):
        return f"{self.date} - {self.title} ₹{self.amount}"
