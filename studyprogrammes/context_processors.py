# context_processors.py for studyprogrammes
from django.conf import settings

def studyprogrammes_base_url(request):
    return {
        'STUDYPROGRAMMES_BASE_URL': getattr(settings, 'STUDYPROGRAMMES_BASE_URL', '/programme-designer/')
    }
