from .models import FirmSetting
from django.utils import timezone

def global_settings(request):
    try:
        setting = FirmSetting.get_settings()
    except Exception:
        setting = None
    return {
        'firm_setting': setting,
        'today_date': timezone.now().date(),
    }
