"""
Helper functions for Z96A Network
"""

import hashlib
import secrets
import string
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import base64
import logging

from django.core.paginator import Paginator, Page
from django.http import JsonResponse
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


# ==================== STRING & FORMATTING HELPERS ====================

def generate_wallet_address() -> str:
    """Generate unique wallet address"""
    timestamp = str(time.time()).encode()
    random_bytes = secrets.token_bytes(16)
    combined = timestamp + random_bytes
    
    # Double hash for security
    first_hash = hashlib.sha256(combined).hexdigest()
    second_hash = hashlib.sha256(first_hash.encode()).hexdigest()
    
    # Return first 32 characters (64 hex chars)
    return second_hash[:32]


def generate_api_key(length: int = 32) -> str:
    """Generate secure API key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_random_string(length: int = 16) -> str:
    """Generate random string for various purposes"""
    return secrets.token_urlsafe(length)[:length]


def format_amount(amount: float, decimals: int = 8) -> str:
    """Format amount with specified decimal places"""
    try:
        if amount is None:
            return "0.0"
        
        # Use Decimal for precise formatting
        from decimal import Decimal, ROUND_DOWN
        dec_amount = Decimal(str(amount))
        
        # Round down to avoid floating point issues
        rounded = dec_amount.quantize(
            Decimal('1.' + '0' * decimals),
            rounding=ROUND_DOWN
        )
        
        # Format with thousands separators
        formatted = f"{rounded:,.{decimals}f}"
        
        # Remove unnecessary trailing zeros
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting amount {amount}: {e}")
        return str(amount)


def format_date(date_obj, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format date object to string"""
    try:
        if not date_obj:
            return ''
        
        if isinstance(date_obj, str):
            # Try to parse if it's a string
            from django.utils.dateparse import parse_datetime
            parsed = parse_datetime(date_obj)
            if parsed:
                return parsed.strftime(format_str)
            return date_obj
        
        return date_obj.strftime(format_str)
        
    except Exception as e:
        logger.error(f"Error formatting date {date_obj}: {e}")
        return str(date_obj)


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string"""
    try:
        if seconds < 60:
            return f"{seconds:.1f}s"
        
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        
        hours = minutes / 60
        if hours < 24:
            return f"{hours:.1f}h"
        
        days = hours / 24
        return f"{days:.1f}d"
        
    except Exception:
        return f"{seconds}s"


def truncate_string(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate string to maximum length"""
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


# ==================== CRYPTOGRAPHY HELPERS ====================

def encrypt_data(data: str, key: str = None) -> str:
    """
    Encrypt data using AES (simplified - use proper key management in production)
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        import os
        
        # Generate key if not provided
        if not key:
            key = os.urandom(32)  # 256-bit key
        
        # Generate IV
        iv = os.urandom(16)
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Encrypt data
        padded_data = pad(data.encode(), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        # Combine IV and encrypted data
        combined = iv + encrypted
        
        # Return base64 encoded
        return base64.b64encode(combined).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error encrypting data: {e}")
        raise


def decrypt_data(encrypted_data: str, key: str) -> str:
    """
    Decrypt data using AES
    """
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        
        # Decode base64
        combined = base64.b64decode(encrypted_data)
        
        # Extract IV and encrypted data
        iv = combined[:16]
        encrypted = combined[16:]
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Decrypt data
        decrypted_padded = cipher.decrypt(encrypted)
        decrypted = unpad(decrypted_padded, AES.block_size)
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error decrypting data: {e}")
        raise


def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash password with salt using PBKDF2
    Returns: (hashed_password, salt)
    """
    try:
        import hashlib
        import binascii
        import os
        
        # Generate salt if not provided
        if not salt:
            salt = secrets.token_bytes(16)
        else:
            salt = base64.b64decode(salt)
        
        # Use PBKDF2 with SHA256
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # Number of iterations
        )
        
        # Return base64 encoded
        return base64.b64encode(dk).decode('utf-8'), base64.b64encode(salt).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify password against hash"""
    try:
        new_hash, _ = hash_password(password, salt)
        return new_hash == hashed_password
    except Exception:
        return False


# ==================== GEOGRAPHICAL HELPERS ====================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    try:
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth radius in kilometers
        radius = 6371.0
        
        return radius * c
        
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return 0.0


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial bearing between two points
    Returns: bearing in degrees (0-360)
    """
    try:
        from math import radians, degrees, atan2, sin, cos
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        dlon = lon2_rad - lon1_rad
        
        x = sin(dlon) * cos(lat2_rad)
        y = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(dlon)
        
        bearing = atan2(x, y)
        bearing_deg = degrees(bearing)
        
        # Normalize to 0-360
        return (bearing_deg + 360) % 360
        
    except Exception as e:
        logger.error(f"Error calculating bearing: {e}")
        return 0.0


