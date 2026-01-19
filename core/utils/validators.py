"""
Validation utilities for Z96A Network
"""

import re
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validate_request_data(data: Dict, required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate request data contains required fields
    Returns: {
        'valid': bool,
        'message': str,
        'missing': List[str],
        'invalid': Dict[str, str]
    }
    """
    try:
        missing = []
        invalid = {}
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                missing.append(field)
            elif data[field] is None or data[field] == '':
                missing.append(field)
        
        # Validate field types and formats
        for field, value in data.items():
            if value is None:
                continue
                
            if field.endswith('_email') and value:
                if not validate_email(value):
                    invalid[field] = "Invalid email format"
            
            elif field.endswith('_url') and value:
                if not re.match(r'^https?://', str(value)):
                    invalid[field] = "Invalid URL format"
            
            elif field.endswith('_date') and value:
                try:
                    datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                except ValueError:
                    invalid[field] = "Invalid date format (use ISO 8601)"
            
            elif field == 'amount' and value:
                try:
                    amount = float(value)
                    if amount <= 0:
                        invalid[field] = "Amount must be positive"
                except (ValueError, TypeError):
                    invalid[field] = "Invalid amount"
            
            elif field == 'coordinates' and value:
                if not validate_coordinates(value):
                    invalid[field] = "Invalid coordinates format"
        
        valid = len(missing) == 0 and len(invalid) == 0
        
        if not valid:
            message_parts = []
            if missing:
                message_parts.append(f"Missing fields: {', '.join(missing)}")
            if invalid:
                invalid_msgs = [f"{k}: {v}" for k, v in invalid.items()]
                message_parts.append(f"Invalid fields: {', '.join(invalid_msgs)}")
            message = '; '.join(message_parts)
        else:
            message = "Validation successful"
        
        return {
            'valid': valid,
            'message': message,
            'missing': missing,
            'invalid': invalid,
        }
        
    except Exception as e:
        logger.error(f"Error validating request data: {e}")
        return {
            'valid': False,
            'message': f"Validation error: {str(e)}",
            'missing': [],
            'invalid': {},
        }


def validate_coordinates(coords: Any) -> bool:
    """
    Validate coordinates format (GeoJSON LineString)
    Expected format: [[lng, lat], [lng, lat], ...]
    """
    try:
        if not isinstance(coords, (list, tuple)):
            return False
        
        # Check if it's a list of coordinate pairs
        for point in coords:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                return False
            
            lng, lat = point
            if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
                return False
            
            # Validate longitude and latitude ranges
            if not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating coordinates: {e}")
        return False


def validate_email(email: str) -> bool:
    """Validate email address format"""
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    except Exception:
        return False


def validate_wallet_address(address: str) -> bool:
    """Validate wallet address format"""
    try:
        # Basic validation - adjust based on your blockchain implementation
        if not address or len(address) < 20 or len(address) > 64:
            return False
        
        # Check if it's hexadecimal (for most blockchain addresses)
        if re.match(r'^[0-9a-fA-F]+$', address):
            return True
        
        # Check if it's base58 (Bitcoin-style)
        if re.match(r'^[1-9A-HJ-NP-Za-km-z]+$', address):
            return True
        
        return False
        
    except Exception:
        return False


def validate_transaction_data(tx_data: Dict) -> Tuple[bool, str]:
    """
    Validate blockchain transaction data
    Returns: (is_valid, error_message)
    """
    try:
        required_fields = ['sender', 'recipient', 'amount']
        
        # Check required fields
        for field in required_fields:
            if field not in tx_data:
                return False, f"Missing required field: {field}"
        
        # Validate amounts
        try:
            amount = float(tx_data['amount'])
            if amount <= 0:
                return False, "Amount must be positive"
        except (ValueError, TypeError):
            return False, "Invalid amount"
        
        # Validate wallet addresses
        if tx_data['sender'] != 'system':  # System transactions don't need validation
            if not validate_wallet_address(tx_data['sender']):
                return False, "Invalid sender address"
        
        if not validate_wallet_address(tx_data['recipient']):
            return False, "Invalid recipient address"
        
        # Validate transaction type
        valid_types = ['transfer', 'reward', 'penalty', 'mining_reward', 'system', 'purchase', 'refund']
        if 'transaction_type' in tx_data and tx_data['transaction_type'] not in valid_types:
            return False, f"Invalid transaction type. Must be one of: {', '.join(valid_types)}"
        
        # Validate signature if present
        if 'signature' in tx_data and tx_data['signature']:
            if not isinstance(tx_data['signature'], str):
                return False, "Signature must be a string"
            
            # Check if it's base64 encoded
            import base64
            try:
                base64.b64decode(tx_data['signature'])
            except Exception:
                return False, "Invalid signature format (must be base64)"
        
        return True, "Transaction data is valid"
        
    except Exception as e:
        logger.error(f"Error validating transaction data: {e}")
        return False, f"Validation error: {str(e)}"


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    try:
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be at most 128 characters long"
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common patterns
        common_patterns = [
            '123456', 'password', 'qwerty', 'admin', 'welcome',
            '12345678', '123456789', '1234567890'
        ]
        
        for pattern in common_patterns:
            if pattern.lower() in password.lower():
                return False, "Password contains common pattern"
        
        return True, "Password is strong"
        
    except Exception as e:
        logger.error(f"Error validating password: {e}")
        return False, f"Validation error: {str(e)}"


def validate_json_schema(data: Any, schema: Dict) -> Tuple[bool, str]:
    """
    Validate data against JSON schema
    Returns: (is_valid, error_message)
    """
    try:
        # Simple JSON schema validation
        def validate(value, schema_part, path=""):
            if 'type' in schema_part:
                expected_type = schema_part['type']
                
                if expected_type == 'string':
                    if not isinstance(value, str):
                        return False, f"{path}: Expected string, got {type(value).__name__}"
                    
                    if 'minLength' in schema_part and len(value) < schema_part['minLength']:
                        return False, f"{path}: String too short (min {schema_part['minLength']})"
                    
                    if 'maxLength' in schema_part and len(value) > schema_part['maxLength']:
                        return False, f"{path}: String too long (max {schema_part['maxLength']})"
                    
                    if 'pattern' in schema_part and not re.match(schema_part['pattern'], value):
                        return False, f"{path}: String doesn't match pattern"
                
                elif expected_type == 'number':
                    if not isinstance(value, (int, float)):
                        return False, f"{path}: Expected number, got {type(value).__name__}"
                    
                    if 'minimum' in schema_part and value < schema_part['minimum']:
                        return False, f"{path}: Value too small (min {schema_part['minimum']})"
                    
                    if 'maximum' in schema_part and value > schema_part['maximum']:
                        return False, f"{path}: Value too large (max {schema_part['maximum']})"
                
                elif expected_type == 'integer':
                    if not isinstance(value, int):
                        return False, f"{path}: Expected integer, got {type(value).__name__}"
                    
                    if 'minimum' in schema_part and value < schema_part['minimum']:
                        return False, f"{path}: Value too small (min {schema_part['minimum']})"
                    
                    if 'maximum' in schema_part and value > schema_part['maximum']:
                        return False, f"{path}: Value too large (max {schema_part['maximum']})"
                
                elif expected_type == 'boolean':
                    if not isinstance(value, bool):
                        return False, f"{path}: Expected boolean, got {type(value).__name__}"
                
                elif expected_type == 'array':
                    if not isinstance(value, list):
                        return False, f"{path}: Expected array, got {type(value).__name__}"
                    
                    if 'minItems' in schema_part and len(value) < schema_part['minItems']:
                        return False, f"{path}: Array too small (min {schema_part['minItems']} items)"
                    
                    if 'maxItems' in schema_part and len(value) > schema_part['maxItems']:
                        return False, f"{path}: Array too large (max {schema_part['maxItems']} items)"
                    
                    if 'items' in schema_part:
                        for i, item in enumerate(value):
                            is_valid, error = validate(item, schema_part['items'], f"{path}[{i}]")
                            if not is_valid:
                                return False, error
                
                elif expected_type == 'object':
                    if not isinstance(value, dict):
                        return False, f"{path}: Expected object, got {type(value).__name__}"
                    
                    if 'properties' in schema_part:
                        for prop_name, prop_schema in schema_part['properties'].items():
                            if prop_name in value:
                                is_valid, error = validate(value[prop_name], prop_schema, f"{path}.{prop_name}")
                                if not is_valid:
                                    return False, error
                            elif 'required' in schema_part and prop_name in schema_part.get('required', []):
                                return False, f"{path}: Missing required property '{prop_name}'"
                    
                    # Additional properties
                    if 'additionalProperties' in schema_part and schema_part['additionalProperties'] is False:
                        allowed_props = set(schema_part.get('properties', {}).keys())
                        actual_props = set(value.keys())
                        extra_props = actual_props - allowed_props
                        if extra_props:
                            return False, f"{path}: Additional properties not allowed: {', '.join(extra_props)}"
            
            # Enum validation
            if 'enum' in schema_part:
                if value not in schema_part['enum']:
                    return False, f"{path}: Value must be one of {schema_part['enum']}"
            
            return True, ""
        
        return validate(data, schema, "")
        
    except Exception as e:
        logger.error(f"Error validating JSON schema: {e}")
        return False, f"Schema validation error: {str(e)}"


def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent XSS and other attacks
    """
    try:
        if not input_string:
            return ""
        
        # Trim whitespace
        sanitized = input_string.strip()
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Replace HTML special characters
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
            "/": "&#x2F;"
        }
        
        for char, escape in html_escape_table.items():
            sanitized = sanitized.replace(char, escape)
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        return ""


