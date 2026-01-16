import json
from django.conf import settings
import requests

def verify_solana_transaction(tx_hash):
    """
    Верификация транзакции в блокчейне Solana
    В демо-режиме всегда возвращает True
    """
    if settings.DEBUG:
        return True  # Для демо-режима
    
    try:
        # Реальная интеграция с Solana RPC
        rpc_url = settings.SOLANA_RPC_URL
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [tx_hash, {"encoding": "json", "maxSupportedTransactionVersion": 0}]
        }
        
        response = requests.post(rpc_url, json=payload)
        data = response.json()
        
        if 'result' in data:
            return True
        return False
        
    except Exception as e:
        print(f"Error verifying transaction: {e}")
        return False

def create_wallet_connection_tx(wallet_address, message):
    """
    Создание транзакции для подключения кошелька
    """
    # В реальном проекте здесь будет создание подписанной транзакции
    # Для демо создаем mock транзакцию
    return {
        'wallet': wallet_address,
        'message': message,
        'signature': f"demo_signature_{wallet_address[:10]}",
        'tx_hash': f"demo_tx_{wallet_address[:10]}"
    }