def midpoint(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """
    Calculate midpoint between two coordinates
    Returns: (lat, lon)
    """
    try:
        from math import radians, degrees, sin, cos, atan2, sqrt
        
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        bx = cos(lat2_rad) * cos(lon2_rad - lon1_rad)
        by = cos(lat2_rad) * sin(lon2_rad - lon1_rad)
        
        lat_mid = atan2(
            sin(lat1_rad) + sin(lat2_rad),
            sqrt((cos(lat1_rad) + bx)**2 + by**2)
        )
        lon_mid = lon1_rad + atan2(by, cos(lat1_rad) + bx)
        
        return degrees(lat_mid), degrees(lon_mid)
        
    except Exception as e:
        logger.error(f"Error calculating midpoint: {e}")
        return lat1, lon1


# ==================== DATA PROCESSING HELPERS ====================

def paginate_query(queryset: QuerySet, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Paginate Django queryset
    Returns: {
        'items': list,
        'total': int,
        'page': int,
        'per_page': int,
        'pages': int,
        'has_next': bool,
        'has_prev': bool,
    }
    """
    try:
        paginator = Paginator(queryset, per_page)
        
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        return {
            'items': list(page_obj.object_list),
            'total': paginator.count,
            'page': page_obj.number,
            'per_page': per_page,
            'pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_prev': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'prev_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
        
    except Exception as e:
        logger.error(f"Error paginating query: {e}")
        return {
            'items': [],
            'total': 0,
            'page': 1,
            'per_page': per_page,
            'pages': 0,
            'has_next': False,
            'has_prev': False,
        }


def api_response(success: bool = True, data: Any = None, 
                message: str = '', status_code: int = 200,
                **kwargs) -> JsonResponse:
    """
    Standard API response format
    """
    response_data = {
        'success': success,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat(),
    }
    
    # Add any additional kwargs
    response_data.update(kwargs)
    
    return JsonResponse(response_data, status=status_code)


def parse_json_safe(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def to_json_safe(data: Any, default: str = '{}') -> str:
    """Safely convert data to JSON string"""
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return default


def deep_update_dict(target: Dict, source: Dict) -> Dict:
    """
    Recursively update dictionary
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update_dict(target[key], value)
        else:
            target[key] = value
    return target


def filter_dict(data: Dict, keys: List[str]) -> Dict:
    """Filter dictionary to only include specified keys"""
    return {k: v for k, v in data.items() if k in keys}


def exclude_dict(data: Dict, keys: List[str]) -> Dict:
    """Filter dictionary to exclude specified keys"""
    return {k: v for k, v in data.items() if k not in keys}


# ==================== VALIDATION HELPERS ====================

def is_valid_email(email: str) -> bool:
    """Check if email is valid"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) if email else False


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    import re
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    return bool(re.match(pattern, url)) if url else False


def is_valid_ip(ip: str) -> bool:
    """Check if IP address is valid"""
    import socket
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_valid_date(date_string: str, format_str: str = '%Y-%m-%d') -> bool:
    """Check if date string is valid"""
    try:
        datetime.strptime(date_string, format_str)
        return True
    except ValueError:
        return False


# ==================== PERFORMANCE HELPERS ====================

def timeit(func):
    """Decorator to measure function execution time"""
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.debug(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    
    return wrapper


def cache_result(ttl: int = 300):
    """
    Decorator to cache function results
    TTL: Time to live in seconds
    """
    from django.core.cache import cache
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, 
         exceptions: tuple = (Exception,)):
    """
    Decorator to retry function on exception
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}")
                    
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)  # Exponential backoff
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    
    return decorator