def validate_cable_data(cable_data: Dict) -> Tuple[bool, str]:
    """
    Validate cable data
    Returns: (is_valid, error_message)
    """
    try:
        required_fields = ['cable_id', 'name', 'length', 'capacity']
        
        for field in required_fields:
            if field not in cable_data:
                return False, f"Missing required field: {field}"
        
        # Validate length
        try:
            length = float(cable_data['length'])
            if length <= 0:
                return False, "Length must be positive"
            if length > 50000:  # 50,000 km maximum
                return False, "Length too large (max 50,000 km)"
        except (ValueError, TypeError):
            return False, "Invalid length"
        
        # Validate capacity
        try:
            capacity = float(cable_data['capacity'])
            if capacity <= 0:
                return False, "Capacity must be positive"
            if capacity > 1000:  # 1000 Tbps maximum
                return False, "Capacity too large (max 1000 Tbps)"
        except (ValueError, TypeError):
            return False, "Invalid capacity"
        
        # Validate status
        valid_statuses = ['planned', 'under_construction', 'active', 'maintenance', 'decommissioned', 'damaged']
        if 'status' in cable_data and cable_data['status'] not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
        # Validate cable type
        valid_types = ['fiber', 'copper', 'hybrid', 'satellite']
        if 'cable_type' in cable_data and cable_data['cable_type'] not in valid_types:
            return False, f"Invalid cable type. Must be one of: {', '.join(valid_types)}"
        
        # Validate coordinates if provided
        if 'coordinates' in cable_data and cable_data['coordinates']:
            if not validate_coordinates(cable_data['coordinates']):
                return False, "Invalid coordinates format"
        
        return True, "Cable data is valid"
        
    except Exception as e:
        logger.error(f"Error validating cable data: {e}")
        return False, f"Validation error: {str(e)}"