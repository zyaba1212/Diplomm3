"""
Контекстные процессоры для передачи глобальных переменных в шаблоны
"""

from django.conf import settings
from .models import NewsArticle


def global_context(request):
    """Глобальные переменные для всех шаблонов"""
    context = {
        'SITE_NAME': 'Z96A',
        'SITE_DESCRIPTION': 'Архитектура гибридных сетей связи с блокчейн-интеграцией',
        'SITE_URL': 'https://z96a.com',
        'CURRENT_YEAR': 2026,
        'DEBUG': settings.DEBUG,
    }
    
    # Добавляем последние новости для боковой панели
    if not request.path.startswith('/admin/'):
        try:
            latest_news = NewsArticle.objects.all().order_by('-published_date')[:5]
            context['latest_news'] = latest_news
        except Exception:
            context['latest_news'] = []
    
    return context


def language_context(request):
    """Контекст для переключения языков"""
    return {
        'CURRENT_LANGUAGE': 'ru',
        'AVAILABLE_LANGUAGES': [
            ('ru', 'Русский'),
            ('en', 'English'),
        ],
    }


def user_context(request):
    """Контекст пользователя (если авторизован через кошелек)"""
    context = {}
    
    # В реальном проекте здесь будет логика получения профиля из сессии/куки
    # Для демо используем заглушку
    wallet_address = request.session.get('wallet_address', None)
    if wallet_address:
        context['wallet_connected'] = True
        context['wallet_address'] = wallet_address
        # Здесь можно добавить nickname, reputation и т.д.
    else:
        context['wallet_connected'] = False
    
    return context