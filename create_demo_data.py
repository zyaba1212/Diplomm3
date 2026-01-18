<<<<<<< HEAD
import os
import django
import json
from datetime import datetime, timedelta
=======
#!/usr/bin/env python
import os
import django
>>>>>>> be60a7bbbb5cbbfe7284d5ef21c08df24e6784bc

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'z96a.settings')
django.setup()

<<<<<<< HEAD
from core.models import *
from django.utils import timezone

def create_regions_countries_cities():
    """Создание иерархии: Регионы → Страны → Города"""
    print("Creating regions, countries, and cities...")
    
    # Северная Америка
    na_region, _ = Region.objects.get_or_create(
        code='NA',
        defaults={'name': 'Северная Америка', 'description': 'Североамериканский континент'}
    )
    
    usa, _ = Country.objects.get_or_create(
        code='USA',
        defaults={'name': 'США', 'capital': 'Вашингтон', 'region': na_region}
    )
    
    cities_usa = [
        {'name': 'Нью-Йорк', 'lat': 40.7128, 'lng': -74.0060, 'type': 'hub', 'pop': 8000000},
        {'name': 'Вашингтон', 'lat': 38.9072, 'lng': -77.0369, 'type': 'capital', 'pop': 700000},
        {'name': 'Лос-Анджелес', 'lat': 34.0522, 'lng': -118.2437, 'type': 'hub', 'pop': 4000000},
        {'name': 'Чикаго', 'lat': 41.8781, 'lng': -87.6298, 'type': 'major', 'pop': 2700000},
    ]
    
    for city_data in cities_usa:
        City.objects.get_or_create(
            name=city_data['name'],
            country=usa,
            defaults={
                'city_type': city_data['type'],
                'latitude': city_data['lat'],
                'longitude': city_data['lng'],
                'population': city_data['pop'],
                'is_hub': city_data['type'] in ['hub', 'capital']
            }
        )
    
    # Европа
    eu_region, _ = Region.objects.get_or_create(
        code='EU',
        defaults={'name': 'Европа', 'description': 'Европейский континент'}
    )
    
    uk, _ = Country.objects.get_or_create(
        code='GBR',
        defaults={'name': 'Великобритания', 'capital': 'Лондон', 'region': eu_region}
    )
    
    City.objects.get_or_create(
        name='Лондон',
        country=uk,
        defaults={'city_type': 'capital', 'latitude': 51.5074, 'longitude': -0.1278, 'population': 9000000, 'is_hub': True}
    )
    
    germany, _ = Country.objects.get_or_create(
        code='DEU',
        defaults={'name': 'Германия', 'capital': 'Берлин', 'region': eu_region}
    )
    
    City.objects.get_or_create(
        name='Франкфурт',
        country=germany,
        defaults={'city_type': 'hub', 'latitude': 50.1109, 'longitude': 8.6821, 'population': 750000, 'is_hub': True}
    )
    
    france, _ = Country.objects.get_or_create(
        code='FRA',
        defaults={'name': 'Франция', 'capital': 'Париж', 'region': eu_region}
    )
    
    City.objects.get_or_create(
        name='Париж',
        country=france,
        defaults={'city_type': 'capital', 'latitude': 48.8566, 'longitude': 2.3522, 'population': 2200000, 'is_hub': True}
    )
    
    # Азия
    asia_region, _ = Region.objects.get_or_create(
        code='ASIA',
        defaults={'name': 'Азия', 'description': 'Азиатский континент'}
    )
    
    japan, _ = Country.objects.get_or_create(
        code='JPN',
        defaults={'name': 'Япония', 'capital': 'Токио', 'region': asia_region}
    )
    
    City.objects.get_or_create(
        name='Токио',
        country=japan,
        defaults={'city_type': 'capital', 'latitude': 35.6895, 'longitude': 139.6917, 'population': 14000000, 'is_hub': True}
    )
    
    singapore, _ = Country.objects.get_or_create(
        code='SGP',
        defaults={'name': 'Сингапур', 'capital': 'Сингапур', 'region': asia_region}
    )
    
    City.objects.get_or_create(
        name='Сингапур',
        country=singapore,
        defaults={'city_type': 'hub', 'latitude': 1.3521, 'longitude': 103.8198, 'population': 5700000, 'is_hub': True}
    )
    
    russia, _ = Country.objects.get_or_create(
        code='RUS',
        defaults={'name': 'Россия', 'capital': 'Москва', 'region': asia_region}
    )
    
    cities_russia = [
        {'name': 'Москва', 'lat': 55.7558, 'lng': 37.6173, 'type': 'capital', 'pop': 12500000},
        {'name': 'Санкт-Петербург', 'lat': 59.9311, 'lng': 30.3609, 'type': 'major', 'pop': 5400000},
        {'name': 'Новосибирск', 'lat': 55.0084, 'lng': 82.9357, 'type': 'regional', 'pop': 1600000},
    ]
    
    for city_data in cities_russia:
        City.objects.get_or_create(
            name=city_data['name'],
            country=russia,
            defaults={
                'city_type': city_data['type'],
                'latitude': city_data['lat'],
                'longitude': city_data['lng'],
                'population': city_data['pop'],
                'is_hub': city_data['type'] == 'capital'
            }
        )
    
    print(f"Created {Region.objects.count()} regions")
    print(f"Created {Country.objects.count()} countries")
    print(f"Created {City.objects.count()} cities")

