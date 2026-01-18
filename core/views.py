from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from .models import *
import json

def index(request):
    """Главная страница"""
    context = {
        'title': _('Z96A - Архитектура сети будущего'),
        'description': _('Инновационная система обработки транзакций'),
    }
    return render(request, 'index.html', context)

def architecture_view(request):
    """Страница с 3D визуализацией"""
    context = {
        'title': _('Архитектура сети'),
    }
    return render(request, 'architecture.html', context)

def news_view(request):
    """Страница новостей"""
    articles = NewsArticle.objects.filter(is_active=True).order_by('-published_date')[:50]
    context = {
        'title': _('Последние новости'),
        'articles': articles,
    }
    return render(request, 'news.html', context)

def discussion_view(request):
    """Страница обсуждения"""
    context = {
        'title': _('Обсуждение'),
    }
    return render(request, 'discussion.html', context)

def about_view(request):
    """Страница О проекте"""
    context = {
        'title': _('О проекте'),
        'student_name': 'Зыблиенко Дмитрий',
        'academy': 'Белорусская Государственная Академия Связи',
        'project_name': 'Архитектура системы обработки транзакций',
    }
    return render(request, 'about.html', context)

def roadmap_view(request):
    """Roadmap"""
    context = {
        'title': _('Дорожная карта'),
    }
    return render(request, 'roadmap.html', context)

# ==================== API ENDPOINTS ====================

@csrf_exempt
def api_connect_wallet(request):
    """API подключения кошелька"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('wallet_address')
            
            import random
            adjectives = ['Digital', 'Cosmic', 'Quantum', 'Neural', 'Cyber', 'Orbital', 'Stellar']
            nouns = ['Explorer', 'Pioneer', 'Voyager', 'Navigator', 'Architect', 'Engineer']
            nickname = f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(1000,9999)}"
            
            while UserProfile.objects.filter(nickname=nickname).exists():
                nickname = f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(1000,9999)}"
            
            profile, created = UserProfile.objects.get_or_create(
                wallet_address=wallet_address,
                defaults={'nickname': nickname}
            )
            
            BlockchainTransaction.objects.create(
                user=profile,
                transaction_type='wallet_connect',
                solana_tx_hash=f"demo_tx_{wallet_address[:10]}",
                data={'wallet': wallet_address},
                verified=True
            )
            
            return JsonResponse({
                'success': True,
                'nickname': profile.nickname,
                'wallet_address': profile.wallet_address,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
def api_get_network_data(request):
    """API данных сети"""
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
                'image_url': elem.image_url or '',
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
def api_get_cables(request):
    """API кабелей"""
    cables = Cable.objects.filter(is_active=True)
    
    data = {
        'cables': [
            {
                'id': cable.cable_id,
                'name': cable.name,
                'type': cable.cable_type,
                'capacity': cable.capacity,
                'length': cable.length,
                'owners': cable.owners,
                'year': cable.year,
                'color': cable.color,
                'description': cable.description,
                'route': [
                    {
                        'lat': point.latitude,
                        'lng': point.longitude,
                        'name': point.location_name,
                        'order': point.order
                    }
                    for point in cable.route.all().order_by('order')
                ]
            }
            for cable in cables
        ]
    }
    return JsonResponse(data)

@csrf_exempt
def api_get_hierarchy(request):
    """API иерархии (регионы, страны, города)"""
    regions = Region.objects.all()
    
    data = {
        'regions': [
            {
                'id': region.id,
                'name': region.name,
                'code': region.code,
                'countries': [
                    {
                        'id': country.id,
                        'name': country.name,
                        'code': country.code,
                        'capital': country.capital,
                        'cities': [
                            {
                                'id': city.id,
                                'name': city.name,
                                'type': city.city_type,
                                'lat': city.latitude,
                                'lng': city.longitude,
                                'is_hub': city.is_hub,
                                'population': city.population,
                            }
                            for city in country.cities.all()
                        ]
                    }
                    for country in region.countries.all()
                ]
            }
            for region in regions
        ]
    }
    return JsonResponse(data)

@csrf_exempt
def api_get_comments(request):
    """API комментариев"""
    comments = Comment.objects.filter(parent__isnull=True).order_by('-created_at')
    
    def serialize_comment(comment):
        return {
            'id': comment.id,
            'user': {
                'nickname': comment.user.nickname,
                'wallet': comment.user.wallet_address[:10] + '...'
            },
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'replies': [serialize_comment(reply) for reply in comment.replies.all()]
        }
    
    data = {
        'comments': [serialize_comment(c) for c in comments]
    }
    return JsonResponse(data)

@csrf_exempt
def api_post_comment(request):
    """API отправки комментария"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('wallet_address')
            content = data.get('content')
            parent_id = data.get('parent_id')
            
            profile = UserProfile.objects.get(wallet_address=wallet_address)
            
            parent = None
            if parent_id:
                parent = Comment.objects.get(id=parent_id)
            
            comment = Comment.objects.create(
                user=profile,
                content=content,
                parent=parent
            )
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
def api_like_comment(request, comment_id):
    """Лайк комментария"""
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.likes += 1
            comment.save()
            return JsonResponse({'success': True, 'likes': comment.likes})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
def api_dislike_comment(request, comment_id):
    """Дизлайк комментария"""
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.dislikes += 1
            comment.save()
            return JsonResponse({'success': True, 'dislikes': comment.dislikes})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)

@csrf_exempt
def api_submit_proposal(request):
    """API предложений"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('wallet_address')
            proposal_data = data.get('proposal')
            
            profile = UserProfile.objects.get(wallet_address=wallet_address)
            
            proposal = Proposal.objects.create(
                user=profile,
                proposal_type=proposal_data.get('type', 'equipment'),
                description=proposal_data.get('description', ''),
                specifications=proposal_data.get('specifications', {}),
                status='pending'
            )
            
            return JsonResponse({
                'success': True,
                'proposal_id': proposal.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)

def api_get_news(request):
    """API новостей"""
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