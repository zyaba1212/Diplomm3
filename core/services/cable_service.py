"""
Cable service layer
Handles cable-related business logic
"""

import logging
from typing import List, Dict, Optional, Tuple
from django.db.models import Q, Count, Sum
from django.core.cache import cache

from ..models import Cable, LandingPoint, Equipment, Region
from ..utils.validators import validate_coordinates

logger = logging.getLogger(__name__)


class CableService:
    """Service for cable operations"""
    
    @staticmethod
    def get_cable_by_id(cable_id: str) -> Optional[Cable]:
        """Get cable by ID with caching"""
        cache_key = f"cable_{cable_id}"
        cable = cache.get(cache_key)
        
        if not cable:
            try:
                cable = Cable.objects.get(cable_id=cable_id)
                cache.set(cache_key, cable, timeout=300)  # 5 minutes
            except Cable.DoesNotExist:
                return None
        
        return cable
    
    @staticmethod
    def search_cables(query: str, filters: Dict = None) -> Tuple[List[Cable], int]:
        """
        Search cables with filters
        Returns: (cables, total_count)
        """
        try:
            cables = Cable.objects.all()
            
            # Apply search query
            if query:
                cables = cables.filter(
                    Q(name__icontains=query) |
                    Q(cable_id__icontains=query) |
                    Q(alternative_name__icontains=query) |
                    Q(owners__icontains=query) |
                    Q(suppliers__icontains=query)
                )
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    cables = cables.filter(status=filters['status'])
                
                if filters.get('region'):
                    cables = cables.filter(region__code=filters['region'])
                
                if filters.get('type'):
                    cables = cables.filter(cable_type=filters['type'])
                
                if filters.get('min_length'):
                    cables = cables.filter(length__gte=filters['min_length'])
                
                if filters.get('max_length'):
                    cables = cables.filter(length__lte=filters['max_length'])
                
                if filters.get('min_capacity'):
                    cables = cables.filter(capacity__gte=filters['min_capacity'])
            
            # Count before ordering
            total_count = cables.count()
            
            # Ordering
            order_by = filters.get('order_by', 'name')
            if order_by in ['name', 'length', 'capacity', 'created_at']:
                if filters.get('order_direction') == 'desc':
                    order_by = f'-{order_by}'
                cables = cables.order_by(order_by)
            
            return list(cables), total_count
            
        except Exception as e:
            logger.error(f"Error searching cables: {e}", exc_info=True)
            return [], 0
    
    @staticmethod
    def get_cable_statistics() -> Dict:
        """Get cable statistics"""
        cache_key = 'cable_statistics'
        stats = cache.get(cache_key)
        
        if not stats:
            try:
                # Aggregate statistics
                aggregates = Cable.objects.aggregate(
                    total_count=Count('id'),
                    total_length=Sum('length'),
                    total_capacity=Sum('capacity'),
                    avg_length=Sum('length') / Count('id'),
                    avg_capacity=Sum('capacity') / Count('id'),
                )
                
                # Status counts
                status_counts = dict(
                    Cable.objects.values_list('status').annotate(
                        count=Count('id')
                    )
                )
                
                # Region counts
                region_counts = dict(
                    Cable.objects.filter(region__isnull=False).values_list(
                        'region__name'
                    ).annotate(
                        count=Count('id')
                    )
                )
                
                # Type counts
                type_counts = dict(
                    Cable.objects.values_list('cable_type').annotate(
                        count=Count('id')
                    )
                )
                
                stats = {
                    'aggregates': aggregates,
                    'status_counts': status_counts,
                    'region_counts': region_counts,
                    'type_counts': type_counts,
                    'timestamp': timezone.now().isoformat(),
                }
                
                cache.set(cache_key, stats, timeout=300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error calculating cable statistics: {e}")
                stats = {}
        
        return stats
    
    @staticmethod
    def create_cable(cable_data: Dict) -> Tuple[bool, str, Optional[Cable]]:
        """
        Create new cable
        Returns: (success, message, cable)
        """
        try:
            # Validate required fields
            required_fields = ['cable_id', 'name', 'length', 'capacity']
            for field in required_fields:
                if field not in cable_data:
                    return False, f"Missing required field: {field}", None
            
            # Validate coordinates if provided
            if 'coordinates' in cable_data:
                if not validate_coordinates(cable_data['coordinates']):
                    return False, "Invalid coordinates format", None
            
            # Check if cable ID already exists
            if Cable.objects.filter(cable_id=cable_data['cable_id']).exists():
                return False, f"Cable with ID {cable_data['cable_id']} already exists", None
            
            # Create cable
            cable = Cable.objects.create(**cable_data)
            
            # Clear cache
            cache.delete('cable_statistics')
            cache.delete_pattern('cable_*')
            
            logger.info(f"Cable created: {cable.cable_id}")
            return True, "Cable created successfully", cable
            
        except Exception as e:
            logger.error(f"Error creating cable: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def update_cable(cable_id: str, update_data: Dict) -> Tuple[bool, str, Optional[Cable]]:
        """
        Update existing cable
        Returns: (success, message, cable)
        """
        try:
            cable = CableService.get_cable_by_id(cable_id)
            if not cable:
                return False, f"Cable {cable_id} not found", None
            
            # Validate coordinates if provided
            if 'coordinates' in update_data:
                if not validate_coordinates(update_data['coordinates']):
                    return False, "Invalid coordinates format", None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(cable, key):
                    setattr(cable, key, value)
            
            cable.save()
            
            # Clear cache
            cache.delete(f"cable_{cable_id}")
            cache.delete('cable_statistics')
            
            logger.info(f"Cable updated: {cable_id}")
            return True, "Cable updated successfully", cable
            
        except Exception as e:
            logger.error(f"Error updating cable {cable_id}: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def delete_cable(cable_id: str) -> Tuple[bool, str]:
        """
        Delete cable
        Returns: (success, message)
        """
        try:
            cable = CableService.get_cable_by_id(cable_id)
            if not cable:
                return False, f"Cable {cable_id} not found"
            
            cable.delete()
            
            # Clear cache
            cache.delete(f"cable_{cable_id}")
            cache.delete('cable_statistics')
            
            logger.info(f"Cable deleted: {cable_id}")
            return True, "Cable deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting cable {cable_id}: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_cables_by_region(region_code: str) -> List[Cable]:
        """Get all cables in a region"""
        try:
            cables = Cable.objects.filter(
                region__code=region_code
            ).order_by('name')
            
            return list(cables)
            
        except Exception as e:
            logger.error(f"Error getting cables for region {region_code}: {e}")
            return []
    
    @staticmethod
    def get_featured_cables(limit: int = 10) -> List[Cable]:
        """Get featured cables"""
        cache_key = f"featured_cables_{limit}"
        cables = cache.get(cache_key)
        
        if not cables:
            try:
                cables = list(
                    Cable.objects.filter(
                        is_featured=True,
                        status='active'
                    ).order_by('-created_at')[:limit]
                )
                cache.set(cache_key, cables, timeout=600)  # 10 minutes
            except Exception as e:
                logger.error(f"Error getting featured cables: {e}")
                cables = []
        
        return cables
    
    @staticmethod
    def get_cable_connections(cable_id: str) -> Dict:
        """Get cable connections (landing points, equipment)"""
        try:
            cable = CableService.get_cable_by_id(cable_id)
            if not cable:
                return {}
            
            landing_points = list(cable.landing_points.all())
            equipment = list(cable.equipment.filter(is_active=True))
            
            return {
                'cable': cable,
                'landing_points': landing_points,
                'equipment': equipment,
                'landing_points_count': len(landing_points),
                'equipment_count': len(equipment),
            }
            
        except Exception as e:
            logger.error(f"Error getting connections for cable {cable_id}: {e}")
            return {}
    
    @staticmethod
    def export_cables(format: str = 'json') -> Tuple[bool, str, Optional[str]]:
        """
        Export cables data
        Returns: (success, message, data_or_filename)
        """
        try:
            cables = Cable.objects.all()
            
            if format == 'json':
                data = []
                for cable in cables:
                    cable_data = {
                        'cable_id': cable.cable_id,
                        'name': cable.name,
                        'length': cable.length,
                        'capacity': cable.capacity,
                        'status': cable.status,
                        'type': cable.cable_type,
                        'coordinates': cable.coordinates,
                        'owners': cable.get_owners_list(),
                        'suppliers': cable.get_suppliers_list(),
                        'region': cable.region.name if cable.region else None,
                        'created_at': cable.created_at.isoformat(),
                    }
                    data.append(cable_data)
                
                import json
                return True, "Export successful", json.dumps(data, indent=2)
            
            elif format == 'csv':
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    'ID', 'Name', 'Length (km)', 'Capacity (Tbps)',
                    'Status', 'Type', 'Owners', 'Region', 'Created'
                ])
                
                # Write data
                for cable in cables:
                    writer.writerow([
                        cable.cable_id,
                        cable.name,
                        cable.length,
                        cable.capacity,
                        cable.status,
                        cable.cable_type,
                        ';'.join(cable.get_owners_list()),
                        cable.region.name if cable.region else '',
                        cable.created_at.strftime('%Y-%m-%d'),
                    ])
                
                return True, "Export successful", output.getvalue()
            
            else:
                return False, f"Unsupported format: {format}", None
                
        except Exception as e:
            logger.error(f"Error exporting cables: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None