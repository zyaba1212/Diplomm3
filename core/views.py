from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
import json
from .models import NetworkNode, Equipment, UserProposal, Comment, NewsArticle, NetworkConnection
from .services.news_parser import NewsParser
from .services.solana_client import SolanaClient

def home(request):
    """Home page view"""
    # Get featured news
    featured_news = NewsArticle.objects.filter(is_featured=True).order_by('-published_date')[:5]
    
    # Get recent proposals
    recent_proposals = UserProposal.objects.filter(status='approved').order_by('-created_at')[:5]
    
    # Get statistics
    stats = {
        'total_nodes': NetworkNode.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'total_connections': NetworkConnection.objects.count(),
        'total_proposals': UserProposal.objects.count(),
    }
    
    context = {
        'featured_news': featured_news,
        'recent_proposals': recent_proposals,
        'stats': stats,
        'page_title': _('Home - Z96A Network Architecture'),
    }
    return render(request, 'core/home.html', context)

def network_architecture(request):
    """Network architecture visualization page"""
    # Get all nodes for the map
    nodes = NetworkNode.objects.all()
    connections = NetworkConnection.objects.filter(is_active=True)
    
    # Convert to GeoJSON format for the map
    nodes_data = []
    for node in nodes:
        nodes_data.append({
            'id': str(node.id),
            'name': node.name,
            'type': node.node_type,
            'network_type': node.network_type,
            'coordinates': [node.longitude, node.latitude, node.altitude],
            'country': node.country,
            'city': node.city,
            'description': node.description,
        })
    
    connections_data = []
    for conn in connections:
        connections_data.append({
            'id': str(conn.id),
            'name': conn.name,
            'type': conn.connection_type,
            'from': str(conn.from_node_id),
            'to': str(conn.to_node_id),
            'path': conn.geojson_path,
            'capacity': conn.capacity_gbps,
        })
    
    context = {
        'nodes': json.dumps(nodes_data),
        'connections': json.dumps(connections_data),
        'page_title': _('Network Architecture - Z96A'),
    }
    return render(request, 'core/network_architecture.html', context)

def news(request):
    """Страница новостей"""
    try:
        news_items = NewsParser.get_latest_news()
    except:
        # Если парсер не работает, показываем примерные новости
        news_items = [
            {"title": "Обновление инфраструктуры сетей", "source": "Habr", "url": "#", "date": "2026-01-19"},
            {"title": "SUI Blockchain Offline Transactions", "source": "Twitter", "url": "#", "date": "2026-01-18"},
            {"title": "Starlink расширяет покрытие", "source": "Reddit", "url": "#", "date": "2026-01-17"},
        ]
    
    # УБЕРИ ЭТУ СТРОКУ (или закомментируй):
    # sources = NewsArticle.SOURCE_CHOICES
    
    context = {
        'title': 'Новости инфокоммуникаций',
        'news_items': news_items,
        # 'sources': sources,  # УБЕРИ ИЛИ ЗАКОММЕНТИРУЙ
    }
    return render(request, 'core/news.html', context)

def discussion(request):
    """Discussion forum page"""
    comments = Comment.objects.filter(parent_comment__isnull=True).order_by('-is_pinned', '-created_at')
    
    # Pagination
    paginator = Paginator(comments, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': _('Discussion - Z96A'),
    }
    return render(request, 'core/discussion.html', context)

def about(request):
    """About page"""
    context = {
        'page_title': _('About Us - Z96A'),
    }
    return render(request, 'core/about.html', context)

