// static/js/wallet.js - Полная реализация кошелька для блокчейн-транзакций

class WalletManager {
    constructor() {
        this.userAddress = localStorage.getItem('sui_wallet_address') || null;
        this.balance = 0;
        this.transactions = [];
        this.offlineMode = false;
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadWalletInfo();
        this.checkConnection();
    }
    
    bindEvents() {
        // Кнопка подключения кошелька
        const connectBtn = document.getElementById('connect-wallet');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connectWallet());
        }
        
        // Кнопка создания транзакции
        const createTxBtn = document.getElementById('create-transaction');
        if (createTxBtn) {
            createTxBtn.addEventListener('click', () => this.createTransaction());
        }
        
        // Офлайн подпись
        const offlineSignBtn = document.getElementById('offline-sign');
        if (offlineSignBtn) {
            offlineSignBtn.addEventListener('click', () => this.signOffline());
        }
        
        // Отправка подписанной транзакции
        const submitTxBtn = document.getElementById('submit-transaction');
        if (submitTxBtn) {
            submitTxBtn.addEventListener('click', () => this.submitTransaction());
        }
        
        // Обновление баланса
        const refreshBtn = document.getElementById('refresh-balance');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.updateBalance());
        }
    }
    
    async connectWallet() {
        try {
            // В реальном приложении: подключение через Sui Wallet Extension
            // Демо-реализация
            if (typeof window.suiWallet !== 'undefined') {
                const accounts = await window.suiWallet.requestAccounts();
                this.userAddress = accounts[0];
                localStorage.setItem('sui_wallet_address', this.userAddress);
                this.showNotification('Кошелек подключен', 'success');
                this.updateUI();
                this.updateBalance();
            } else {
                // Режим демо: генерируем тестовый адрес
                this.userAddress = this.generateDemoAddress();
                localStorage.setItem('sui_wallet_address', this.userAddress);
                this.showNotification('Демо-кошелек создан', 'info');
                this.offlineMode = true;
                this.updateUI();
                this.updateBalance();
            }
        } catch (error) {
            console.error('Wallet connection error:', error);
            this.showNotification('Ошибка подключения кошелька', 'error');
        }
    }
    
    async createTransaction() {
        if (!this.userAddress) {
            this.showNotification('Сначала подключите кошелек', 'warning');
            return;
        }
        
        const recipient = document.getElementById('recipient-address')?.value;
        const amount = document.getElementById('transaction-amount')?.value;
        const betType = document.getElementById('bet-type')?.value;
        
        if (!recipient || !amount) {
            this.showNotification('Заполните все поля', 'warning');
            return;
        }
        
        const txData = {
            sender: this.userAddress,
            recipient: recipient,
            amount: parseFloat(amount),
            metadata: {
                bet_type: betType,
                timestamp: new Date().toISOString()
            }
        };
        
        try {
            const response = await fetch('/api/blockchain/create-transaction/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(txData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Транзакция создана', 'success');
                this.displayTransaction(result.transaction);
                
                if (result.offline_mode) {
                    this.showOfflineSigning(result.transaction);
                }
            } else {
                this.showNotification(result.error || 'Ошибка создания транзакции', 'error');
            }
        } catch (error) {
            console.error('Create transaction error:', error);
            this.showNotification('Сетевая ошибка', 'error');
        }
    }
    
    async signOffline() {
        const privateKey = document.getElementById('offline-private-key')?.value;
        const txHash = document.getElementById('offline-tx-hash')?.value;
        
        if (!privateKey || !txHash) {
            this.showNotification('Введите приватный ключ и хеш транзакции', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/blockchain/sign-offline/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tx_hash: txHash,
                    private_key: privateKey
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Транзакция подписана', 'success');
                this.displaySignedTransaction(result.signed_transaction);
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Offline signing error:', error);
            this.showNotification('Ошибка подписи', 'error');
        }
    }
    
    async submitTransaction() {
        const signedData = document.getElementById('signed-transaction-data')?.value;
        
        if (!signedData) {
            this.showNotification('Нет данных для отправки', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/blockchain/submit-transaction/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(JSON.parse(signedData))
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Транзакция отправлена в сеть', 'success');
                this.updateTransactionStatus(result.tx_digest, 'submitted');
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Submit transaction error:', error);
            this.showNotification('Ошибка отправки', 'error');
        }
    }
    
    async updateBalance() {
        if (!this.userAddress) return;
        
        try {
            const response = await fetch(`/api/blockchain/balance/${this.userAddress}/`);
            const result = await response.json();
            
            if (result.success) {
                this.balance = result.balance;
                this.displayBalance();
            }
        } catch (error) {
            console.error('Balance update error:', error);
            this.balance = 0;
            this.displayBalance();
        }
    }
    
    // Вспомогательные методы
    displayBalance() {
        const balanceElement = document.getElementById('wallet-balance');
        if (balanceElement) {
            balanceElement.textContent = `${this.balance} SUI`;
        }
    }
    
    displayTransaction(tx) {
        const txList = document.getElementById('transactions-list');
        if (!txList) return;
        
        const txElement = document.createElement('div');
        txElement.className = 'transaction-item';
        txElement.innerHTML = `
            <div class="tx-hash">${tx.hash.substring(0, 16)}...</div>
            <div class="tx-amount">${tx.amount} SUI</div>
            <div class="tx-status ${tx.status}">${this.getStatusText(tx.status)}</div>
            <div class="tx-actions">
                ${tx.status === 'pending' ? '<button class="btn-sign">Подписать</button>' : ''}
                ${tx.status === 'signed' ? '<button class="btn-submit">Отправить</button>' : ''}
            </div>
        `;
        
        txList.prepend(txElement);
    }
    
    showOfflineSigning(tx) {
        const offlineSection = document.getElementById('offline-signing-section');
        const txHashInput = document.getElementById('offline-tx-hash');
        
        if (offlineSection && txHashInput) {
            offlineSection.style.display = 'block';
            txHashInput.value = tx.hash;
        }
    }
    
    showNotification(message, type = 'info') {
        // Реализация уведомлений
        console.log(`${type.toUpperCase()}: ${message}`);
        alert(`${type}: ${message}`); // Временная реализация
    }
    
    generateDemoAddress() {
        return `0x${Array.from({length: 64}, () => 
            Math.floor(Math.random() * 16).toString(16)
        ).join('')}`;
    }
    
    getStatusText(status) {
        const statusMap = {
            'pending': 'Ожидает',
            'signed': 'Подписана',
            'submitted': 'Отправлена',
            'confirmed': 'Подтверждена',
            'failed': 'Ошибка'
        };
        return statusMap[status] || status;
    }
    
    async checkConnection() {
        try {
            const response = await fetch('/api/blockchain/status/');
            const result = await response.json();
            this.offlineMode = !result.online;
            
            const statusElement = document.getElementById('blockchain-status');
            if (statusElement) {
                statusElement.textContent = this.offlineMode ? 'Офлайн режим' : 'Онлайн';
                statusElement.className = this.offlineMode ? 'offline' : 'online';
            }
        } catch (error) {
            this.offlineMode = true;
        }
    }
    
    updateUI() {
        const addressElement = document.getElementById('wallet-address');
        const connectBtn = document.getElementById('connect-wallet');
        
        if (addressElement && this.userAddress) {
            addressElement.textContent = `${this.userAddress.substring(0, 10)}...`;
        }
        
        if (connectBtn) {
            connectBtn.textContent = this.userAddress ? 'Кошелек подключен' : 'Подключить кошелек';
            connectBtn.disabled = !!this.userAddress;
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.walletManager = new WalletManager();
});