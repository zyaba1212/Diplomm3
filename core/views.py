"""
Views for Z96A Network
Refactored with service layer, error handling, and API endpoints.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
import json
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes

from .models import (
    Cable, LandingPoint, Equipment, BlockchainTransaction,
    News, Discussion, UserProfile, SystemLog, Region
)
from .services import (
    BlockchainService, CableService, UserService,
    DiscussionService, NewsService
)
from .utils.validators import validate_request_data
from .utils.helpers import api_response

logger = logging.getLogger(__name__)


# ==================== MAIN PAGES ====================

def index(request):
    """Home page with 3D globe"""
    try:
        featured_cables = Cable.objects.filter(
            is_featured=True, 
            status='active'
        )[:10]
        
        recent_news = News.objects.filter(
            is_published=True
        ).order_by('-published_date')[:5]
        
        cable_stats = {
            'total': Cable.objects.count(),
            'active': Cable.objects.filter(status='active').count(),
            'total_length': Cable.objects.aggregate(Sum('length'))['length__sum'] or 0,
            'total_capacity': Cable.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0,
        }
        
        context = {
            'featured_cables': featured_cables,
            'recent_news': recent_news,
            'cable_stats': cable_stats,
            'page_title': 'Global Cable Network Visualization',
        }
        return render(request, 'index.html', context)
        
    except Exception as e:
        logger.error(f"Error in index view: {e}", exc_info=True)
        return render(request, 'error.html', {
            'error_message': 'Unable to load page. Please try again later.'
        })


def about(request):
    """About page"""
    return render(request, 'about.html', {
        'page_title': 'About Z96A Network'
    })


def architecture(request):
    """System architecture page"""
    return render(request, 'architecture.html', {
        'page_title': 'System Architecture'
    })


def roadmap(request):
    """Project roadmap page"""
    return render(request, 'roadmap.html', {
        'page_title': 'Project Roadmap'
    })


# ==================== CABLE VIEWS ====================

class CableListView(View):
    """List all cables with filtering and pagination"""
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request):
        try:
            # Get filter parameters
            status_filter = request.GET.get('status', '')
            region_filter = request.GET.get('region', '')
            search_query = request.GET.get('q', '')
            cable_type = request.GET.get('type', '')
            
            # Start with all cables
            cables = Cable.objects.all()
            
            # Apply filters
            if status_filter:
                cables = cables.filter(status=status_filter)
            
            if region_filter:
                cables = cables.filter(region__code=region_filter)
            
            if cable_type:
                cables = cables.filter(cable_type=cable_type)
            
            if search_query:
                cables = cables.filter(
                    Q(name__icontains=search_query) |
                    Q(cable_id__icontains=search_query) |
                    Q(alternative_name__icontains=search_query) |
                    Q(owners__icontains=search_query)
                )
            
            # Ordering
            order_by = request.GET.get('order_by', 'name')
            if order_by in ['name', 'length', 'capacity', 'created_at']:
                cables = cables.order_by(order_by)
            
            # Pagination
            paginator = Paginator(cables, 20)  # 20 cables per page
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Get statistics for filters
            regions = Region.objects.all()
            status_counts = Cable.objects.values('status').annotate(
                count=Count('id')
            )
            
            context = {
                'page_obj': page_obj,
                'regions': regions,
                'status_counts': status_counts,
                'total_cables': cables.count(),
                'filters': {
                    'status': status_filter,
                    'region': region_filter,
                    'q': search_query,
                    'type': cable_type,
                    'order_by': order_by,
                },
                'page_title': 'Submarine Cables',
            }
            
            return render(request, 'cables/list.html', context)
            
        except Exception as e:
            logger.error(f"Error in CableListView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading cables. Please try again.'
            })


class CableDetailView(View):
    """Detail view for a single cable"""
    
    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    def get(self, request, cable_id):
        try:
            cable = get_object_or_404(Cable, cable_id=cable_id)
            
            # Increment view count (async in production)
            if request.user.is_authenticated:
                UserService.record_cable_view(request.user, cable)
            
            # Get related data
            landing_points = cable.landing_points.all()
            equipment = cable.equipment.filter(is_active=True)
            discussions = cable.discussions.filter(
                is_approved=True
            ).order_by('-created_at')[:10]
            
            # Get similar cables
            similar_cables = Cable.objects.filter(
                region=cable.region,
                status='active'
            ).exclude(id=cable.id)[:5]
            
            # Get cable transactions
            transactions = cable.transactions.filter(
                status='confirmed'
            ).order_by('-created_at')[:5]
            
            context = {
                'cable': cable,
                'landing_points': landing_points,
                'equipment': equipment,
                'discussions': discussions,
                'similar_cables': similar_cables,
                'transactions': transactions,
                'page_title': f'{cable.name} - Submarine Cable',
            }
            
            return render(request, 'cables/detail.html', context)
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error in CableDetailView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading cable details.'
            })


# ==================== BLOCKCHAIN VIEWS ====================

class BlockchainAPIView(APIView):
    """Blockchain API endpoints"""
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        """Get blockchain information"""
        try:
            blockchain = BlockchainService.get_blockchain()
            
            data = {
                'chain_length': len(blockchain.chain),
                'pending_transactions': len(blockchain.pending_transactions),
                'difficulty': blockchain.difficulty,
                'mining_reward': blockchain.mining_reward,
                'is_valid': blockchain.is_chain_valid()[0],
            }
            
            return Response(data)
            
        except Exception as e:
            logger.error(f"Error in BlockchainAPIView GET: {e}", exc_info=True)
            return Response(
                {'error': 'Unable to retrieve blockchain data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @method_decorator(csrf_exempt)
    def post(self, request):
        """Add a new transaction"""
        try:
            # Validate request data
            required_fields = ['sender', 'recipient', 'amount', 'signature']
            validation_result = validate_request_data(request.data, required_fields)
            
            if not validation_result['valid']:
                return Response(
                    {'error': validation_result['message']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Add transaction to blockchain
            success, message = BlockchainService.add_transaction(request.data)
            
            if success:
                return Response(
                    {'message': message, 'success': True},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': message, 'success': False},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error in BlockchainAPIView POST: {e}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletView(LoginRequiredMixin, View):
    """User wallet view"""
    
    def get(self, request):
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            
            # Get transactions
            transactions = BlockchainTransaction.objects.filter(
                Q(sender=user_profile.wallet_address) |
                Q(recipient=user_profile.wallet_address)
            ).order_by('-created_at')[:50]
            
            # Get balance from blockchain
            blockchain = BlockchainService.get_blockchain()
            balance = blockchain.get_balance(user_profile.wallet_address)
            
            context = {
                'profile': user_profile,
                'transactions': transactions,
                'blockchain_balance': balance,
                'page_title': 'My Wallet',
            }
            
            return render(request, 'wallet/index.html', context)
            
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            UserService.create_user_profile(request.user)
            return redirect('wallet')
        except Exception as e:
            logger.error(f"Error in WalletView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading wallet.'
            })
    
    def post(self, request):
        """Handle wallet actions (transfer, etc.)"""
        try:
            action = request.POST.get('action')
            user_profile = UserProfile.objects.get(user=request.user)
            
            if action == 'transfer':
                # Validate transfer data
                recipient = request.POST.get('recipient')
                amount = float(request.POST.get('amount', 0))
                description = request.POST.get('description', '')
                
                if not recipient or amount <= 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid recipient or amount'
                    })
                
                # Create and sign transaction
                success, message = UserService.create_transfer(
                    user=request.user,
                    recipient=recipient,
                    amount=amount,
                    description=description
                )
                
                return JsonResponse({
                    'success': success,
                    'message': message
                })
                
            elif action == 'refresh':
                # Refresh balance from blockchain
                blockchain = BlockchainService.get_blockchain()
                balance = blockchain.get_balance(user_profile.wallet_address)
                
                # Update profile balance
                user_profile.balance = balance
                user_profile.save()
                
                return JsonResponse({
                    'success': True,
                    'balance': float(balance),
                    'message': 'Balance updated'
                })
            
            return JsonResponse({
                'success': False,
                'message': 'Unknown action'
            })
            
        except Exception as e:
            logger.error(f"Error in WalletView POST: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Internal server error'
            })


# ==================== NEWS VIEWS ====================

class NewsListView(View):
    """List all news articles"""
    
    @method_decorator(cache_page(60 * 2))  # Cache for 2 minutes
    def get(self, request):
        try:
            news_list = News.objects.filter(
                is_published=True
            ).order_by('-published_date')
            
            # Filter by category
            category = request.GET.get('category', '')
            if category:
                news_list = news_list.filter(category=category)
            
            # Search
            search_query = request.GET.get('q', '')
            if search_query:
                news_list = news_list.filter(
                    Q(title__icontains=search_query) |
                    Q(content__icontains=search_query) |
                    Q(excerpt__icontains=search_query)
                )
            
            # Pagination
            paginator = Paginator(news_list, 10)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Get categories for filter
            categories = News.CATEGORIES
            
            context = {
                'page_obj': page_obj,
                'categories': categories,
                'current_category': category,
                'search_query': search_query,
                'page_title': 'News & Updates',
            }
            
            return render(request, 'news/list.html', context)
            
        except Exception as e:
            logger.error(f"Error in NewsListView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading news.'
            })


class NewsDetailView(View):
    """Detail view for a news article"""
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def get(self, request, slug):
        try:
            news = get_object_or_404(News, slug=slug, is_published=True)
            
            # Increment view count
            news.increment_views()
            
            # Get related news
            related_news = News.objects.filter(
                category=news.category,
                is_published=True
            ).exclude(id=news.id)[:4]
            
            # Get discussions
            discussions = news.discussions.filter(
                is_approved=True
            ).order_by('-created_at')[:20]
            
            context = {
                'news': news,
                'related_news': related_news,
                'discussions': discussions,
                'page_title': news.title,
            }
            
            return render(request, 'news/detail.html', context)
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error in NewsDetailView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading news article.'
            })


# ==================== DISCUSSION VIEWS ====================

class DiscussionView(View):
    """Main discussion page"""
    
    def get(self, request):
        try:
            # Get discussions with filters
            content_type = request.GET.get('type', '')
            cable_id = request.GET.get('cable', '')
            
            discussions = Discussion.objects.filter(
                is_approved=True,
                parent__isnull=True  # Only top-level discussions
            ).order_by('-is_pinned', '-created_at')
            
            # Apply filters
            if content_type:
                discussions = discussions.filter(content_type=content_type)
            
            if cable_id:
                cable = get_object_or_404(Cable, cable_id=cable_id)
                discussions = discussions.filter(cable=cable)
            
            # Pagination
            paginator = Paginator(discussions, 25)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            
            # Get cables for filter
            cables = Cable.objects.filter(status='active')[:50]
            
            context = {
                'page_obj': page_obj,
                'cables': cables,
                'content_types': Discussion.CONTENT_TYPES,
                'filters': {
                    'type': content_type,
                    'cable': cable_id,
                },
                'page_title': 'Community Discussions',
            }
            
            return render(request, 'discussion/index.html', context)
            
        except Exception as e:
            logger.error(f"Error in DiscussionView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading discussions.'
            })
    
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def post(self, request):
        """Create new discussion"""
        try:
            # Validate data
            content = request.POST.get('content', '').strip()
            title = request.POST.get('title', '').strip()
            content_type = request.POST.get('content_type', 'general')
            cable_id = request.POST.get('cable_id', '')
            
            if not content:
                return JsonResponse({
                    'success': False,
                    'message': 'Content is required'
                })
            
            # Create discussion
            success, message, discussion = DiscussionService.create_discussion(
                user=request.user,
                content=content,
                title=title,
                content_type=content_type,
                cable_id=cable_id
            )
            
            if success:
                # Award points for participation
                UserService.award_points(
                    user=request.user,
                    amount=5.0,
                    reason='Created discussion'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Discussion created successfully',
                    'discussion_id': discussion.id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except Exception as e:
            logger.error(f"Error creating discussion: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Internal server error'
            })


class DiscussionDetailView(View):
    """Detail view for a discussion with replies"""
    
    def get(self, request, discussion_id):
        try:
            discussion = get_object_or_404(
                Discussion, 
                id=discussion_id,
                is_approved=True
            )
            
            # Get all replies
            replies = discussion.replies.filter(
                is_approved=True
            ).order_by('created_at')
            
            context = {
                'discussion': discussion,
                'replies': replies,
                'page_title': discussion.title or 'Discussion',
            }
            
            return render(request, 'discussion/detail.html', context)
            
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Error in DiscussionDetailView: {e}", exc_info=True)
            return render(request, 'error.html', {
                'error_message': 'Error loading discussion.'
            })
    
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def post(self, request, discussion_id):
        """Add reply to discussion"""
        try:
            discussion = get_object_or_404(Discussion, id=discussion_id)
            content = request.POST.get('content', '').strip()
            
            if not content:
                return JsonResponse({
                    'success': False,
                    'message': 'Content is required'
                })
            
            # Create reply
            success, message, reply = DiscussionService.create_reply(
                user=request.user,
                parent=discussion,
                content=content
            )
            
            if success:
                # Award points for participation
                UserService.award_points(
                    user=request.user,
                    amount=2.0,
                    reason='Replied to discussion'
                )
                
                # Update reply count
                discussion.update_reply_count()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Reply added successfully',
                    'reply_id': reply.id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except Exception as e:
            logger.error(f"Error adding reply: {e}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': 'Internal server error'
            })


# ==================== API VIEWS ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_cables(request):
    """API endpoint for cables data (for 3D globe)"""
    try:
        cables = Cable.objects.filter(status='active')
        
        data = []
        for cable in cables:
            cable_data = {
                'id': cable.cable_id,
                'name': cable.name,
                'length': cable.length,
                'capacity': cable.capacity,
                'coordinates': cable.get_coordinates_list(),
                'color': cable.get_status_color(),
                'status': cable.status,
                'type': cable.cable_type,
            }
            data.append(cable_data)
        
        return Response({
            'success': True,
            'count': len(data),
            'cables': data
        })
        
    except Exception as e:
        logger.error(f"Error in api_cables: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Unable to retrieve cable data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_wallet_balance(request):
    """API endpoint for wallet balance"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        blockchain = BlockchainService.get_blockchain()
        
        balance = blockchain.get_balance(user_profile.wallet_address)
        
        return Response({
            'success': True,
            'balance': float(balance),
            'address': user_profile.wallet_address
        })
        
    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'User profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in api_wallet_balance: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Unable to retrieve balance'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def api_create_transaction(request):
    """API endpoint to create blockchain transaction"""
    try:
        # Validate required fields
        required_fields = ['recipient', 'amount']
        validation_result = validate_request_data(request.data, required_fields)
        
        if not validation_result['valid']:
            return Response({
                'success': False,
                'error': validation_result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create transaction
        success, message = UserService.create_transfer(
            user=request.user,
            recipient=request.data['recipient'],
            amount=float(request.data['amount']),
            description=request.data.get('description', '')
        )
        
        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'error': message
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in api_create_transaction: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_blockchain_info(request):
    """API endpoint for blockchain information"""
    try:
        blockchain = BlockchainService.get_blockchain()
        
        data = {
            'chain_length': len(blockchain.chain),
            'pending_transactions': len(blockchain.pending_transactions),
            'difficulty': blockchain.difficulty,
            'mining_reward': blockchain.mining_reward,
            'is_valid': blockchain.is_chain_valid()[0],
            'last_block': blockchain.get_last_block().index if blockchain.chain else None,
        }
        
        return Response({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in api_blockchain_info: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': 'Unable to retrieve blockchain info'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== UTILITY VIEWS ====================

def handler404(request, exception):
    """Custom 404 handler"""
    return render(request, 'error.html', {
        'error_code': 404,
        'error_message': 'Page not found',
        'page_title': '404 - Page Not Found'
    }, status=404)


def handler500(request):
    """Custom 500 handler"""
    return render(request, 'error.html', {
        'error_code': 500,
        'error_message': 'Internal server error',
        'page_title': '500 - Server Error'
    }, status=500)


def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Check database
        Cable.objects.count()
        
        # Check blockchain
        blockchain = BlockchainService.get_blockchain()
        is_valid, _ = blockchain.is_chain_valid()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'blockchain': 'valid' if is_valid else 'invalid',
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)


@login_required
def user_dashboard(request):
    """User dashboard with stats and activities"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Get user statistics
        user_stats = {
            'cables_viewed': user_profile.cables_viewed.count(),
            'cables_favorited': user_profile.cables_favorited.count(),
            'discussions_created': user_profile.discussions_count,
            'transactions_made': user_profile.transactions_count,
            'total_earned': float(user_profile.total_earned),
            'total_spent': float(user_profile.total_spent),
        }
        
        # Get recent activities
        recent_transactions = BlockchainTransaction.objects.filter(
            Q(sender=user_profile.wallet_address) |
            Q(recipient=user_profile.wallet_address)
        ).order_by('-created_at')[:10]
        
        recent_discussions = Discussion.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
        
        context = {
            'profile': user_profile,
            'user_stats': user_stats,
            'recent_transactions': recent_transactions,
            'recent_discussions': recent_discussions,
            'page_title': 'My Dashboard',
        }
        
        return render(request, 'user/dashboard.html', context)
        
    except UserProfile.DoesNotExist:
        UserService.create_user_profile(request.user)
        return redirect('user_dashboard')
    except Exception as e:
        logger.error(f"Error in user_dashboard: {e}", exc_info=True)
        return render(request, 'error.html', {
            'error_message': 'Error loading dashboard.'
        })