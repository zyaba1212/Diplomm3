"""
User service layer
Handles user-related business logic and blockchain operations
"""

import logging
import hashlib
import secrets
from typing import Dict, Tuple, Optional, List
from django.contrib.auth.models import User
from django.utils import timezone
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

from ..models import UserProfile, BlockchainTransaction, Cable
from .blockchain_service import BlockchainService
from ..utils.helpers import generate_wallet_address

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations"""
    
    @staticmethod
    def create_user_profile(user: User) -> Tuple[bool, str, Optional[UserProfile]]:
        """
        Create user profile with wallet
        Returns: (success, message, profile)
        """
        try:
            # Check if profile already exists
            if hasattr(user, 'profile'):
                return True, "Profile already exists", user.profile
            
            # Generate wallet address
            wallet_address = generate_wallet_address()
            
            # Generate RSA key pair
            key = RSA.generate(2048)
            private_key = key.export_key()
            public_key = key.publickey().export_key()
            
            # Encrypt private key (in production, use proper key management)
            cipher = PKCS1_OAEP.new(key.publickey())
            encrypted_private_key = base64.b64encode(
                cipher.encrypt(private_key)
            ).decode('utf-8')
            
            # Create profile
            profile = UserProfile.objects.create(
                user=user,
                wallet_address=wallet_address,
                public_key=public_key.decode('utf-8'),
                private_key_encrypted=encrypted_private_key,
                balance=100.0,  # Initial balance
            )
            
            # Create initial reward transaction
            BlockchainService.create_reward(
                user_address=wallet_address,
                amount=100.0,
                reason="Welcome bonus"
            )
            
            logger.info(f"User profile created for {user.username}")
            return True, "Profile created successfully", profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def get_user_profile(user: User) -> Optional[UserProfile]:
        """Get user profile, create if doesn't exist"""
        try:
            if hasattr(user, 'profile'):
                return user.profile
            else:
                success, message, profile = UserService.create_user_profile(user)
                return profile if success else None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    @staticmethod
    def update_profile(user: User, update_data: Dict) -> Tuple[bool, str]:
        """
        Update user profile
        Returns: (success, message)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found"
            
            # Update allowed fields
            allowed_fields = ['bio', 'location', 'website', 'avatar',
                            'email_notifications', 'newsletter_subscription', 'theme']
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(profile, field):
                    setattr(profile, field, value)
            
            profile.save()
            
            logger.info(f"Profile updated for {user.username}")
            return True, "Profile updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def award_points(user: User, amount: float, reason: str) -> Tuple[bool, str]:
        """
        Award points (ZETA tokens) to user
        Returns: (success, message)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found"
            
            # Create reward transaction
            success, message = BlockchainService.create_reward(
                user_address=profile.wallet_address,
                amount=amount,
                reason=reason
            )
            
            if success:
                # Update profile statistics
                profile.total_earned += amount
                profile.balance += amount
                profile.save()
                
                logger.info(f"Awarded {amount} ZETA to {user.username} for: {reason}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def create_transfer(user: User, recipient: str, amount: float,
                       description: str = "") -> Tuple[bool, str]:
        """
        Create transfer transaction
        Returns: (success, message)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found"
            
            # Check balance
            balance = BlockchainService.get_balance(profile.wallet_address)
            if balance < amount:
                return False, "Insufficient balance"
            
            # Get recipient profile (if exists)
            try:
                recipient_profile = UserProfile.objects.get(wallet_address=recipient)
                recipient_user = recipient_profile.user.username
            except UserProfile.DoesNotExist:
                recipient_user = "External address"
            
            # Create transaction data
            tx_data = {
                'sender': profile.wallet_address,
                'recipient': recipient,
                'amount': amount,
                'transaction_type': 'transfer',
                'description': description or f"Transfer to {recipient_user}",
            }
            
            # Add to blockchain
            success, message = BlockchainService.add_transaction(tx_data)
            
            if success:
                # Update sender statistics
                profile.total_spent += amount
                profile.balance -= amount
                profile.transactions_count += 1
                profile.save()
                
                logger.info(f"Transfer created: {profile.wallet_address} -> {recipient}: {amount} ZETA")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error creating transfer: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def record_cable_view(user: User, cable: Cable) -> bool:
        """Record that user viewed a cable"""
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False
            
            # Add cable to viewed set if not already there
            if cable not in profile.cables_viewed.all():
                profile.cables_viewed.add(cable)
                
                # Award points for viewing new cable
                if profile.cables_viewed.count() % 10 == 0:
                    UserService.award_points(
                        user=user,
                        amount=5.0,
                        reason=f"Viewed {profile.cables_viewed.count()} cables"
                    )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error recording cable view: {e}")
            return False
    
    @staticmethod
    def toggle_cable_favorite(user: User, cable: Cable) -> Tuple[bool, str]:
        """
        Toggle cable favorite status
        Returns: (success, message)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found"
            
            if cable in profile.cables_favorited.all():
                profile.cables_favorited.remove(cable)
                message = "Cable removed from favorites"
                logger.info(f"{user.username} unfavorited cable {cable.cable_id}")
            else:
                profile.cables_favorited.add(cable)
                message = "Cable added to favorites"
                logger.info(f"{user.username} favorited cable {cable.cable_id}")
            
            return True, message
            
        except Exception as e:
            logger.error(f"Error toggling cable favorite: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_user_statistics(user: User) -> Dict:
        """Get user statistics"""
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return {}
            
            # Get blockchain balance
            blockchain_balance = BlockchainService.get_balance(profile.wallet_address)
            
            # Get transaction history
            transactions = BlockchainService.get_transactions(profile.wallet_address, limit=100)
            
            # Calculate activity
            today = timezone.now().date()
            recent_activity = len([
                tx for tx in transactions
                if timezone.datetime.fromtimestamp(tx['timestamp']).date() == today
            ])
            
            return {
                'profile': {
                    'username': user.username,
                    'wallet_address': profile.wallet_address,
                    'balance': float(profile.balance),
                    'blockchain_balance': blockchain_balance,
                    'total_earned': float(profile.total_earned),
                    'total_spent': float(profile.total_spent),
                    'transactions_count': profile.transactions_count,
                    'discussions_count': profile.discussions_count,
                    'cables_viewed': profile.cables_viewed.count(),
                    'cables_favorited': profile.cables_favorited.count(),
                    'is_verified': profile.is_verified,
                },
                'activity': {
                    'recent_transactions': len(transactions),
                    'today_activity': recent_activity,
                    'joined_date': user.date_joined.strftime('%Y-%m-%d'),
                },
                'transactions': transactions[:10],  # Last 10 transactions
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}
    
    @staticmethod
    def generate_verification_code(user: User) -> Tuple[bool, str, Optional[str]]:
        """
        Generate email verification code
        Returns: (success, message, code)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found", None
            
            # Generate 6-digit code
            code = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            # Set expiration (10 minutes)
            profile.verification_code = code
            profile.verification_expires = timezone.now() + timezone.timedelta(minutes=10)
            profile.save()
            
            logger.info(f"Verification code generated for {user.username}")
            return True, "Verification code generated", code
            
        except Exception as e:
            logger.error(f"Error generating verification code: {e}")
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def verify_email(user: User, code: str) -> Tuple[bool, str]:
        """
        Verify email with code
        Returns: (success, message)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found"
            
            # Check if already verified
            if profile.is_verified:
                return True, "Email already verified"
            
            # Check code and expiration
            if not profile.verification_code or not profile.verification_expires:
                return False, "No verification code found"
            
            if profile.verification_expires < timezone.now():
                return False, "Verification code expired"
            
            if profile.verification_code != code:
                return False, "Invalid verification code"
            
            # Verify email
            profile.is_verified = True
            profile.verification_code = ''
            profile.verification_expires = None
            profile.save()
            
            # Award points for verification
            UserService.award_points(
                user=user,
                amount=25.0,
                reason="Email verification"
            )
            
            logger.info(f"Email verified for {user.username}")
            return True, "Email verified successfully"
            
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_leaderboard(limit: int = 20) -> List[Dict]:
        """Get user leaderboard by balance"""
        try:
            profiles = UserProfile.objects.select_related('user').order_by('-balance')[:limit]
            
            leaderboard = []
            for i, profile in enumerate(profiles, 1):
                leaderboard.append({
                    'rank': i,
                    'username': profile.user.username,
                    'wallet_address': profile.wallet_address[:8] + '...',
                    'balance': float(profile.balance),
                    'transactions_count': profile.transactions_count,
                    'discussions_count': profile.discussions_count,
                    'is_verified': profile.is_verified,
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    @staticmethod
    def export_user_data(user: User) -> Tuple[bool, str, Optional[Dict]]:
        """
        Export all user data (GDPR compliance)
        Returns: (success, message, data)
        """
        try:
            profile = UserService.get_user_profile(user)
            if not profile:
                return False, "Profile not found", None
            
            # Get user data
            user_data = {
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                },
                'profile': {
                    'wallet_address': profile.wallet_address,
                    'balance': float(profile.balance),
                    'total_earned': float(profile.total_earned),
                    'total_spent': float(profile.total_spent),
                    'bio': profile.bio,
                    'location': profile.location,
                    'website': profile.website,
                    'created_at': profile.created_at.isoformat(),
                    'updated_at': profile.updated_at.isoformat(),
                },
                'activity': {
                    'cables_viewed': [
                        {
                            'id': cable.cable_id,
                            'name': cable.name,
                            'viewed_at': profile.created_at.isoformat(),  # Approximate
                        }
                        for cable in profile.cables_viewed.all()[:100]
                    ],
                    'cables_favorited': [
                        {
                            'id': cable.cable_id,
                            'name': cable.name,
                        }
                        for cable in profile.cables_favorited.all()
                    ],
                },
                'transactions': BlockchainService.get_transactions(profile.wallet_address, limit=1000),
            }
            
            logger.info(f"User data exported for {user.username}")
            return True, "Data exported successfully", user_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None