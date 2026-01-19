"""
Solana client for Z96A project.
Handles wallet connections and blockchain interactions.
"""

import json
import base58
import requests
from django.conf import settings

class SolanaClient:
    """Client for interacting with Solana blockchain"""
    
    def __init__(self, network='devnet'):
        self.network = network
        self.rpc_url = self.get_rpc_url()
        
        # API endpoints
        self.solscan_url = 'https://api.solscan.io' if network == 'mainnet' else 'https://api-devnet.solscan.io'
    
    def get_rpc_url(self):
        """Get RPC URL based on network"""
        urls = {
            'mainnet': 'https://api.mainnet-beta.solana.com',
            'devnet': 'https://api.devnet.solana.com',
            'testnet': 'https://api.testnet.solana.com'
        }
        return urls.get(self.network, urls['devnet'])
    
    def validate_wallet_address(self, address):
        """Validate Solana wallet address"""
        try:
            # Проверяем длину и кодировку base58
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False
    
    def get_transaction_info(self, tx_signature):
        """Get transaction information from Solscan"""
        try:
            url = f"{self.solscan_url}/transaction?tx={tx_signature}"
            headers = {
                'User-Agent': 'Z96A Network/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching transaction: {e}")
            return None
    
    def get_wallet_balance(self, wallet_address):
        """Get wallet balance"""
        try:
            # В реальной реализации здесь будет RPC вызов
            # Для разработки возвращаем тестовое значение
            return 0.0
        except Exception:
            return 0.0
    
    def verify_transaction(self, tx_signature, expected_parameters=None):
        """Verify transaction signature and parameters"""
        try:
            tx_info = self.get_transaction_info(tx_signature)
            if not tx_info:
                return {'valid': False, 'error': 'Transaction not found'}
            
            # Здесь будет проверка параметров транзакции
            # Пока просто проверяем, что транзакция существует
            return {
                'valid': True,
                'signature': tx_signature,
                'timestamp': tx_info.get('blockTime'),
                'status': tx_info.get('status')
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def generate_test_transaction(self, wallet_address):
        """Generate test transaction signature for development"""
        # В реальном приложении здесь будет создание реальной транзакции
        # Для разработки генерируем тестовую подпись
        import hashlib
        import time
        
        hash_input = f"{wallet_address}_{time.time()}_{self.network}"
        tx_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:64]
        
        return {
            'signature': tx_hash,
            'status': 'confirmed',
            'timestamp': int(time.time()),
            'is_test': True
        }

# Создаем глобальный экземпляр клиента
solana_client = SolanaClient(network='devnet')