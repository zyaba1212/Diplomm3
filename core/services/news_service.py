"""
News service layer
Handles news-related business logic
"""

import logging
import feedparser
from typing import Dict, Tuple, Optional, List
from datetime import datetime
from django.utils import timezone
from django.core.cache import cache

from ..models import News, Cable

logger = logging.getLogger(__name__)


class NewsService:
    """Service for news operations"""
    
    @staticmethod
    def create_news(title: str, content: str, author: str = "",
                   category: str = 'project', tags: str = "",
                   image_url: str = None, source_url: str = None,
                   related_cables: List[str] = None) -> Tuple[bool, str, Optional[News]]:
        """
        Create news article
        Returns: (success, message, news)
        """
        try:
            # Validate required fields
            if not title or not content:
                return False, "Title and content are required", None
            
            # Create slug from title
            from django.utils.text import slugify
            slug = slugify(title)
            
            # Check if slug already exists
            counter = 1
            original_slug = slug
            while News.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Create excerpt if not provided
            excerpt = content[:200] + '...' if len(content) > 200 else content
            
            # Create news
            news = News.objects.create(
                title=title.strip(),
                slug=slug,
                content=content.strip(),
                excerpt=excerpt,
                category=category,
                tags=tags,
                author=author.strip() or "Z96A Team",
                source_url=source_url,
                is_published=False,  # Draft by default
            )
            
            # Add related cables
            if related_cables:
                for cable_id in related_cables:
                    try:
                        cable = Cable.objects.get(cable_id=cable_id)
                        news.related_cables.add(cable)
                    except Cable.DoesNotExist:
                        logger.warning(f"Cable {cable_id} not found for news {news.id}")
            
            # Clear cache
            cache.delete_pattern('news_*')
            cache.delete('recent_news')
            
            logger.info(f"News created: {news.slug}")
            return True, "News created successfully", news
            
        except Exception as e:
            logger.error(f"Error creating news: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def publish_news(news_id: int) -> Tuple[bool, str]:
        """
        Publish news article
        Returns: (success, message)
        """
        try:
            news = News.objects.get(id=news_id)
            
            if news.is_published:
                return True, "News already published"
            
            news.publish()
            
            # Clear cache
            cache.delete_pattern('news_*')
            cache.delete('recent_news')
            
            logger.info(f"News published: {news.slug}")
            return True, "News published successfully"
            
        except News.DoesNotExist:
            return False, "News not found"
        except Exception as e:
            logger.error(f"Error publishing news: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_news_by_slug(slug: str) -> Optional[News]:
        """Get news by slug with caching"""
        cache_key = f"news_{slug}"
        news = cache.get(cache_key)
        
        if not news:
            try:
                news = News.objects.get(slug=slug, is_published=True)
                cache.set(cache_key, news, timeout=300)  # 5 minutes
            except News.DoesNotExist:
                return None
        
        return news
    
    @staticmethod
    def get_recent_news(limit: int = 10, category: str = None) -> List[News]:
        """Get recent news articles"""
        cache_key = f"recent_news_{category}_{limit}"
        news_list = cache.get(cache_key)
        
        if not news_list:
            try:
                news_list = News.objects.filter(is_published=True)
                
                if category:
                    news_list = news_list.filter(category=category)
                
                news_list = list(news_list.order_by('-published_date')[:limit])
                cache.set(cache_key, news_list, timeout=300)  # 5 minutes
            except Exception as e:
                logger.error(f"Error getting recent news: {e}")
                news_list = []
        
        return news_list
    
    @staticmethod
    def get_news_statistics() -> Dict:
        """Get news statistics"""
        cache_key = 'news_statistics'
        stats = cache.get(cache_key)
        
        if not stats:
            try:
                from django.db.models import Count, Sum
                
                # Total news
                total = News.objects.filter(is_published=True).count()
                
                # By category
                by_category = dict(
                    News.objects.filter(is_published=True).values_list(
                        'category'
                    ).annotate(
                        count=Count('id')
                    )
                )
                
                # Views and engagement
                engagement = News.objects.filter(is_published=True).aggregate(
                    total_views=Sum('views'),
                    total_likes=Sum('likes'),
                    total_shares=Sum('shares'),
                    avg_views=Sum('views') / Count('id'),
                )
                
                # Recent activity (last 30 days)
                month_ago = timezone.now() - timezone.timedelta(days=30)
                recent = News.objects.filter(
                    is_published=True,
                    published_date__gte=month_ago
                ).count()
                
                stats = {
                    'total': total,
                    'by_category': by_category,
                    'engagement': engagement,
                    'recent_month': recent,
                    'updated_at': timezone.now().isoformat(),
                }
                
                cache.set(cache_key, stats, timeout=600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"Error getting news statistics: {e}")
                stats = {}
        
        return stats
    
    @staticmethod
    def import_from_rss(feed_url: str, category: str = 'cable') -> Tuple[int, int, List[str]]:
        """
        Import news from RSS feed
        Returns: (imported_count, skipped_count, errors)
        """
        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                logger.error(f"Error parsing RSS feed: {feed.bozo_exception}")
                return 0, 0, [str(feed.bozo_exception)]
            
            imported = 0
            skipped = 0
            errors = []
            
            for entry in feed.entries[:10]:  # Limit to 10 entries
                try:
                    # Check if news already exists by title
                    title = entry.title
                    if News.objects.filter(title=title).exists():
                        skipped += 1
                        continue
                    
                    # Extract content
                    content = ''
                    if hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # Extract publication date
                    published_date = timezone.now()
                    if hasattr(entry, 'published_parsed'):
                        published_date = datetime(*entry.published_parsed[:6])
                    
                    # Extract image
                    image_url = None
                    if hasattr(entry, 'links'):
                        for link in entry.links:
                            if link.type.startswith('image/'):
                                image_url = link.href
                                break
                    
                    # Extract source URL
                    source_url = entry.link if hasattr(entry, 'link') else None
                    
                    # Create news
                    success, message, news = NewsService.create_news(
                        title=title,
                        content=content,
                        author=entry.author if hasattr(entry, 'author') else feed.feed.title,
                        category=category,
                        tags=', '.join([tag.term for tag in entry.tags]) if hasattr(entry, 'tags') else '',
                        image_url=image_url,
                        source_url=source_url,
                    )
                    
                    if success:
                        # Set publication date and publish
                        news.published_date = published_date
                        news.is_published = True
                        news.save()
                        
                        imported += 1
                        logger.info(f"Imported news from RSS: {title}")
                    else:
                        errors.append(f"Failed to create news '{title}': {message}")
                        skipped += 1
                        
                except Exception as e:
                    errors.append(f"Error processing entry '{entry.title}': {str(e)}")
                    skipped += 1
            
            logger.info(f"RSS import completed: {imported} imported, {skipped} skipped")
            return imported, skipped, errors
            
        except Exception as e:
            logger.error(f"Error importing from RSS: {e}", exc_info=True)
            return 0, 0, [str(e)]
    
    @staticmethod
    def search_news(query: str, limit: int = 20) -> List[Dict]:
        """Search news articles"""
        try:
            from django.db.models import Q
            
            news_list = News.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(tags__icontains=query),
                is_published=True
            ).order_by('-published_date')[:limit]
            
            result = []
            for news in news_list:
                result.append({
                    'id': news.id,
                    'title': news.title,
                    'slug': news.slug,
                    'excerpt': news.excerpt,
                    'category': news.category,
                    'published_date': news.published_date.isoformat() if news.published_date else None,
                    'author': news.author,
                    'views': news.views,
                    'likes': news.likes,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []
    
    @staticmethod
    def increment_views(news_id: int) -> bool:
        """Increment news view count"""
        try:
            news = News.objects.get(id=news_id)
            news.increment_views()
            return True
        except News.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error incrementing news views: {e}")
            return False
    
    @staticmethod
    def get_related_news(news_id: int, limit: int = 4) -> List[News]:
        """Get related news articles"""
        try:
            news = News.objects.get(id=news_id)
            
            # Get news with same category
            related = News.objects.filter(
                category=news.category,
                is_published=True
            ).exclude(id=news_id)[:limit]
            
            # If not enough, get any recent news
            if len(related) < limit:
                additional = News.objects.filter(
                    is_published=True
                ).exclude(
                    id=news_id
                ).exclude(
                    id__in=[n.id for n in related]
                ).order_by('-published_date')[:limit - len(related)]
                
                related = list(related) + list(additional)
            
            return list(related)
            
        except News.DoesNotExist:
            return []
        except Exception as e:
            logger.error(f"Error getting related news: {e}")
            return []
    
    @staticmethod
    def export_news(format: str = 'json') -> Tuple[bool, str, Optional[str]]:
        """
        Export news data
        Returns: (success, message, data_or_filename)
        """
        try:
            news_list = News.objects.filter(is_published=True)
            
            if format == 'json':
                data = []
                for news in news_list:
                    news_data = {
                        'id': news.id,
                        'title': news.title,
                        'slug': news.slug,
                        'content': news.content,
                        'excerpt': news.excerpt,
                        'category': news.category,
                        'tags': news.tags,
                        'author': news.author,
                        'published_date': news.published_date.isoformat() if news.published_date else None,
                        'views': news.views,
                        'likes': news.likes,
                        'shares': news.shares,
                        'source_url': news.source_url,
                        'related_cables': [
                            cable.cable_id for cable in news.related_cables.all()
                        ],
                        'created_at': news.created_at.isoformat(),
                    }
                    data.append(news_data)
                
                import json
                return True, "Export successful", json.dumps(data, indent=2)
            
            elif format == 'rss':
                # Generate RSS feed
                from django.contrib.syndication.views import Feed
                from django.utils.feedgenerator import Rss201rev2Feed
                from io import StringIO
                
                feed = Rss201rev2Feed(
                    title="Z96A Network News",
                    link="https://z96a.network/news/",
                    description="Latest news about submarine cables and network infrastructure",
                    language="en",
                )
                
                for news in news_list[:50]:  # Limit to 50 items
                    feed.add_item(
                        title=news.title,
                        link=f"https://z96a.network/news/{news.slug}/",
                        description=news.excerpt,
                        author_name=news.author,
                        pubdate=news.published_date or news.created_at,
                    )
                
                output = StringIO()
                feed.write(output, 'utf-8')
                
                return True, "Export successful", output.getvalue()
            
            else:
                return False, f"Unsupported format: {format}", None
                
        except Exception as e:
            logger.error(f"Error exporting news: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None