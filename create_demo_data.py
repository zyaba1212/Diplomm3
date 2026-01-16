#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'z96a.settings')
django.setup()

from core.models import NetworkElement, NewsArticle, UserProfile, Comment
from django.utils import timezone
import uuid

print("Creating demo data...")

# Create sample network elements
sample_elements = [
    {
        'name': 'Спутник Starlink-1',
        'element_type': 'satellite',
        'network_type': 'proposed',
        'latitude': 0.0,
        'longitude': 0.0,
        'altitude': 550,
        'description': 'Спутник спутниковой сети для глобального интернета'
    },
    {
        'name': 'Наземная станция Минск',
        'element_type': 'ground_station',
        'network_type': 'existing',
        'latitude': 53.9045,
        'longitude': 27.5615,
        'altitude': 160,
        'description': 'Наземная приемо-передающая станция в Минске'
    },
    {
        'name': 'Маршрутизатор Москва',
        'element_type': 'router',
        'network_type': 'existing',
        'latitude': 55.7558,
        'longitude': 37.6173,
        'altitude': 200,
        'description': 'Основной маршрутизатор московского узла'
    },
    {
        'name': 'Сервер Европа',
        'element_type': 'server',
        'network_type': 'existing',
        'latitude': 52.3676,
        'longitude': 4.9041,
        'altitude': 150,
        'description': 'Центральный сервер европейской сети'
    }
]

for elem_data in sample_elements:
    try:
        NetworkElement.objects.get_or_create(
            element_id=uuid.uuid4(),
            name=elem_data['name'],
            element_type=elem_data['element_type'],
            network_type=elem_data['network_type'],
            latitude=elem_data['latitude'],
            longitude=elem_data['longitude'],
            altitude=elem_data['altitude'],
            description=elem_data['description'],
            is_active=True
        )
        print(f"✓ Created: {elem_data['name']}")
    except Exception as e:
        print(f"✗ Error creating {elem_data['name']}: {e}")

# Create sample news articles
sample_news = [
    {
        'title': 'Спутниковая интернет Starlink расширяет покрытие в Африке',
        'content': 'Компания SpaceX объявила о расширении сети Starlink в африканских странах...',
        'source': 'twitter',
        'url': '#',
        'published_date': timezone.now()
    },
    {
        'title': 'SUI блокчейн разработал инновационную систему оффлайн-транзакций',
        'content': 'Команда разработчиков SUI представила новую архитектуру для работы в условиях отсутствия сетевого соединения...',
        'source': 'habr',
        'url': '#',
        'published_date': timezone.now()
    },
    {
        'title': 'Безопасность инфокоммуникационных сетей в 2026 году',
        'content': 'Новые вызовы и решения в области кибербезопасности телекоммуникационных систем...',
        'source': 'reddit',
        'url': '#',
        'published_date': timezone.now()
    }
]

for news_data in sample_news:
    try:
        NewsArticle.objects.get_or_create(
            title=news_data['title'],
            defaults={
                'content': news_data['content'],
                'source': news_data['source'],
                'url': news_data['url'],
                'published_date': news_data['published_date'],
                'is_active': True
            }
        )
        print(f"✓ Created news: {news_data['title'][:50]}...")
    except Exception as e:
        print(f"✗ Error creating news: {e}")

print("\n✓ Demo data created successfully!")
