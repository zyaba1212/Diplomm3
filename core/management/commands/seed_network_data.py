from django.core.management.base import BaseCommand
from core.models import NetworkNode, Equipment, NetworkConnection
import json

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными сети'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных сети...')
        
        # Очищаем старые данные
        NetworkNode.objects.all().delete()
        Equipment.objects.all().delete()
        NetworkConnection.objects.all().delete()
        
        # Создаём ключевые узлы сети
        nodes_data = [
            # Северная Америка
            {'name': 'Нью-Йорк', 'type': 'hub', 'lat': 40.7, 'lon': -74, 'country': 'USA', 'city': 'New York'},
            {'name': 'Ашберн', 'type': 'datacenter', 'lat': 39.0, 'lon': -77.5, 'country': 'USA', 'city': 'Ashburn'},
            {'name': 'Лос-Анджелес', 'type': 'hub', 'lat': 34.0, 'lon': -118, 'country': 'USA', 'city': 'Los Angeles'},
            {'name': 'Майами', 'type': 'gateway', 'lat': 25.8, 'lon': -80.2, 'country': 'USA', 'city': 'Miami'},
            
            # Европа
            {'name': 'Франкфурт', 'type': 'ix', 'lat': 50.1, 'lon': 8.7, 'country': 'Germany', 'city': 'Frankfurt'},
            {'name': 'Лондон', 'type': 'hub', 'lat': 51.5, 'lon': -0.1, 'country': 'UK', 'city': 'London'},
            {'name': 'Амстердам', 'type': 'ix', 'lat': 52.4, 'lon': 4.9, 'country': 'Netherlands', 'city': 'Amsterdam'},
            {'name': 'Париж', 'type': 'hub', 'lat': 48.9, 'lon': 2.4, 'country': 'France', 'city': 'Paris'},
            
            # Азия
            {'name': 'Сингапур', 'type': 'hub', 'lat': 1.3, 'lon': 103.8, 'country': 'Singapore', 'city': 'Singapore'},
            {'name': 'Гонконг', 'type': 'hub', 'lat': 22.3, 'lon': 114.2, 'country': 'China', 'city': 'Hong Kong'},
            {'name': 'Токио', 'type': 'hub', 'lat': 35.7, 'lon': 139.8, 'country': 'Japan', 'city': 'Tokyo'},
            {'name': 'Шанхай', 'type': 'gateway', 'lat': 31.2, 'lon': 121.5, 'country': 'China', 'city': 'Shanghai'},
            
            # Россия
            {'name': 'Москва', 'type': 'ix', 'lat': 55.8, 'lon': 37.6, 'country': 'Russia', 'city': 'Moscow'},
            {'name': 'Санкт-Петербург', 'type': 'pop', 'lat': 59.9, 'lon': 30.3, 'country': 'Russia', 'city': 'Saint Petersburg'},
            {'name': 'Владивосток', 'type': 'gateway', 'lat': 43.1, 'lon': 131.9, 'country': 'Russia', 'city': 'Vladivostok'},
            
            # Другие регионы
            {'name': 'Сидней', 'type': 'hub', 'lat': -33.9, 'lon': 151.2, 'country': 'Australia', 'city': 'Sydney'},
            {'name': 'Дубай', 'type': 'gateway', 'lat': 25.2, 'lon': 55.3, 'country': 'UAE', 'city': 'Dubai'},
            {'name': 'Мумбаи', 'type': 'hub', 'lat': 19.1, 'lon': 72.9, 'country': 'India', 'city': 'Mumbai'},
            {'name': 'Сан-Паулу', 'type': 'hub', 'lat': -23.6, 'lon': -46.6, 'country': 'Brazil', 'city': 'Sao Paulo'},
        ]
        
        nodes = {}
        for data in nodes_data:
            node = NetworkNode.objects.create(
                name=data['name'],
                node_type=data['type'],
                latitude=data['lat'],
                longitude=data['lon'],
                altitude=0,
                country=data['country'],
                city=data['city'],
                description=f'Ключевой узел сети в {data["city"]}, {data["country"]}',
                capacity_gbps=100 if data['type'] == 'hub' else 40
            )
            nodes[data['name']] = node
        
        # Создаём оборудование
        equipment_data = [
            {'name': 'Cisco Nexus 9000', 'type': 'switch', 'manufacturer': 'Cisco', 'model': 'N9K-C93180YC-EX'},
            {'name': 'Juniper MX Series', 'type': 'router', 'manufacturer': 'Juniper', 'model': 'MX204'},
            {'name': 'Huawei OptiX OSN', 'type': 'optical', 'manufacturer': 'Huawei', 'model': 'OSN 9800'},
            {'name': 'Arista 7050', 'type': 'switch', 'manufacturer': 'Arista', 'model': 'DCS-7050SX3'},
            {'name': 'Nokia 7750', 'type': 'router', 'manufacturer': 'Nokia', 'model': 'SR-7750'},
            {'name': 'Dell PowerEdge', 'type': 'server', 'manufacturer': 'Dell', 'model': 'R750'},
        ]
        
        equipment = {}
        for data in equipment_data:
            eq = Equipment.objects.create(
                name=data['name'],
                equipment_type=data['type'],
                manufacturer=data['manufacturer'],
                model=data['model'],
                specifications=f'Производитель: {data["manufacturer"]}, Модель: {data["model"]}'
            )
            equipment[data['name']] = eq
        
        # Создаём соединения (подводные кабели)
        connections_data = [
            {'name': 'MAREA', 'type': 'submarine', 'from': 'Нью-Йорк', 'to': 'Лондон', 'capacity': 200},
            {'name': 'Apollo', 'type': 'submarine', 'from': 'Нью-Йорк', 'to': 'Париж', 'capacity': 160},
            {'name': 'FASTER', 'type': 'submarine', 'from': 'Лос-Анджелес', 'to': 'Токио', 'capacity': 180},
            {'name': 'SEA-ME-WE 3', 'type': 'submarine', 'from': 'Сингапур', 'to': 'Франкфурт', 'capacity': 140},
            {'name': 'Asia Pacific Gateway', 'type': 'submarine', 'from': 'Сингапур', 'to': 'Гонконг', 'capacity': 120},
            {'name': '2Africa', 'type': 'submarine', 'from': 'Лондон', 'to': 'Дубай', 'capacity': 180},
            {'name': 'BRUSA', 'type': 'submarine', 'from': 'Майами', 'to': 'Сан-Паулу', 'capacity': 100},
            
            # Наземные соединения
            {'name': 'Транссиб', 'type': 'terrestrial', 'from': 'Москва', 'to': 'Владивосток', 'capacity': 80},
            {'name': 'EU Backbone', 'type': 'terrestrial', 'from': 'Лондон', 'to': 'Франкфурт', 'capacity': 200},
            {'name': 'US Cross-country', 'type': 'terrestrial', 'from': 'Нью-Йорк', 'to': 'Лос-Анджелес', 'capacity': 400},
        ]
        
        for data in connections_data:
            NetworkConnection.objects.create(
                name=data['name'],
                connection_type=data['type'],
                from_node=nodes[data['from']],
                to_node=nodes[data['to']],
                capacity_gbps=data['capacity'],
                length_km=1000,  # примерная длина
                geojson_path='[]',
                is_active=True
            )
        
        self.stdout.write(self.style.SUCCESS(
            f'Создано: {NetworkNode.objects.count()} узлов, '
            f'{Equipment.objects.count()} оборудования, '
            f'{NetworkConnection.objects.count()} соединений'
        ))
        self.stdout.write('Тестовые данные успешно созданы!')