from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .models import *
import json
from .blockchain import verify_solana_transaction, create_wallet_connection_tx
from .parser import fetch_news_articles

def index(request):
    """Главная страница"""
    context = {
        'title': _('Z96A - Архитектура сети будущего'),
        'description': _('Инновационная система обработки транзакций для инфокоммуникационных систем'),
    }
    return render(request, 'index.html', context)

def architecture_view(request):
    """Страница с 3D визуализацией архитектуры сети"""
    elements = NetworkElement.objects.filter(is_active=True)
    connections = NetworkConnection.objects.all()
    
    context = {
        'title': _('Архитектура сети'),
        'elements': elements,
        'connections': connections,
    }
    return render(request, 'architecture.html', context)

def news_view(request):
    """Страница с новостями"""
    articles = NewsArticle.objects.filter(is_active=True).order_by('-published_date')[:50]
    
    context = {
        'title': _('Последние новости'),
        'articles': articles,
    }
    return render(request, 'news.html', context)

def discussion_view(request):
    """Страница обсуждения"""
    comments = Comment.objects.filter(parent__isnull=True).order_by('-created_at')
    
    context = {
        'title': _('Обсуждение'),
        'comments': comments,
    }
    return render(request, 'discussion.html', context)

def about_view(request):
    """Страница "О нас" """
    context = {
        'title': _('О проекте'),
        'student_name': 'Зыблиенко Дмитрий',
        'academy': 'Белорусская Государственная Академия Связи',
        'project_name': 'Архитектура системы обработки транзакций для инфокоммуникационных систем в условиях частичного отсутствия сетевого соединения',
    }
    return render(request, 'about.html', context)

def roadmap_view(request):
    """Страница с roadmap"""
    context = {
        'title': _('Дорожная карта'),
    }
    return render(request, 'roadmap.html', context)

@csrf_exempt
def api_connect_wallet(request):
    """API для подключения кошелька"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('wallet_address')
            signature = data.get('signature')
            
            # В реальном проекте здесь будет верификация подписи
            # Для демо просто создаем/обновляем пользователя
            
            # Генерируем случайный никнейм
            import random
            adjectives = ['Digital', 'Cosmic', 'Quantum', 'Neural', 'Cyber', 'Orbital', 'Stellar']
            nouns = ['Explorer', 'Pioneer', 'Voyager', 'Navigator', 'Architect', 'Engineer']
            nickname = f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(1000,9999)}"
            
            # Проверяем уникальность
            while UserProfile.objects.filter(nickname=nickname).exists():
                nickname = f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(1000,9999)}"
            
            # Создаем или обновляем профиль
            profile, created = UserProfile.objects.get_or_create(
                wallet_address=wallet_address,
                defaults={'nickname': nickname}
            )
            
            # Создаем запись транзакции
            transaction = BlockchainTransaction.objects.create(
                user=profile,
                transaction_type='wallet_connect',
                solana_tx_hash=f"demo_tx_{wallet_address[:10]}",
                data={'signature': signature, 'wallet': wallet_address},
                verified=True  # Для демо
            )
            
            return JsonResponse({
                'success': True,
                'nickname': profile.nickname,
                'wallet_address': profile.wallet_address,
                'message': _('Кошелек успешно подключен')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
def api_get_network_data(request):
    """API для получения данных сети для 3D визуализации"""
    elements = NetworkElement.objects.filter(is_active=True)
    connections = NetworkConnection.objects.all()
    
    data = {
        'elements': [
            {
                'id': str(elem.element_id),
                'name': elem.name,
                'type': elem.element_type,
                'network': elem.network_type,
                'lat': elem.latitude,
                'lng': elem.longitude,
                'alt': elem.altitude,
                'description': elem.description,
                'image_url': elem.image_url if elem.image_url else '',
                'proposed_by': elem.proposed_by.nickname if elem.proposed_by else None,
                'specifications': elem.specifications,
            }
            for elem in elements
        ],
        'connections': [
            {
                'from': str(conn.from_element.element_id),
                'to': str(conn.to_element.element_id),
                'type': conn.connection_type,
                'bandwidth': conn.bandwidth,
                'latency': conn.latency,
            }
            for conn in connections
        ]
    }
    
    return JsonResponse(data)

@csrf_exempt
def api_submit_proposal(request):
    """API для отправки предложений"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('wallet_address')
            proposal_data = data.get('proposal')
            
            # Находим пользователя
            try:
                profile = UserProfile.objects.get(wallet_address=wallet_address)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': _('Пользователь не найден')}, status=404)
            
            # Создаем предложение
            proposal = Proposal.objects.create(
                user=profile,
                proposal_type=proposal_data.get('type', 'equipment'),
                description=proposal_data.get('description', ''),
                specifications=proposal_data.get('specifications', {}),
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'proposal_id': proposal.id,
                'message': _('Предложение успешно отправлено')
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'error': 'Invalid method'}, status=400)

def api_get_news(request):
    """API для получения новостей"""
    articles = NewsArticle.objects.filter(is_active=True).order_by('-published_date')[:20]
    
    data = {
        'articles': [
            {
                'id': article.id,
                'title': article.title,
                'content_preview': article.content[:200] + '...' if len(article.content) > 200 else article.content,
                'source': article.source,
                'url': article.url,
                'published_date': article.published_date.strftime('%Y-%m-%d %H:%M'),
            }
            for article in articles
        ]
    }
    
    return JsonResponse(data)

@login_required
def admin_custom_view(request):
    """Кастомная админ-панель"""
    if not request.user.is_superuser:
        return redirect('admin:login')
    
    pending_proposals = Proposal.objects.filter(status='pending').count()
    total_users = UserProfile.objects.count()
    total_elements = NetworkElement.objects.count()
    
    context = {
        'pending_proposals': pending_proposals,
        'total_users': total_users,
        'total_elements': total_elements,
        'title': _('Панель администратора Z96A'),
    }
    
    return render(request, 'admin/custom_admin.html', context)