# ==================== FILE HELPERS ====================

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    if '.' in filename:
        return filename.split('.')[-1].lower()
    return ''


def is_allowed_file(filename: str, allowed_extensions: List[str]) -> bool:
    """Check if file extension is allowed"""
    extension = get_file_extension(filename)
    return extension in allowed_extensions


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable size"""
    if size_bytes == 0:
        return "0B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1
    
    return f"{size_bytes:.2f} {units[unit_index]}"


# ==================== COLOR HELPERS ====================

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB to hex color"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def interpolate_color(color1: str, color2: str, factor: float = 0.5) -> str:
    """
    Interpolate between two colors
    factor: 0 = color1, 1 = color2
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return rgb_to_hex((r, g, b))


def get_status_color(status: str) -> str:
    """Get color for status"""
    colors = {
        'active': '#4CAF50',  # Green
        'pending': '#FFC107',  # Amber
        'inactive': '#9E9E9E',  # Gray
        'error': '#F44336',  # Red
        'warning': '#FF9800',  # Orange
        'success': '#4CAF50',  # Green
        'info': '#2196F3',  # Blue
    }
    return colors.get(status.lower(), '#9E9E9E')


# ==================== LOGGING HELPERS ====================

def setup_logger(name: str, log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger  # Already configured
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ==================== TESTING HELPERS ====================

def generate_test_data(model_name: str, count: int = 10) -> List[Dict]:
    """Generate test data for models"""
    import random
    from faker import Faker
    
    fake = Faker()
    data = []
    
    if model_name == 'cable':
        for i in range(count):
            data.append({
                'cable_id': f'TEST{i:03d}',
                'name': f'Test Cable {i+1}',
                'length': random.uniform(100, 10000),
                'capacity': random.uniform(1, 100),
                'status': random.choice(['active', 'planned', 'under_construction']),
                'cable_type': 'fiber',
                'coordinates': [[random.uniform(-180, 180), random.uniform(-90, 90)] 
                              for _ in range(random.randint(2, 5))],
            })
    
    elif model_name == 'user':
        for i in range(count):
            data.append({
                'username': fake.user_name(),
                'email': fake.email(),
                'password': 'testpassword123',
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
            })
    
    return data


# ==================== MISC HELPERS ====================

def get_current_timestamp() -> int:
    """Get current timestamp in milliseconds"""
    return int(time.time() * 1000)


def generate_unique_id(prefix: str = '') -> str:
    """Generate unique ID with optional prefix"""
    timestamp = int(time.time() * 1000)
    random_part = secrets.randbelow(10000)
    return f"{prefix}{timestamp}{random_part:04d}"


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List) -> List:
    """Flatten nested list"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with zero check"""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value between min and max"""
    return max(min_value, min(value, max_value))


# ==================== CONTEXT PROCESSORS ====================

def get_app_version() -> str:
    """Get application version"""
    try:
        from core import __version__
        return __version__
    except ImportError:
        return '1.0.0'


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    import platform
    import sys
    
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'processor': platform.processor(),
        'system': platform.system(),
        'release': platform.release(),
    }


# Export commonly used functions
__all__ = [
    'generate_wallet_address',
    'format_amount',
    'format_date',
    'calculate_distance',
    'paginate_query',
    'api_response',
    'timeit',
    'cache_result',
    'retry',
    'hex_to_rgb',
    'rgb_to_hex',
    'get_status_color',
    'setup_logger',
    'generate_test_data',
    'get_current_timestamp',
    'generate_unique_id',
    'safe_divide',
    'clamp',
    'get_app_version',
    'get_system_info',
]