from django.core.management.base import BaseCommand
from billing.models import FirmSetting, Trader

class Command(BaseCommand):
    help = 'Seed initial master data and settings'

    def handle(self, *args, **kwargs):
        st, created = FirmSetting.objects.get_or_create(id=1, defaults={
            'firm_name': 'શ્રી ઉમિયા તમાકુ ટ્રેડિંગ કંપની',
            'firm_address': 'વિજાપુર-હિંમતનગર હાઈવે, ગોવિંદપુરા રોડ, વિજાપુર - ૩૮૨૮૭૦',
            'firm_gst': '24AAACU1234F1Z5',
            'bardan_rate': 15.00,
            'market_fee_rate': 3.00,
            'commission_rate': 1.50,
            'initial_cash': 25000.00,
            'initial_bank': 150000.00,
            'bank_name': 'સ્ટેટ બેંક ઓફ ઇન્ડિયા (SBI)',
            'bank_account': '30291827364',
            'sign_name': 'પટેલ રમેશભાઈ કે.',
            'sign_gst': '24AAACU1234F1Z5'
        })
        if created:
            self.stdout.write(self.style.SUCCESS('Created initial firm settings.'))

        default_traders = [
            'જય અંબે ટ્રેડર્સ',
            'પટેલ ટોબેકો કંપની',
            'શ્રી રામ એગ્રો એન્ટરપ્રાઇઝ',
            'ખોડલ એન્ટરપ્રાઇઝ',
            'ગણેશ ટ્રેડિંગ',
            'વિષ્ણુ બ્રધર્સ'
        ]
        for name in default_traders:
            t, was_created = Trader.objects.get_or_create(name=name)
            if was_created:
                self.stdout.write(f'Added trader: id={t.id}')

        self.stdout.write('Master data seeding complete.')
