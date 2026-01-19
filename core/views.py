# core/views.py - ПОЛНЫЙ ФУНКЦИОНАЛ
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
from django.views.decorators.csrf import csrf_exempt

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
    return render(request, 'core/index.html', context)

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
    """News page"""
    # Временные тестовые данные вместо парсера
    news_items = [
        {"title": "SUI Blockchain Offline Transactions Research", "source": "Twitter", "url": "#", "date": "2026-01-19"},
        {"title": "Starlink Expands Global Coverage", "source": "Reddit", "url": "#", "date": "2026-01-18"},
        {"title": "New Submarine Cable Connects Europe and Africa", "source": "Habr", "url": "#", "date": "2026-01-17"},
        {"title": "5G Network Infrastructure Updates", "source": "Twitter", "url": "#", "date": "2026-01-16"},
        {"title": "Blockchain for Network Resilience", "source": "Habr", "url": "#", "date": "2026-01-15"},
    ]
    
    context = {
        'title': 'Infocommunication News',
        'news_items': news_items,
    }
    return render(request, 'core/news.html', context)

def discussion(request):
    """Discussion forum page"""
    comments = Comment.objects.filter(parent_comment__isnull=True).order_by('-is_pinned', '-created_at')
    
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
    ]
    
    context = {
        'roadmap': roadmap_data,
        'page_title': _('Roadmap - Z96A'),
    }
    return render(request, 'core/roadmap.html', context)

@csrf_exempt
def connect_wallet(request):
    """Connect Solana wallet"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            wallet_address = data.get('address')
            
            if wallet_address:
                request.session['wallet_address'] = wallet_address
                return JsonResponse({
                    'status': 'success',
                    'message': 'Wallet connected',
                    'address': wallet_address
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=400)

def get_node_details(request, node_id):
    """Get detailed information about a network node"""
    try:
        node = NetworkNode.objects.get(id=node_id)
        return JsonResponse({
            'name': node.name,
            'type': node.node_type,
            'location': f"{node.latitude}, {node.longitude}",
            'network_type': node.get_network_type_display(),
            'description': node.description or 'No description available',
            'equipment': list(node.equipment.values('name', 'type', 'status'))
        })
    except NetworkNode.DoesNotExist:
        return JsonResponse({'error': 'Node not found'}, status=404)