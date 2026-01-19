"""
Z96A Core Application
Initialization file with signal imports and app configuration.
"""

default_app_config = 'core.apps.CoreConfig'

# Import signals to ensure they're registered
try:
    import core.signals
except ImportError:
    # Signals module might not exist yet
    pass

# Import services for easy access
try:
    from core.services.blockchain_service import BlockchainService
    from core.services.cable_service import CableService
    from core.services.user_service import UserService
except ImportError:
    # Services might not be initialized yet
    pass

# Version information
__version__ = '3.0.0'
__author__ = 'Z96A Team'
__description__ = 'Submarine Cable Network Visualization with Blockchain'