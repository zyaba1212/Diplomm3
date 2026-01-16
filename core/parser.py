import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from .models import NewsArticle
from django.conf import settings
import time

def parse_twitter():
    """Парсинг Twitter/X (упрощенная версия)"""
    # В реальном проекте используйте Twitter API
    articles = []
    
    try:
        # Демо данные
        articles.append({
            'title': 'Новые технологии в инфокоммуникационных сетях',
            'content': 'Развитие сетей 6G и квантовой связи открывает новые возможности...',
            'source': 'twitter',
            'url': 'https://twitter.com/technews/status/123456789',
            'published_date': datetime.now()
        })
    except Exception as e:
        print(f"Error parsing Twitter: {e}")
    
    return articles

def parse_reddit():
    """Парсинг Reddit"""
    articles = []
    
    try:
        url = settings.NEWS_SOURCES['reddit']
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Поиск постов (упрощенно)
            for post in soup.find_all('div', {'data-testid': 'post-container'})[:5]:
                try:
                    title_elem = post.find('h3')
                    if title_elem:
                        title = title_elem.text.strip()
                        link = post.find('a', {'data-click-id': 'body'})
                        url = f"https://reddit.com{link['href']}" if link else '#'
                        
                        articles.append({
                            'title': title,
                            'content': f'Reddit post about {title[:50]}...',
                            'source': 'reddit',
                            'url': url,
                            'published_date': datetime.now()
                        })
                except:
                    continue
    except Exception as e:
        print(f"Error parsing Reddit: {e}")
    
    return articles

def parse_habr():
    """Парсинг Habr"""
    articles = []
    
    try:
        url = settings.NEWS_SOURCES['habr']
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for article in soup.find_all('article', class_='tm-articles-list__item')[:5]:
                try:
                    title_elem = article.find('h2', class_='tm-title')
                    if title_elem:
                        title = title_elem.text.strip()
                        link = title_elem.find('a')
                        url = f"https://habr.com{link['href']}" if link else '#'
                        
                        content_elem = article.find('div', class_='article-formatted-body')
                        content = content_elem.text.strip()[:300] if content_elem else ''
                        
                        articles.append({
                            'title': title,
                            'content': content,
                            'source': 'habr',
                            'url': url,
                            'published_date': datetime.now()
                        })
                except:
                    continue
    except Exception as e:
        print(f"Error parsing Habr: {e}")
    
    return articles

def fetch_news_articles():
    """Основная функция сбора новостей"""
    all_articles = []
    
    # Парсим все источники
    all_articles.extend(parse_twitter())
    all_articles.extend(parse_reddit())
    all_articles.extend(parse_habr())
    
    # Сохраняем в базу
    for article_data in all_articles:
        try:
            # Проверяем, нет ли уже такой статьи
            if not NewsArticle.objects.filter(url=article_data['url']).exists():
                NewsArticle.objects.create(
                    title=article_data['title'],
                    content=article_data['content'],
                    source=article_data['source'],
                    url=article_data['url'],
                    published_date=article_data['published_date']
                )
        except Exception as e:
            print(f"Error saving article: {e}")
    
    return len(all_articles)