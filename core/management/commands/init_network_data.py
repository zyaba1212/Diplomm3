from django.core.management.base import BaseCommand
from core.models import NetworkNode, Equipment, NetworkConnection, CablePath
import json
from pathlib import Path

class Command(BaseCommand):
    help = 'Initialize network data with real-world infrastructure'

    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing network data...')
        
        # Load data from JSON file if exists
        data_file = Path(__file__).parent.parent.parent / 'data' / 'network_data.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create network nodes
            for node_data in data.get('nodes', []):
                NetworkNode.objects.update_or_create(
                    name=node_data['name'],
                    defaults={
                        'node_type': node_data['type'],
                        'latitude': node_data['latitude'],
                        'longitude': node_data['longitude'],
                        'country': node_data['country'],
                        'city': node_data['city'],
                        'description': node_data['description'],
                        'capacity_gbps': node_data.get('capacity_gbps', 100),
                        'network_type': node_data.get('network_type', 'existing'),
                    }
                )
            
            # Create equipment
            for eq_data in data.get('equipment', []):
                Equipment.objects.update_or_create(
                    manufacturer=eq_data['manufacturer'],
                    model=eq_data['model'],
                    defaults={
                        'name': eq_data['name'],
                        'equipment_type': eq_data['type'],
                        'description': eq_data['description'],
                        'specifications': eq_data.get('specifications', {}),
                        'throughput_gbps': eq_data.get('throughput_gbps', 0),
                        'power_consumption_w': eq_data.get('power_consumption_w', 0),
                    }
                )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(data.get("nodes", []))} nodes and {len(data.get("equipment", []))} equipment'))
        else:
            # Create sample data
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample network data"""
        # Major internet exchange points
        ix_points = [
            {
                'name': 'DE-CIX Frankfurt',
                'type': 'ix',
                'latitude': 50.1109,
                'longitude': 8.6821,
                'country': 'Germany',
                'city': 'Frankfurt',
                'description': 'World\'s largest internet exchange point by peak traffic',
                'capacity_gbps': 10000,
            },
            {
                'name': 'AMS-IX Amsterdam',
                'type': 'ix',
                'latitude': 52.3702,
                'longitude': 4.8952,
                'country': 'Netherlands',
                'city': 'Amsterdam',
                'description': 'One of the largest European internet exchanges',
                'capacity_gbps': 8000,
            },
            {
                'name': 'MSK-IX Moscow',
                'type': 'ix',
                'latitude': 55.7558,
                'longitude': 37.6173,
                'country': 'Russia',
                'city': 'Moscow',
                'description': 'Major internet exchange in Russia',
                'capacity_gbps': 5000,
            },
        ]
        
        for ix in ix_points:
            NetworkNode.objects.get_or_create(
                name=ix['name'],
                defaults=ix
            )
        
        self.stdout.write(self.style.SUCCESS('Created sample network data'))