def roadmap(request):
    """Roadmap page"""
    roadmap_data = [
        {
            'quarter': 'Q1 2026',
            'title': _('Stage 1: Web Project Implementation'),
            'items': [
                _('Web project realization'),
                _('Network architecture visualization creation'),
                _('Web3 integration for network interaction'),
                _('Discussion forum implementation'),
                _('Infocommunication news parser'),
            ]
        },
        {
            'quarter': 'Q2 2026',
            'title': _('Stage 2: Token Launch and Expansion'),
            'items': [
                _('Z96A token launch on pump.fun'),
                _('Token integration for project operations'),
                _('Funding system implementation'),
                _('Community governance features'),
            ]
        },
        {
            'quarter': 'Q3 2026',
            'title': _('Stage 3: Advanced Features'),
            'items': [
                _('Real-time network monitoring'),
                _('Predictive analytics implementation'),
                _('Mobile application development'),
                _('API for third-party integrations'),
            ]
        },
        {
            'quarter': 'Q4 2026',
            'title': _('Stage 4: Global Expansion'),
            'items': [
                _('Multilingual support expansion'),
                _('Regional network specialization'),
                _('Partnership program launch'),
                _('Research paper publication'),
            ]
        }
    ]
    
    context = {
        'roadmap': roadmap_data,
        'page_title': _('Roadmap - Z96A'),
    }
    return render(request, 'core/roadmap.html', context)

@login_required
def submit_proposal(request):
    """Handle user proposal submission"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Verify Solana transaction
            solana_client = SolanaClient()
            tx_valid = solana_client.verify_transaction(
                data['tx_signature'],
                request.user.wallet_address
            )
            
            if not tx_valid:
                return JsonResponse({'error': _('Invalid transaction signature')}, status=400)
            
            # Create proposal
            proposal = UserProposal.objects.create(
                user=request.user,
                proposal_type=data['proposal_type'],
                title=data['title'],
                description=data['description'],
                target_node_id=data.get('target_node'),
                proposed_equipment_id=data.get('proposed_equipment'),
                quantity=data.get('quantity', 1),
                justification=data['justification'],
                solana_tx_signature=data['tx_signature'],
            )
            
            return JsonResponse({
                'success': True,
                'proposal_id': str(proposal.id),
                'message': _('Proposal submitted successfully')
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': _('Invalid request method')}, status=405)

def get_node_details(request, node_id):
    """Get detailed information about a network node"""
    node = get_object_or_404(NetworkNode, id=node_id)
    
    # Get installed equipment
    installed_equipment = node.installed_equipment.select_related('equipment').all()
    
    # Get user proposals for this node
    proposals = UserProposal.objects.filter(target_node=node).order_by('-created_at')
    
    data = {
        'node': {
            'id': str(node.id),
            'name': node.name,
            'type': node.get_node_type_display(),
            'network_type': node.get_network_type_display(),
            'coordinates': [node.longitude, node.latitude, node.altitude],
            'location': f"{node.city}, {node.country}",
            'description': node.description,
            'capacity': node.capacity_gbps,
            'created_at': node.created_at.isoformat(),
        },
        'equipment': [
            {
                'id': str(item.id),
                'name': item.equipment.name,
                'type': item.equipment.get_equipment_type_display(),
                'manufacturer': item.equipment.manufacturer,
                'model': item.equipment.model,
                'quantity': item.quantity,
                'status': item.get_status_display(),
                'image_url': item.equipment.image.url if item.equipment.image else None,
                'specifications': item.equipment.specifications,
            }
            for item in installed_equipment
        ],
        'proposals': [
            {
                'id': str(p.id),
                'title': p.title,
                'type': p.get_proposal_type_display(),
                'user': p.user.nickname,
                'status': p.get_status_display(),
                'created_at': p.created_at.isoformat(),
                'solana_tx': p.solana_tx_signature,
                'solana_tx_url': f"https://solscan.io/tx/{p.solana_tx_signature}",
            }
            for p in proposals
        ]
    }
    
    return JsonResponse(data)

def update_news(request):
    """Trigger news update manually (admin only)"""
    if not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied')}, status=403)
    
    try:
        parser = NewsParser()
        new_articles = parser.fetch_all_news()
        
        return JsonResponse({
            'success': True,
            'message': _('News updated successfully'),
            'new_articles': len(new_articles)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)