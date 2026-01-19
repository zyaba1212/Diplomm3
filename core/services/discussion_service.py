"""
Discussion service layer
Handles discussion and comment business logic
"""

import logging
from typing import Dict, Tuple, Optional, List
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache

from ..models import Discussion, Cable, News
from .user_service import UserService

logger = logging.getLogger(__name__)


class DiscussionService:
    """Service for discussion operations"""
    
    @staticmethod
    def create_discussion(user: User, content: str, title: str = "",
                         content_type: str = 'general', cable_id: str = None,
                         news_id: int = None) -> Tuple[bool, str, Optional[Discussion]]:
        """
        Create new discussion
        Returns: (success, message, discussion)
        """
        try:
            # Validate content
            if not content or len(content.strip()) < 10:
                return False, "Content must be at least 10 characters", None
            
            if len(content) > 5000:
                return False, "Content too long (max 5000 characters)", None
            
            # Get related objects
            cable = None
            if cable_id:
                try:
                    cable = Cable.objects.get(cable_id=cable_id)
                except Cable.DoesNotExist:
                    return False, f"Cable {cable_id} not found", None
            
            news = None
            if news_id:
                try:
                    news = News.objects.get(id=news_id, is_published=True)
                except News.DoesNotExist:
                    return False, "News article not found", None
            
            # Create discussion
            discussion = Discussion.objects.create(
                title=title.strip(),
                content=content.strip(),
                content_type=content_type,
                user=user,
                author_name=user.username,
                author_email=user.email if user.email else '',
                cable=cable,
                news=news,
                is_approved=True,  # Auto-approve for now
            )
            
            # Update user profile
            profile = UserService.get_user_profile(user)
            if profile:
                profile.discussions_count += 1
                profile.save()
            
            # Clear cache
            cache.delete_pattern('discussion_*')
            
            logger.info(f"Discussion created by {user.username}: {discussion.id}")
            return True, "Discussion created successfully", discussion
            
        except Exception as e:
            logger.error(f"Error creating discussion: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def create_reply(user: User, parent: Discussion, content: str) -> Tuple[bool, str, Optional[Discussion]]:
        """
        Create reply to discussion
        Returns: (success, message, reply)
        """
        try:
            # Validate content
            if not content or len(content.strip()) < 5:
                return False, "Reply must be at least 5 characters", None
            
            if len(content) > 2000:
                return False, "Reply too long (max 2000 characters)", None
            
            # Create reply
            reply = Discussion.objects.create(
                content=content.strip(),
                content_type=parent.content_type,
                user=user,
                author_name=user.username,
                author_email=user.email if user.email else '',
                parent=parent,
                cable=parent.cable,
                news=parent.news,
                is_approved=True,
            )
            
            # Update parent reply count
            parent.update_reply_count()
            
            # Update user profile
            profile = UserService.get_user_profile(user)
            if profile:
                profile.discussions_count += 1
                profile.save()
            
            # Clear cache
            cache.delete(f"discussion_{parent.id}_replies")
            
            logger.info(f"Reply created by {user.username} to discussion {parent.id}")
            return True, "Reply added successfully", reply
            
        except Exception as e:
            logger.error(f"Error creating reply: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def vote_discussion(user: User, discussion: Discussion, vote_type: str) -> Tuple[bool, str]:
        """
        Vote on discussion (upvote/downvote)
        Returns: (success, message)
        """
        try:
            # Check if user already voted (simplified - in production use ManyToMany)
            # For now, we'll allow multiple votes
            
            if vote_type == 'upvote':
                discussion.upvotes += 1
            elif vote_type == 'downvote':
                discussion.downvotes += 1
            else:
                return False, "Invalid vote type"
            
            discussion.save()
            
            # Award points to discussion author for upvotes
            if vote_type == 'upvote' and discussion.user:
                UserService.award_points(
                    user=discussion.user,
                    amount=0.5,
                    reason=f"Received upvote on discussion"
                )
            
            logger.info(f"User {user.username} {vote_type}d discussion {discussion.id}")
            return True, "Vote recorded"
            
        except Exception as e:
            logger.error(f"Error voting on discussion: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_discussion_with_replies(discussion_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        Get discussion with all replies
        Returns: (success, message, data)
        """
        cache_key = f"discussion_{discussion_id}_full"
        cached = cache.get(cache_key)
        
        if cached:
            return True, "Retrieved from cache", cached
        
        try:
            discussion = Discussion.objects.get(
                id=discussion_id,
                is_approved=True
            )
            
            # Get all replies
            replies = discussion.replies.filter(
                is_approved=True
            ).order_by('created_at')
            
            # Format data
            data = {
                'discussion': {
                    'id': discussion.id,
                    'title': discussion.title,
                    'content': discussion.content,
                    'author': discussion.author_name,
                    'user_id': discussion.user.id if discussion.user else None,
                    'created_at': discussion.created_at.isoformat(),
                    'upvotes': discussion.upvotes,
                    'downvotes': discussion.downvotes,
                    'vote_score': discussion.vote_score(),
                    'reply_count': discussion.reply_count,
                    'is_pinned': discussion.is_pinned,
                    'is_featured': discussion.is_featured,
                    'content_type': discussion.content_type,
                    'cable': {
                        'id': discussion.cable.cable_id,
                        'name': discussion.cable.name,
                    } if discussion.cable else None,
                    'news': {
                        'id': discussion.news.id,
                        'title': discussion.news.title,
                    } if discussion.news else None,
                },
                'replies': [
                    {
                        'id': reply.id,
                        'content': reply.content,
                        'author': reply.author_name,
                        'user_id': reply.user.id if reply.user else None,
                        'created_at': reply.created_at.isoformat(),
                        'upvotes': reply.upvotes,
                        'downvotes': reply.downvotes,
                    }
                    for reply in replies
                ],
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, data, timeout=300)
            
            return True, "Retrieved successfully", data
            
        except Discussion.DoesNotExist:
            return False, "Discussion not found", None
        except Exception as e:
            logger.error(f"Error getting discussion {discussion_id}: {e}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def get_recent_discussions(limit: int = 20, content_type: str = None) -> List[Dict]:
        """Get recent discussions"""
        cache_key = f"recent_discussions_{content_type}_{limit}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            discussions = Discussion.objects.filter(
                is_approved=True,
                parent__isnull=True
            )
            
            if content_type:
                discussions = discussions.filter(content_type=content_type)
            
            discussions = discussions.order_by('-created_at')[:limit]
            
            result = []
            for discussion in discussions:
                result.append({
                    'id': discussion.id,
                    'title': discussion.title,
                    'content_preview': discussion.content[:100] + '...' if len(discussion.content) > 100 else discussion.content,
                    'author': discussion.author_name,
                    'created_at': discussion.created_at.isoformat(),
                    'reply_count': discussion.reply_count,
                    'vote_score': discussion.vote_score(),
                    'content_type': discussion.content_type,
                    'cable_name': discussion.cable.name if discussion.cable else None,
                    'news_title': discussion.news.title if discussion.news else None,
                })
            
            # Cache for 2 minutes
            cache.set(cache_key, result, timeout=120)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent discussions: {e}")
            return []
    
    @staticmethod
    def get_discussions_by_cable(cable_id: str, limit: int = 50) -> List[Dict]:
        """Get discussions for a specific cable"""
        cache_key = f"cable_discussions_{cable_id}_{limit}"
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            cable = Cable.objects.get(cable_id=cable_id)
            
            discussions = Discussion.objects.filter(
                cable=cable,
                is_approved=True,
                parent__isnull=True
            ).order_by('-created_at')[:limit]
            
            result = []
            for discussion in discussions:
                result.append({
                    'id': discussion.id,
                    'title': discussion.title,
                    'content_preview': discussion.content[:150] + '...' if len(discussion.content) > 150 else discussion.content,
                    'author': discussion.author_name,
                    'created_at': discussion.created_at.isoformat(),
                    'reply_count': discussion.reply_count,
                    'vote_score': discussion.vote_score(),
                })
            
            # Cache for 5 minutes
            cache.set(cache_key, result, timeout=300)
            
            return result
            
        except Cable.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"Error getting cable discussions: {e}")
            return []
    
    @staticmethod
    def moderate_discussion(discussion_id: int, action: str, reason: str = "") -> Tuple[bool, str]:
        """
        Moderate discussion (approve, reject, delete)
        Returns: (success, message)
        """
        try:
            discussion = Discussion.objects.get(id=discussion_id)
            
            if action == 'approve':
                discussion.is_approved = True
                message = "Discussion approved"
                
            elif action == 'reject':
                discussion.is_approved = False
                message = "Discussion rejected"
                
            elif action == 'delete':
                # Get user for notification
                user = discussion.user
                discussion.delete()
                
                # Notify user if exists
                if user:
                    # In production, send email notification
                    pass
                
                message = "Discussion deleted"
                
            elif action == 'feature':
                discussion.is_featured = not discussion.is_featured
                message = f"Discussion {'featured' if discussion.is_featured else 'unfeatured'}"
                
            elif action == 'pin':
                discussion.is_pinned = not discussion.is_pinned
                message = f"Discussion {'pinned' if discussion.is_pinned else 'unpinned'}"
                
            else:
                return False, "Invalid moderation action"
            
            if action != 'delete':
                discussion.save()
            
            # Clear cache
            cache.delete_pattern('discussion_*')
            cache.delete_pattern('recent_discussions_*')
            
            logger.info(f"Discussion {discussion_id} moderated: {action} - {reason}")
            return True, message
            
        except Discussion.DoesNotExist:
            return False, "Discussion not found"
        except Exception as e:
            logger.error(f"Error moderating discussion: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def search_discussions(query: str, limit: int = 50) -> List[Dict]:
        """Search discussions by content"""
        try:
            from django.db.models import Q
            
            discussions = Discussion.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query),
                is_approved=True,
                parent__isnull=True
            ).order_by('-created_at')[:limit]
            
            result = []
            for discussion in discussions:
                result.append({
                    'id': discussion.id,
                    'title': discussion.title,
                    'content_preview': discussion.content[:200] + '...' if len(discussion.content) > 200 else discussion.content,
                    'author': discussion.author_name,
                    'created_at': discussion.created_at.isoformat(),
                    'reply_count': discussion.reply_count,
                    'vote_score': discussion.vote_score(),
                    'content_type': discussion.content_type,
                    'cable_name': discussion.cable.name if discussion.cable else None,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching discussions: {e}")
            return []
    
    @staticmethod
    def get_discussion_statistics() -> Dict:
        """Get discussion statistics"""
        cache_key = 'discussion_statistics'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            from django.db.models import Count
            
            # Total discussions
            total = Discussion.objects.filter(is_approved=True).count()
            
            # By content type
            by_type = dict(
                Discussion.objects.filter(is_approved=True).values_list(
                    'content_type'
                ).annotate(
                    count=Count('id')
                )
            )
            
            # Recent activity (last 7 days)
            week_ago = timezone.now() - timezone.timedelta(days=7)
            recent = Discussion.objects.filter(
                is_approved=True,
                created_at__gte=week_ago
            ).count()
            
            # Top cables by discussions
            top_cables = list(
                Discussion.objects.filter(
                    is_approved=True,
                    cable__isnull=False
                ).values(
                    'cable__cable_id',
                    'cable__name'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')[:10]
            )
            
            stats = {
                'total': total,
                'by_type': by_type,
                'recent_week': recent,
                'top_cables': top_cables,
                'updated_at': timezone.now().isoformat(),
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, stats, timeout=600)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting discussion statistics: {e}")
            return {}