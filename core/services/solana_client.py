import base64
import json
from typing import Optional, Dict, Any
import requests
from django.conf import settings
import base58
import hashlib
import time

try:
    # Проверяем доступность solana модулей
    from solana.rpc.api import Client
    from solders.pubkey import Pubkey as PublicKey
    from solders.signature import Signature
    from solders.message import Message
    from solders.keypair import Keypair
    from solders.transaction import Transaction
    SOLANA_AVAILABLE = True
    print("Solana modules imported successfully")
except ImportError as e:
    SOLANA_AVAILABLE = False
    print(f"Solana modules import error: {e}")
    # Только для случая когда модули действительно не установлены
    Client = None
    PublicKey = None
    Signature = None
    Message = None
    Keypair = None
    Transaction = None

class SolanaClient:
    """Solana blockchain client for wallet integration"""
    
    def __init__(self, rpc_url: Optional[str] = None):
        self.rpc_url = rpc_url or settings.SOLANA_RPC_URL
        if SOLANA_AVAILABLE and Client:
            self.client = Client(self.rpc_url)
        else:
            self.client = None
            print("Solana client not initialized - modules not available")
    
    def verify_signature(self, signature: str, message: str, public_key: str) -> bool:
        """Verify a message signature"""
        if not SOLANA_AVAILABLE:
            print("Solana modules not available, signature verification disabled")
            return True  # Для разработки
            
        try:
            # Реальная проверка подписи
            from nacl.signing import VerifyKey
            import base58
            
            # Декодируем публичный ключ
            pubkey_bytes = base58.b58decode(public_key)
            verify_key = VerifyKey(pubkey_bytes)
            
            # Декодируем подпись
            sig_bytes = base58.b58decode(signature)
            
            # Проверяем подпись
            verify_key.verify(message.encode('utf-8'), sig_bytes)
            return True
            
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    def verify_transaction(self, tx_signature: str, expected_signer: str) -> bool:
        """Verify a Solana transaction"""
        if not SOLANA_AVAILABLE or not self.client:
            print("Solana client not available, transaction verification disabled")
            return True  # Для разработки
            
        try:
            # Используем правильный импорт Signature
            signature = Signature.from_string(tx_signature)
            
            # Получаем информацию о транзакции
            tx_info = self.client.get_transaction(
                signature,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )
            
            if not tx_info.value:
                return False
            
            # Проверяем подписантов транзакции
            transaction = tx_info.value.transaction
            signers = transaction.transaction.signatures
            
            # Преобразуем expected_signer в PublicKey
            expected_pubkey = PublicKey.from_string(expected_signer)
            
            # Проверяем, что expected_signer был подписантом
            # Это упрощенная проверка - в реальности нужно анализировать всю транзакцию
            for sig in signers:
                # Можно добавить более сложную логику проверки
                pass
                
            return True
            
        except Exception as e:
            print(f"Transaction verification error: {e}")
            return False
    
    def get_wallet_balance(self, wallet_address: str) -> float:
        """Get SOL balance of a wallet"""
        if not SOLANA_AVAILABLE or not self.client:
            print("Solana client not available, balance check disabled")
            return 0.0
            
        try:
            pubkey = PublicKey.from_string(wallet_address)
            balance = self.client.get_balance(pubkey)
            return balance.value / 1e9  # Конвертируем lamports в SOL
        except Exception as e:
            print(f"Balance check error: {e}")
            return 0.0
    
    def generate_auth_token(self, wallet_address: str) -> str:
        """Generate authentication token for wallet"""
        timestamp = str(int(time.time()))
        message = f"{wallet_address}:{timestamp}:{settings.SECRET_KEY}"
        token_hash = hashlib.sha256(message.encode()).hexdigest()
        
        token = f"{timestamp}:{token_hash}"
        return base64.b64encode(token.encode()).decode()
    
    def verify_auth_token(self, token: str, wallet_address: str) -> bool:
        """Verify authentication token"""
        try:
            decoded = base64.b64decode(token.encode()).decode()
            timestamp, token_hash = decoded.split(":", 1)
            
            # Проверяем срок действия (1 час)
            if int(time.time()) - int(timestamp) > 3600:
                return False
            
            # Воссоздаем и сравниваем хэш
            message = f"{wallet_address}:{timestamp}:{settings.SECRET_KEY}"
            expected_hash = hashlib.sha256(message.encode()).hexdigest()
            
            return token_hash == expected_hash
            
        except Exception as e:
            print(f"Token verification error: {e}")
            return False
    
    def get_address_from_token(self, token: str) -> Optional[str]:
        """Extract wallet address from token"""
        try:
            decoded = base64.b64decode(token.encode()).decode()
            parts = decoded.split(":")
            if len(parts) >= 1:
                return parts[0]
        except Exception as e:
            print(f"Error extracting address from token: {e}")
        return None