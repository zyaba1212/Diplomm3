from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import SiteSettings

def global_settings(request):
    """Add global settings to template context"""
    try:
        site_settings = SiteSettings.objects.filter(key='global_settings').first()
        if site_settings:
            settings_data = site_settings.value
        else:
            settings_data = {}
    except:
        settings_data = {}
    
    return {
        'SITE_NAME': settings_data.get('site_name', settings.SITE_NAME),
        'SITE_DESCRIPTION': settings_data.get('site_description', settings.SITE_DESCRIPTION),
        'SOLANA_RPC_URL': settings.SOLANA_RPC_URL,
        'SOLANA_WEB3_JS': settings.SOLANA_WEB3_JS,
        'SOLANA_WALLET_ADAPTER': settings.SOLANA_WALLET_ADAPTER,
        'LANGUAGES': settings.LANGUAGES,
        'LANGUAGE_CODE': request.LANGUAGE_CODE,
        'available_languages': [
            {'code': code, 'name': name, 'active': code == request.LANGUAGE_CODE}
            for code, name in settings.LANGUAGES
        ],
    }