def create_cables():
    """Создание кабелей из JSON файла"""
    print("Creating cables from cables.json...")
    
    json_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'cables.json')
    
    if not os.path.exists(json_path):
        print(f"Warning: cables.json not found at {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for cable_data in data['cables']:
        cable, created = Cable.objects.get_or_create(
            cable_id=cable_data['id'],
            defaults={
                'name': cable_data['name'],
                'cable_type': cable_data['type'],
                'capacity': cable_data.get('capacity', ''),
                'length': cable_data.get('length', ''),
                'owners': cable_data.get('owners', []),
                'year': cable_data.get('year'),
                'color': cable_data.get('color', '#1e90ff'),
                'description': cable_data.get('description', ''),
                'is_active': True
            }
        )
        
        if created:
            for idx, point in enumerate(cable_data['route']):
                CableRoute.objects.create(
                    cable=cable,
                    order=idx,
                    latitude=point['lat'],
                    longitude=point['lng'],
                    location_name=point['name']
                )
    
    print(f"Created {Cable.objects.count()} cables")
    print(f"Created {CableRoute.objects.count()} cable route points")

def create_network_elements():
    """Создание демо элементов сети"""
    print("Creating network elements...")
    
    moscow = City.objects.filter(name='Москва').first()
    tokyo = City.objects.filter(name='Токио').first()
    nyc = City.objects.filter(name='Нью-Йорк').first()
    
    elements_data = [
        {
            'name': 'Starlink Satellite 001',
            'type': 'satellite',
            'network': 'proposed',
            'lat': 40.7128,
            'lng': -74.0060,
            'alt': 550,
            'description': 'Low Earth orbit satellite for global coverage',
            'specs': {'bandwidth': '1 Gbps', 'frequency': 'Ka-band'}
        },
        {
            'name': 'DE-CIX Frankfurt',
            'type': 'ix',
            'network': 'existing',
            'lat': 50.1109,
            'lng': 8.6821,
            'alt': 0,
            'description': 'Largest Internet Exchange in the world',
            'specs': {'peak_traffic': '12 Tbps', 'members': '1000+'}
        },
    ]
    
    if moscow:
        elements_data.append({
            'name': 'MSK-IX Москва',
            'type': 'ix',
            'network': 'existing',
            'lat': moscow.latitude,
            'lng': moscow.longitude,
            'alt': 0,
            'city': moscow,
            'description': 'Московская точка обмена трафиком',
            'specs': {'peak_traffic': '5 Tbps'}
        })
    
    for elem_data in elements_data:
        city = elem_data.pop('city', None)
        specs = elem_data.pop('specs', {})
        
        NetworkElement.objects.get_or_create(
            name=elem_data['name'],
            defaults={
                **elem_data,
                'city': city,
                'specifications': specs
            }
        )
    
    print(f"Created {NetworkElement.objects.count()} network elements")

def create_demo_user():
    """Создание демо пользователя"""
    print("Creating demo user...")
    
    from django.contrib.auth.models import User
    
    user, _ = User.objects.get_or_create(
        username='demo',
        defaults={'is_staff': True, 'is_superuser': True}
    )
    user.set_password('demo123')
    user.save()
    
    profile, _ = UserProfile.objects.get_or_create(
        wallet_address='DemoWallet123456789',
        defaults={'nickname': 'DemoUser', 'user': user}
    )
    
    print(f"Demo user created: username=demo, password=demo123")

def create_news():
    """Создание демо новостей"""
    print("Creating demo news...")
    
    news_data = [
        {
            'title': 'Новые технологии в инфокоммуникационных сетях',
            'content': 'Развитие сетей 6G и квантовой связи открывает новые возможности для обработки транзакций в условиях отсутствия соединения.',
            'source': 'habr',
            'url': 'https://habr.com/demo',
            'date': timezone.now() - timedelta(hours=2)
        },
        {
            'title': 'Starlink расширяет покрытие',
            'content': 'SpaceX запустил новую партию спутников для обеспечения интернетом удаленных регионов.',
            'source': 'twitter',
            'url': 'https://twitter.com/demo',
            'date': timezone.now() - timedelta(hours=5)
        },
    ]
    
    for news in news_data:
        NewsArticle.objects.get_or_create(
            title=news['title'],
            defaults={
                'content': news['content'],
                'source': news['source'],
                'url': news['url'],
                'published_date': news['date']
            }
        )
    
    print(f"Created {NewsArticle.objects.count()} news articles")

def main():
    """Запуск всех функций создания данных"""
    print("=" * 50)
    print("ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ ДЕМО-ДАННЫМИ")
    print("=" * 50)
    
    create_regions_countries_cities()
    create_cables()
    create_network_elements()
    create_demo_user()
    create_news()
    
    print("=" * 50)
    print("✅ БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
    print("=" * 50)
    print("\nВы можете войти в админку:")
    print("URL: http://127.0.0.1:8000/admin/")
    print("Username: demo")
    print("Password: demo123")

if __name__ == '__main__':
    main()
=======
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
>>>>>>> be60a7bbbb5cbbfe7284d5ef21c08df24e6784bc
