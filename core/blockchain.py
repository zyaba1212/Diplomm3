"""
core/blockchain.py - Полный рефакторинг для работы с Sui блокчейном
Поддержка онлайн/офлайн режимов, подписи транзакций, верификации
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from django.conf import settings
from django.core.cache import cache

# Настройка логирования
logger = logging.getLogger(__name__)

class SuiBlockchainService:
    """Сервис для работы с блокчейном Sui"""
    
    def __init__(self):
        self.online_mode = True
        self.client = None
        self.pending_transactions = []
        self.init_client()
    
    def init_client(self):
        """Инициализация клиента Sui"""
        try:
            from sui.sui_client import SuiClient
            rpc_url = getattr(settings, 'SUI_RPC_URL', 'https://fullnode.testnet.sui.io:443')
            self.client = SuiClient(rpc_url)
            logger.info(f"Sui client initialized with RPC: {rpc_url}")
        except ImportError as e:
            logger.error(f"Sui SDK not installed: {e}")
            self.online_mode = False
        except Exception as e:
            logger.error(f"Failed to initialize Sui client: {e}")
            self.online_mode = False
    
    def create_transaction(self, 
                          sender: str,
                          recipient: str,
                          amount: float,
                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Создание транзакции для ставки
        
        Args:
            sender: Адрес отправителя
            recipient: Адрес получателя (контракт ипподрома)
            amount: Сумма ставки
            metadata: Дополнительные данные (ID забега, тип ставки и т.д.)
        
        Returns:
            Словарь с данными транзакции
        """
        try:
            transaction_data = {
                "version": "1.0",
                "timestamp": datetime.utcnow().isoformat(),
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "currency": "SUI",
                "metadata": metadata or {},
                "nonce": self._generate_nonce(sender),
                "chain_id": "sui-testnet"
            }
            
            # Создаем хеш для подписи
            transaction_data["hash"] = self._calculate_transaction_hash(transaction_data)
            
            if self.online_mode and self.client:
                # Онлайн режим: сразу создаем в блокчейне
                tx_result = self._create_online_transaction(transaction_data)
                transaction_data["tx_digest"] = tx_result.get("digest")
                transaction_data["status"] = "submitted"
            else:
                # Офлайн режим: готовим к подписи
                transaction_data["status"] = "pending_signature"
                self.pending_transactions.append(transaction_data)
            
            logger.info(f"Transaction created: {transaction_data['hash']}")
            return transaction_data
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    def sign_transaction_offline(self, 
                                transaction_hash: str,
                                private_key: str) -> Dict[str, Any]:
        """
        Подпись транзакции в офлайн режиме
        
        Args:
            transaction_hash: Хеш транзакции
            private_key: Приватный ключ для подписи (в реальном приложении НЕ передавать так!)
        
        Returns:
            Подписанная транзакция
        """
        try:
            # Ищем транзакцию в ожидающих
            tx = next((t for t in self.pending_transactions 
                      if t.get("hash") == transaction_hash), None)
            
            if not tx:
                raise ValueError(f"Transaction {transaction_hash} not found")
            
            # В реальном приложении здесь была бы криптографическая подпись
            # Это упрощенный пример
            signature = self._simulate_signature(transaction_hash, private_key)
            
            signed_tx = {
                **tx,
                "signature": signature,
                "signed_at": datetime.utcnow().isoformat(),
                "public_key": self._derive_public_key(private_key),
                "status": "signed"
            }
            
            # Сохраняем в кеше для последующей отправки
            cache_key = f"signed_tx_{transaction_hash}"
            cache.set(cache_key, signed_tx, timeout=3600)
            
            logger.info(f"Transaction {transaction_hash} signed offline")
            return signed_tx
            
        except Exception as e:
            logger.error(f"Error signing transaction: {e}")
            raise
    
    def submit_signed_transaction(self, signed_transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Отправка подписанной транзакции в сеть
        
        Args:
            signed_transaction: Подписанная транзакция
        
        Returns:
            Результат отправки
        """
        if not self.online_mode or not self.client:
            raise ConnectionError("Blockchain client not available")
        
        try:
            # В реальном приложении здесь был бы вызов RPC Sui
            # Это демо-реализация
            result = {
                "success": True,
                "tx_digest": hashlib.sha256(
                    json.dumps(signed_transaction, sort_keys=True).encode()
                ).hexdigest(),
                "timestamp": datetime.utcnow().isoformat(),
                "gas_used": 1000,
                "checkpoint": 123456
            }
            
            # Обновляем статус транзакции
            if signed_transaction.get("hash") in [t.get("hash") for t in self.pending_transactions]:
                self.pending_transactions = [
                    t for t in self.pending_transactions 
                    if t.get("hash") != signed_transaction.get("hash")
                ]
            
            logger.info(f"Transaction submitted: {result['tx_digest']}")
            return result
            
        except Exception as e:
            logger.error(f"Error submitting transaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_transaction(self, tx_digest: str) -> Dict[str, Any]:
        """
        Проверка статуса транзакции в блокчейне
        
        Args:
            tx_digest: Хеш транзакции
        
        Returns:
            Статус транзакции
        """
        try:
            if self.online_mode and self.client:
                # В реальном приложении: запрос к блокчейну
                status = {
                    "digest": tx_digest,
                    "status": "confirmed",
                    "timestamp": datetime.utcnow().isoformat(),
                    "confirmed_round": 123456,
                    "executed": True
                }
            else:
                # Офлайн проверка из кеша
                cache_key = f"tx_status_{tx_digest}"
                status = cache.get(cache_key, {
                    "digest": tx_digest,
                    "status": "pending",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Error verifying transaction: {e}")
            return {
                "digest": tx_digest,
                "status": "error",
                "error": str(e)
            }
    
    # Вспомогательные методы
    def _generate_nonce(self, address: str) -> str:
        """Генерация nonce для транзакции"""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        return hashlib.sha256(f"{address}{timestamp}".encode()).hexdigest()[:16]
    
    def _calculate_transaction_hash(self, transaction_data: Dict[str, Any]) -> str:
        """Вычисление хеша транзакции"""
        data_str = json.dumps(transaction_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _simulate_signature(self, data_hash: str, private_key: str) -> str:
        """Симуляция криптографической подписи (для демо)"""
        # В реальном приложении: ed25519 или secp256k1 подпись
        simulated = f"sig_{data_hash[:16]}_{private_key[-8:]}"
        return hashlib.sha256(simulated.encode()).hexdigest()
    
    def _derive_public_key(self, private_key: str) -> str:
        """Получение публичного ключа из приватного (для демо)"""
        return hashlib.sha256(private_key.encode()).hexdigest()[:64]
    
    def _create_online_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создание транзакции через Sui SDK (демо)"""
        return {
            "digest": transaction_data["hash"],
            "raw_transaction": json.dumps(transaction_data),
            "estimated_gas": 1000
        }


# Глобальный экземпляр сервиса
blockchain_service = SuiBlockchainService()