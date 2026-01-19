"""
Парсер новостей из различных источников
Twitter/X, Reddit, Хабр, TechCrunch и другие
"""

import json
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time
import re
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import NewsArticle


class NewsParser:
    """Парсер новостей из разных источников"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def parse_habr(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Парсинг новостей с Хабра"""
        articles = []
        try:
            # RSS фид Хабра
            feed = feedparser.parse('https://habr.com/ru/rss/all/all/')
            
            for entry in feed.entries[:limit]:
                # Извлечение категорий
                categories = []
                if hasattr(entry, 'tags'):
                    categories = [tag.term for tag in entry.tags]
                
                # Определение основной категории
                category = self._categorize_article(entry.title, entry.summary, categories)
                
                articles.append({
                    'title': entry.title,
                    'content': entry.summary,
                    'excerpt': self._create_excerpt(entry.summary, 250),
                    'source': 'HABR',
                    'category': category,
                    'url': entry.link,
                    'author': entry.author if hasattr(entry, 'author') else 'Хабр',
                    'published_date': self._parse_date(entry.published),
                    'is_verified': True,  # Хабр проверенный источник
                })
                
        except Exception as e:
            print(f"Error parsing Habr: {e}")
        
        return articles
    
    def parse_reddit(self, subreddit: str = 'networking', limit: int = 15) -> List[Dict[str, Any]]:
        """Парсинг новостей с Reddit"""
        articles = []
        try:
            url = f'https://www.reddit.com/r/{subreddit}/hot/.json?limit={limit}'
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            for post in data['data']['children'][:limit]:
                post_data = post['data']
                
                # Пропускаем NSFW и удаленные посты
                if post_data.get('over_18') or post_data.get('removed_by_category'):
                    continue
                
                # Определение категории
                category = self._categorize_article(
                    post_data['title'],
                    post_data.get('selftext', ''),
                    post_data.get('flair', '')
                )
                
                articles.append({
                    'title': post_data['title'],
                    'content': post_data.get('selftext', '')[:2000],  # Ограничение длины
                    'excerpt': self._create_excerpt(post_data.get('selftext', ''), 200),
                    'source': 'REDDIT',
                    'category': category,
                    'url': f"https://reddit.com{post_data['permalink']}",
                    'author': post_data.get('author', 'Anonymous'),
                    'published_date': datetime.fromtimestamp(post_data['created_utc']),
                    'is_verified': False,
                })
                
        except Exception as e:
            print(f"Error parsing Reddit: {e}")
        
        return articles
    
    def parse_techcrunch(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Парсинг новостей с TechCrunch"""
        articles = []
        try:
            feed = feedparser.parse('https://techcrunch.com/feed/')
            
            for entry in feed.entries[:limit]:
                # Извлечение контента
                content = ''
                if hasattr(entry, 'content'):
                    for item in entry.content:
                        content += item.value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                
                # Очистка HTML тегов
                content = self._clean_html(content)
                
                # Определение категории
                category = 'TELECOM'  # TechCrunch часто пишет о телекоме
                if any(word in entry.title.lower() for word in ['blockchain', 'crypto', 'bitcoin']):
                    category = 'BLOCKCHAIN'
                elif any(word in entry.title.lower() for word in ['satellite', 'spacex', 'starlink']):
                    category = 'SATELLITE'
                elif any(word in entry.title.lower() for word in ['security', 'hack', 'cyber']):
                    category = 'CYBERSECURITY'
                
                articles.append({
                    'title': entry.title,
                    'content': content[:3000],  # Ограничение длины
                    'excerpt': self._create_excerpt(content, 250),
                    'source': 'TECH_CRUNCH',
                    'category': category,
                    'url': entry.link,
                    'author': entry.author if hasattr(entry, 'author') else 'TechCrunch',
                    'published_date': self._parse_date(entry.published),
                    'is_verified': True,
                })
                
        except Exception as e:
            print(f"Error parsing TechCrunch: {e}")
        
        return articles
    
    def parse_twitter_search(self, query: str = 'telecom OR blockchain OR satellite', limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск твитов по запросу (симуляция - Twitter API требует токен)"""
        articles = []
        try:
            # Заглушка - в реальности нужен Twitter API v2
            # Здесь возвращаем демо-данные
            demo_tweets = [
                {
                    'title': 'Новые спутники Starlink запущены успешно',
                    'content': 'SpaceX успешно запустила очередную партию спутников Starlink. Общее количество на орбите превысило 5000 аппаратов.',
                    'author': 'SpaceX Updates',
                    'url': 'https://twitter.com/SpaceX/status/demo',
                },
                {
                    'title': 'Белорусская академия связи развивает блокчейн-проекты',
                    'content': 'Студенты БГАС разрабатывают инновационные решения для телекоммуникаций с использованием блокчейн-технологий.',
                    'author': 'БГАС Официальный',
                    'url': 'https://twitter.com/BGAS/status/demo',
                },
                {
                    'title': 'Квантовая связь: прорыв в безопасности данных',
                    'content': 'Исследователи достигли нового рекорда в дальности квантовой связи. Технология обещает революцию в защите данных.',
                    'author': 'Tech Innovations',
                    'url': 'https://twitter.com/TechNews/status/demo',
                },
            ]
            
            for tweet in demo_tweets[:limit]:
                category = self._categorize_article(tweet['title'], tweet['content'], [])
                
                articles.append({
                    'title': tweet['title'],
                    'content': tweet['content'],
                    'excerpt': self._create_excerpt(tweet['content'], 150),
                    'source': 'TWITTER',
                    'category': category,
                    'url': tweet['url'],
                    'author': tweet['author'],
                    'published_date': timezone.now() - timedelta(hours=random.randint(1, 24)),
                    'is_verified': False,
                })
                
        except Exception as e:
            print(f"Error parsing Twitter: {e}")
        
        return articles
    
    def parse_all_sources(self) -> List[Dict[str, Any]]:
        """Парсинг всех источников"""
        all_articles = []
        
        # Парсим разные источники
        all_articles.extend(self.parse_habr(limit=10))
        all_articles.extend(self.parse_reddit(subreddit='networking', limit=8))
        all_articles.extend(self.parse_reddit(subreddit='blockchain', limit=7))
        all_articles.extend(self.parse_techcrunch(limit=10))
        all_articles.extend(self.parse_twitter_search(limit=5))
        
        # Сортировка по дате (новые сначала)
        all_articles.sort(key=lambda x: x['published_date'], reverse=True)
        
        return all_articles
    
    def save_articles_to_db(self, articles: List[Dict[str, Any]]) -> int:
        """Сохранение статей в базу данных"""
        saved_count = 0
        
        for article in articles:
            try:
                # Проверяем, не существует ли уже такая статья
                if NewsArticle.objects.filter(url=article['url']).exists():
                    continue
                
                # Создаем запись
                NewsArticle.objects.create(
                    title=article['title'],
                    content=article['content'],
                    excerpt=article['excerpt'],
                    source=article['source'],
                    category=article['category'],
                    url=article['url'],
                    author=article['author'],
                    published_date=article['published_date'],
                    is_verified=article['is_verified'],
                )
                
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving article '{article['title']}': {e}")
                continue
        
        return saved_count
    
    def run_parsing_job(self) -> Dict[str, Any]:
        """Запуск полного цикла парсинга"""
        start_time = time.time()
        
        print("Starting news parsing job...")
        
        # Парсим все источники
        articles = self.parse_all_sources()
        
        # Сохраняем в базу
        saved_count = self.save_articles_to_db(articles)
        
        elapsed_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'total_found': len(articles),
            'saved_count': saved_count,
            'elapsed_time': round(elapsed_time, 2),
            'timestamp': timezone.now().isoformat(),
        }
        
        print(f"Parsing job completed: {result}")
        return result
    
    # ==============================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ==============================================
    
    def _categorize_article(self, title: str, content: str, tags: Any) -> str:
        """Определение категории статьи на основе содержимого"""
        text = (title + ' ' + content).lower()
        
        # Ключевые слова для категорий
        telecom_keywords = [
            'телеком', 'telecom', 'связь', 'network', 'интернет', 'internet',
            '5g', '6g', 'wi-fi', 'wireless', 'оптика', 'fiber', 'кабель', 'cable',
            'роутер', 'router', 'коммутатор', 'switch', 'маршрутизатор',
            'телефон', 'phone', 'мобильн', 'mobile', 'сотовая',
        ]
        
        blockchain_keywords = [
            'блокчейн', 'blockchain', 'крипто', 'crypto', 'биткоин', 'bitcoin',
            'солана', 'solana', 'эфириум', 'ethereum', 'нфт', 'nft', 'децентрализ',
            'web3', 'смарт-контракт', 'smart contract', 'токен', 'token',
        ]
        
        satellite_keywords = [
            'спутник', 'satellite', 'старлинк', 'starlink', 'космос', 'space',
            'орбита', 'orbit', 'телескоп', 'telescope', 'навигация', 'gps',
            'глонасс', 'glonass', 'spacex', 'илон маск', 'elon musk',
        ]
        
        cybersecurity_keywords = [
            'кибербезопасность', 'cybersecurity', 'хакер', 'hacker', 'взлом',
            'защита', 'security', 'вирус', 'virus', 'малвар', 'malware',
            'фишинг', 'phishing', 'ddos', 'атака', 'attack', 'уязвимость',
        ]
        
        infrastructure_keywords = [
            'инфраструктура', 'infrastructure', 'сервер', 'server', 'дата-центр',
            'data center', 'облако', 'cloud', 'хранилище', 'storage', 'резерв',
            'backup', 'мониторинг', 'monitoring', 'отказоустойчив', 'redundancy',
        ]
        
        # Проверка категорий
        if any(keyword in text for keyword in telecom_keywords):
            return 'TELECOM'
        elif any(keyword in text for keyword in blockchain_keywords):
            return 'BLOCKCHAIN'
        elif any(keyword in text for keyword in satellite_keywords):
            return 'SATELLITE'
        elif any(keyword in text for keyword in cybersecurity_keywords):
            return 'CYBERSECURITY'
        elif any(keyword in text for keyword in infrastructure_keywords):
            return 'INFRASTRUCTURE'
        else:
            return 'GENERAL'
    
    def _create_excerpt(self, text: str, max_length: int = 200) -> str:
        """Создание краткого описания"""
        # Очистка от HTML тегов
        clean_text = self._clean_html(text)
        
        # Обрезка до максимальной длины
        if len(clean_text) <= max_length:
            return clean_text
        
        # Обрезка до последнего пробела
        excerpt = clean_text[:max_length]
        last_space = excerpt.rfind(' ')
        
        if last_space > max_length * 0.7:  # Если есть нормальное место для обрезки
            excerpt = excerpt[:last_space]
        
        return excerpt + '...'
    
    def _clean_html(self, html: str) -> str:
        """Очистка текста от HTML тегов"""
        if not html:
            return ''
        
        # Простая очистка регулярными выражениями
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из разных форматов"""
        try:
            # Попытка парсинга стандартных форматов
            for fmt in [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M',
            ]:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Если ничего не сработало, возвращаем текущую дату
            return timezone.now()
            
        except Exception:
            return timezone.now()


# Глобальный экземпляр парсера
news_parser = NewsParser()