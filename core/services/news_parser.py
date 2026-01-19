"""
News parser service for Z96A project.
Parses news from various sources related to infocommunications.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import re

class NewsParser:
    """Parser for infocommunication news from various sources"""
    
    def __init__(self):
        self.sources = {
            'habr': {
                'name': 'Хабр',
                'url': 'https://habr.com/ru/rss/hub/infosecurity/?fl=ru',
                'type': 'rss'
            },
            'reddit_networking': {
                'name': 'Reddit Networking',
                'url': 'https://www.reddit.com/r/networking/.rss',
                'type': 'rss'
            },
            'reddit_blockchain': {
                'name': 'Reddit Blockchain',
                'url': 'https://www.reddit.com/r/blockchain/.rss',
                'type': 'rss'
            },
            'twitter_sui': {
                'name': 'Twitter SUI',
                'url': 'https://twitrss.me/twitter_user_to_rss/?user=SuiNetwork',
                'type': 'rss'
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_rss(self, url, source_name, max_items=10):
        """Parse RSS feed"""
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:max_items]:
                article = {
                    'title': entry.get('title', 'Без заголовка'),
                    'excerpt': entry.get('summary', entry.get('description', ''))[:200],
                    'content': entry.get('content', [{'value': ''}])[0]['value'] if entry.get('content') else entry.get('description', ''),
                    'source': source_name,
                    'source_url': entry.get('link', '#'),
                    'author': entry.get('author', 'Неизвестный автор'),
                    'published_date': self.parse_date(entry.get('published', entry.get('updated', ''))),
                    'category': self.detect_category(entry.get('title', '') + ' ' + entry.get('summary', '')),
                    'tags': self.extract_tags(entry.get('title', '') + ' ' + entry.get('summary', '')),
                    'is_featured': False
                }
                
                # Ограничиваем длину
                if len(article['excerpt']) > 500:
                    article['excerpt'] = article['excerpt'][:497] + '...'
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            print(f"Error parsing RSS {url}: {e}")
            return []
    
    def parse_date(self, date_string):
        """Parse various date formats"""
        try:
            if not date_string:
                return datetime.now()
            
            # Пробуем разные форматы
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # Если ни один формат не подошел
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def detect_category(self, text):
        """Detect article category based on keywords"""
        text_lower = text.lower()
        
        categories = {
            'infrastructure': ['сеть', 'кабель', 'роутер', 'коммутатор', 'маршрутизатор', 'infrastructure', 'network', 'router'],
            'blockchain': ['блокчейн', 'солана', 'sui', 'транзакция', 'blockchain', 'solana', 'transaction'],
            'satellite': ['спутник', 'starlink', 'орбита', 'satellite', 'космос', 'space'],
            'research': ['исследование', 'анализ', 'разработка', 'research', 'analysis', 'development'],
            'general': []
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return 'general'
    
    def extract_tags(self, text):
        """Extract hashtags from text"""
        hashtags = re.findall(r'#(\w+)', text)
        words = re.findall(r'\b[a-zA-Zа-яА-Я]{4,}\b', text.lower())
        
        # Берем наиболее частые слова как теги
        from collections import Counter
        word_counts = Counter(words)
        common_words = [word for word, count in word_counts.most_common(5) if count > 1]
        
        all_tags = hashtags + common_words[:3]
        return ','.join(all_tags[:5])
    
    def fetch_all_news(self, max_per_source=5):
        """Fetch news from all sources"""
        all_articles = []
        
        for source_key, source_info in self.sources.items():
            try:
                if source_info['type'] == 'rss':
                    articles = self.parse_rss(
                        source_info['url'], 
                        source_info['name'],
                        max_items=max_per_source
                    )
                    all_articles.extend(articles)
                    
            except Exception as e:
                print(f"Error fetching from {source_key}: {e}")
                continue
        
        # Сортируем по дате (новые сначала)
        all_articles.sort(key=lambda x: x['published_date'], reverse=True)
        
        # Отмечаем первые 3 как рекомендуемые
        for i, article in enumerate(all_articles[:3]):
            article['is_featured'] = True
        
        return all_articles[:20]  # Возвращаем не более 20 статей
    
    def get_test_news(self):
        """Return test news for development"""
        return [
            {
                'title': 'SUI Blockchain оффлайн-транзакции успешно протестированы',
                'excerpt': 'Команда SUI провела успешные испытания оффлайн-транзакций с использованием радиоволн и Bluetooth',
                'content': 'Технология оффлайн-транзакций SUI показала устойчивость в условиях отсутствия сетевого соединения. Это открывает новые возможности для инфокоммуникационных систем в удаленных регионах.',
                'source': 'SUI Network',
                'source_url': '#',
                'author': 'SUI Research Team',
                'published_date': datetime.now() - timedelta(days=1),
                'category': 'blockchain',
                'tags': 'sui,blockchain,offline,transactions',
                'is_featured': True
            },
            {
                'title': 'Starlink расширяет покрытие в удаленных регионах',
                'excerpt': 'SpaceX запустила новые спутники для расширения покрытия Starlink в труднодоступных регионах',
                'content': 'Компания SpaceX продолжает развертывание спутниковой группировки Starlink. Новые запуски позволят обеспечить связь в регионах с плохой инфраструктурой.',
                'source': 'SpaceX Updates',
                'source_url': '#',
                'author': 'Elon Musk',
                'published_date': datetime.now() - timedelta(days=2),
                'category': 'satellite',
                'tags': 'starlink,satellite,spacex,coverage',
                'is_featured': True
            },
            {
                'title': 'Новый подводный кабель соединит Европу и Африку',
                'excerpt': 'Запущен проект нового подводного кабеля 2Africa протяженностью 45,000 км',
                'content': 'Консорциум компаний анонсировал строительство кабеля 2Africa, который станет самым длинным подводным кабелем в мире, соединяющим Европу, Африку и Ближний Восток.',
                'source': 'Telecom News',
                'source_url': '#',
                'author': 'Industry Analyst',
                'published_date': datetime.now() - timedelta(days=3),
                'category': 'infrastructure',
                'tags': 'submarine,cable,africa,network',
                'is_featured': True
            }
        ]

# Создаем глобальный экземпляр парсера
news_parser = NewsParser()