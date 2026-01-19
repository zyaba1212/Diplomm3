"""
Blockchain service layer
Handles all blockchain-related business logic
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from django.utils import timezone
from django.core.cache import cache

from ..blockchain import (
    get_blockchain, Blockchain, BlockchainTransaction,
    create_reward_transaction, create_transfer_transaction
)
from ..models import BlockchainTransaction as DBTransaction

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for blockchain operations"""
    
    @staticmethod
    def get_blockchain() -> Blockchain:
        """Get blockchain instance (singleton)"""
        return get_blockchain()
    
    @staticmethod
    def add_transaction(transaction_data: Dict) -> Tuple[bool, str]:
        """
        Add transaction to blockchain
        Returns: (success, message)
        """
        try:
            blockchain = get_blockchain()
            
            # Create transaction object
            tx = BlockchainTransaction.from_dict(transaction_data)
            
            # Verify signature if present
            if tx.sender != 'system' and not tx.verify_signature():
                return False, "Invalid transaction signature"
            
            # Add to blockchain
            success, message = blockchain.add_transaction(tx)
            
            if success:
                # Save to database
                db_tx = DBTransaction.objects.create(
                    tx_id=tx.tx_id,
                    sender=tx.sender,
                    recipient=tx.recipient,
                    amount=tx.amount,
                    transaction_type=tx.transaction_type,
                    description=tx.description,
                    public_key=tx.public_key,
                    signature=tx.signature,
                    status='pending',
                    blockchain_timestamp=tx.timestamp,
                )
                
                logger.info(f"Transaction added: {tx.tx_id}")
                return True, message
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error adding transaction: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def mine_pending_transactions(miner_address: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Mine pending transactions
        Returns: (success, message, block_data)
        """
        try:
            blockchain = get_blockchain()
            block = blockchain.mine_pending_transactions(miner_address)
            
            if block:
                # Update database transactions
                for tx_data in block.transactions:
                    if tx_data.get('tx_id') == 'genesis':
                        continue
                    
                    DBTransaction.objects.filter(
                        tx_id=tx_data['tx_id']
                    ).update(
                        status='confirmed',
                        block_hash=block.hash,
                        block_index=block.index,
                        confirmation_time=timezone.now(),
                        tx_hash=tx_data.get('hash', '')
                    )
                
                # Cache block data
                cache_key = f"block_{block.index}"
                cache.set(cache_key, block.to_dict(), timeout=3600)
                
                logger.info(f"Block #{block.index} mined successfully")
                return True, f"Block #{block.index} mined", block.to_dict()
            else:
                return False, "Failed to mine block", None
                
        except Exception as e:
            logger.error(f"Error mining block: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    @staticmethod
    def get_balance(address: str) -> float:
        """Get balance for address"""
        try:
            blockchain = get_blockchain()
            return blockchain.get_balance(address)
        except Exception as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return 0.0
    
    @staticmethod
    def get_transactions(address: str, limit: int = 50) -> List[Dict]:
        """Get transactions for address"""
        try:
            blockchain = get_blockchain()
            return blockchain.get_transactions(address, limit)
        except Exception as e:
            logger.error(f"Error getting transactions for {address}: {e}")
            return []
    
    @staticmethod
    def validate_chain() -> Tuple[bool, str]:
        """Validate blockchain integrity"""
        try:
            blockchain = get_blockchain()
            return blockchain.is_chain_valid()
        except Exception as e:
            logger.error(f"Error validating chain: {e}")
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def get_chain_info() -> Dict[str, Any]:
        """Get blockchain information"""
        try:
            blockchain = get_blockchain()
            
            return {
                'length': len(blockchain.chain),
                'pending_transactions': len(blockchain.pending_transactions),
                'difficulty': blockchain.difficulty,
                'mining_reward': blockchain.mining_reward,
                'last_block': blockchain.get_last_block().index if blockchain.chain else None,
                'is_valid': blockchain.is_chain_valid()[0],
            }
            
        except Exception as e:
            logger.error(f"Error getting chain info: {e}")
            return {}
    
    @staticmethod
    def create_reward(user_address: str, amount: float, reason: str) -> Tuple[bool, str]:
        """
        Create reward transaction
        Returns: (success, message)
        """
        try:
            tx = create_reward_transaction(user_address, amount, reason)
            
            success, message = blockchain.add_transaction(tx)
            if success:
                # Save to database
                DBTransaction.objects.create(
                    tx_id=tx.tx_id,
                    sender=tx.sender,
                    recipient=tx.recipient,
                    amount=tx.amount,
                    transaction_type=tx.transaction_type,
                    description=tx.description,
                    status='pending',
                    blockchain_timestamp=tx.timestamp,
                )
                
                logger.info(f"Reward created: {tx.tx_id} for {user_address}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error creating reward: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def sync_with_database():
        """Sync blockchain with database transactions"""
        try:
            blockchain = get_blockchain()
            
            # Get pending transactions from database
            db_pending = DBTransaction.objects.filter(status='pending')
            
            for db_tx in db_pending:
                # Check if transaction already in blockchain
                tx_exists = any(
                    tx.tx_id == db_tx.tx_id 
                    for tx in blockchain.pending_transactions
                )
                
                if not tx_exists:
                    # Add to blockchain
                    tx_data = {
                        'tx_id': db_tx.tx_id,
                        'sender': db_tx.sender,
                        'recipient': db_tx.recipient,
                        'amount': float(db_tx.amount),
                        'transaction_type': db_tx.transaction_type,
                        'description': db_tx.description,
                        'public_key': db_tx.public_key,
                        'signature': db_tx.signature,
                        'timestamp': db_tx.blockchain_timestamp or db_tx.created_at.timestamp(),
                    }
                    
                    tx = BlockchainTransaction.from_dict(tx_data)
                    blockchain.pending_transactions.append(tx)
            
            logger.info(f"Synced {len(db_pending)} transactions with blockchain")
            return True, f"Synced {len(db_pending)} transactions"
            
        except Exception as e:
            logger.error(f"Error syncing with database: {e}")
            return False, f"Sync error: {str(e)}"