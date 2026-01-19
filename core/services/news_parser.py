import requests
import json
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import feedparser
from django.utils.timezone import make_aware
from django.conf import settings
from ..models import NewsArticle

class NewsParser:
    """News parser for various sources"""
    
    def __init__(self):
        self.sources = settings.NEWS_SOURCES
    
    def fetch_all_news(self) -> List[NewsArticle]:
        """Fetch news from all configured sources"""
        all_articles = []
        
        # Fetch from Habr (RSS)
        habr_articles = self.parse_habr_rss()
        all_articles.extend(habr_articles)
        
        # Fetch from Reddit (API)
        reddit_articles = self.parse_reddit()
        all_articles.extend(reddit_articles)
        
        # Save to database
        saved_count = 0
        for article_data in all_articles:
            try:
                # Check if article already exists
                if not NewsArticle.objects.filter(source_url=article_data['source_url']).exists():
                    NewsArticle.objects.create(**article_data)
                    saved_count += 1
            except Exception as e:
                print(f"Error saving article: {e}")
        
        return all_articles
    
    def parse_habr_rss(self) -> List[Dict[str, Any]]:
        """Parse Habr RSS feed"""
        articles = []
        
        try:
            feed = feedparser.parse(self.sources['habr'])
            
            for entry in feed.entries[:20]:  # Limit to 20 articles
                # Filter for relevant topics
                title = entry.title
                content = entry.get('summary', '')
                
                if self._is_relevant_article(title, content):
                    article = {
                        'title': title,
                        'content': content,
                        'excerpt': content[:500] + '...' if len(content) > 500 else content,
                        'source': 'habr',
                        'source_url': entry.link,
                        'author': entry.get('author', 'Habr User'),
                        'published_date': make_aware(datetime(*entry.published_parsed[:6])),
                        'category': self._extract_category(entry),
                        'tags': entry.get('tags', []),
                        'is_featured': False,
                    }
                    articles.append(article)
                    
        except Exception as e:
            print(f"Error parsing Habr RSS: {e}")
        
        return articles
    
    def parse_reddit(self) -> List[Dict[str, Any]]:
        """Parse Reddit posts"""
        articles = []
        
        try:
            response = requests.get(
                self.sources['reddit'],
                headers={'User-Agent': 'Z96A-News-Parser/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for post in data['data']['children'][:25]:  # Limit to 25 posts
                    post_data = post['data']
                    
                    # Check if post is relevant
                    title = post_data['title']
                    content = post_data.get('selftext', '')
                    
                    if self._is_relevant_article(title, content):
                        article = {
                            'title': title,
                            'content': content,
                            'excerpt': content[:500] + '...' if len(content) > 500 else content,
                            'source': 'reddit',
                            'source_url': f"https://reddit.com{post_data['permalink']}",
                            'author': post_data['author'],
                            'published_date': make_aware(datetime.fromtimestamp(post_data['created_utc'])),
                            'category': post_data.get('subreddit', ''),
                            'tags': [post_data.get('link_flair_text', '')] if post_data.get('link_flair_text') else [],
                            'is_featured': post_data.get('score', 0) > 100,
                        }
                        articles.append(article)
                        
        except Exception as e:
            print(f"Error parsing Reddit: {e}")
        
        return articles
    
    def _is_relevant_article(self, title: str, content: str) -> bool:
        """Check if article is relevant to infocommunication networks"""
        keywords = [
            'network', 'telecom', 'infrastructure', '5G', 'fiber', 'satellite',
            'internet', 'blockchain', 'sui', 'starlink', 'iot', 'cloud',
            'data center', 'cybersecurity', 'router', 'switch', 'cable',
            'wireless', 'mobile', 'broadband', 'connectivity', 'latency',
            'bandwidth', 'protocol', 'tcp/ip', 'bgp', 'dns', 'vpn'
        ]
        
        text = (title + ' ' + content).lower()
        
        # Check for at least 2 keywords
        keyword_count = sum(1 for keyword in keywords if keyword in text)
        return keyword_count >= 2
    
    def _extract_category(self, entry) -> str:
        """Extract category from feed entry"""
        # Try to get category from different fields
        if hasattr(entry, 'tags') and entry.tags:
            return entry.tags[0].term
        elif hasattr(entry, 'category'):
            return entry.category
        return 'General'