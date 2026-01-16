// Интеграция с Solana кошельком

class WalletManager {
    constructor() {
        this.connection = null;
        this.wallet = null;
        this.userProfile = null;
        this.provider = null;
        
        this.init();
    }
    
    async init() {
        // Проверяем наличие Phantom Wallet
        if ('solana' in window) {
            this.provider = window.solana;
            this.setupEventListeners();
        } else {
            console.warn('Solana wallet not found');
        }
        
        // Проверяем сохраненное соединение
        await this.checkSavedConnection();
    }
    
    setupEventListeners() {
        const connectBtn = document.getElementById('connectWalletBtn');
        const disconnectBtn = document.getElementById('disconnectWalletBtn');
        
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connect());
        }
        
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.disconnect());
        }
    }
    
    async connect() {
        try {
            if (!this.provider) {
                this.showWalletInstallModal();
                return;
            }
            
            // Запрос на подключение кошелька
            const response = await this.provider.connect();
            this.wallet = response.publicKey.toString();
            
            // Сохраняем в localStorage
            localStorage.setItem('z96a_wallet_address', this.wallet);
            
            // Отправляем на сервер для верификации
            await this.verifyWalletOnServer();
            
            // Показываем уведомление
            window.Z96A.utils.showNotification('Кошелек успешно подключен', 'success');
            
        } catch (error) {
            console.error('Wallet connection error:', error);
            window.Z96A.utils.showNotification('Ошибка подключения кошелька', 'error');
        }
    }
    
    async verifyWalletOnServer() {
        try {
            // Создаем сообщение для подписи
            const message = `Z96A Login: ${Date.now()}`;
            const encodedMessage = new TextEncoder().encode(message);
            
            // Запрашиваем подпись
            const signature = await this.provider.signMessage(encodedMessage, 'utf8');
            
            // Отправляем на сервер
            const response = await fetch('/api/connect-wallet/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    wallet_address: this.wallet,
                    signature: Array.from(signature),
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.userProfile = {
                    nickname: data.nickname,
                    walletAddress: data.wallet_address
                };
                
                // Сохраняем nickname
                localStorage.setItem('z96a_user_nickname', data.nickname);
                
                // Обновляем UI
                this.updateUI();
                
            } else {
                throw new Error(data.error || 'Verification failed');
            }
            
        } catch (error) {
            console.error('Verification error:', error);
            throw error;
        }
    }
    
    async checkSavedConnection() {
        const savedWallet = localStorage.getItem('z96a_wallet_address');
        const savedNickname = localStorage.getItem('z96a_user_nickname');
        
        if (savedWallet && savedNickname) {
            this.wallet = savedWallet;
            this.userProfile = {
                nickname: savedNickname,
                walletAddress: savedWallet
            };
            this.updateUI();
        }
    }
    
    updateUI() {
        const walletBtn = document.getElementById('connectWalletBtn');
        const userInfo = document.getElementById('userInfo');
        const userNickname = document.getElementById('userNickname');
        
        if (walletBtn && userInfo && userNickname && this.userProfile) {
            walletBtn.style.display = 'none';
            userInfo.style.display = 'flex';
            userNickname.textContent = this.userProfile.nickname;
        }
    }
    
    async disconnect() {
        try {
            if (this.provider && this.provider.disconnect) {
                await this.provider.disconnect();
            }
            
            // Очищаем localStorage
            localStorage.removeItem('z96a_wallet_address');
            localStorage.removeItem('z96a_user_nickname');
            
            // Сбрасываем состояние
            this.wallet = null;
            this.userProfile = null;
            
            // Обновляем UI
            const walletBtn = document.getElementById('connectWalletBtn');
            const userInfo = document.getElementById('userInfo');
            
            if (walletBtn && userInfo) {
                walletBtn.style.display = 'flex';
                userInfo.style.display = 'none';
            }
            
            window.Z96A.utils.showNotification('Кошелек отключен', 'info');
            
        } catch (error) {
            console.error('Disconnect error:', error);
            window.Z96A.utils.showNotification('Ошибка отключения', 'error');
        }
    }
    
    showWalletInstallModal() {
        const modal = document.createElement('div');
        modal.className = 'wallet-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Установите кошелек</h3>
                <p>Для работы с блокчейном необходим Solana кошелек. Рекомендуем установить Phantom:</p>
                <div class="wallet-options">
                    <a href="https://phantom.app/" target="_blank" class="wallet-option">
                        <img src="https://phantom.app/img/logo.png" alt="Phantom">
                        <span>Phantom Wallet</span>
                    </a>
                </div>
                <button class="close-modal">Закрыть</button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Стили для модального окна
        const styles = `
        .wallet-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            backdrop-filter: blur(5px);
        }
        
        .wallet-modal .modal-content {
            background: linear-gradient(135deg, #1b1523 0%, #0a1a2d 100%);
            padding: 2rem;
            border-radius: 16px;
            max-width: 400px;
            width: 90%;
            border: 1px solid rgba(108, 99, 255, 0.3);
        }
        
        .wallet-modal h3 {
            color: #6c63ff;
            margin-bottom: 1rem;
        }
        
        .wallet-modal p {
            margin-bottom: 1.5rem;
            color: #aaa;
        }
        
        .wallet-options {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .wallet-option {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            text-decoration: none;
            color: white;
            transition: all 0.3s ease;
        }
        
        .wallet-option:hover {
            background: rgba(108, 99, 255, 0.2);
            transform: translateY(-2px);
        }
        
        .wallet-option img {
            width: 32px;
            height: 32px;
            border-radius: 8px;
        }
        
        .close-modal {
            width: 100%;
            padding: 0.8rem;
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            border-radius: 8px;
            cursor: pointer;
            font-family: inherit;
        }
        `;
        
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
        
        // Закрытие модального окна
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
            styleEl.remove();
        });
        
        // Закрытие по клику на фон
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                styleEl.remove();
            }
        });
    }
    
    // Получить публичный ключ
    getPublicKey() {
        return this.wallet;
    }
    
    // Получить информацию о пользователе
    getUserInfo() {
        return this.userProfile;
    }
    
    // Проверить, подключен ли кошелек
    isConnected() {
        return !!this.wallet && !!this.userProfile;
    }
    
    // Отправить транзакцию
    async sendTransaction(transactionData) {
        if (!this.isConnected()) {
            throw new Error('Wallet not connected');
        }
        
        try {
            // В реальном проекте здесь будет создание и отправка транзакции
            // Для демо создаем mock транзакцию
            
            const mockTransaction = {
                signature: `mock_signature_${Date.now()}`,
                slot: Math.floor(Math.random() * 1000000),
                blockTime: Date.now() / 1000
            };
            
            window.Z96A.utils.showNotification('Транзакция отправлена', 'success');
            
            return mockTransaction;
            
        } catch (error) {
            console.error('Transaction error:', error);
            window.Z96A.utils.showNotification('Ошибка транзакции', 'error');
            throw error;
        }
    }
    
    // Подписать сообщение
    async signMessage(message) {
        if (!this.isConnected()) {
            throw new Error('Wallet not connected');
        }
        
        try {
            const encodedMessage = new TextEncoder().encode(message);
            const signature = await this.provider.signMessage(encodedMessage, 'utf8');
            return Array.from(signature);
        } catch (error) {
            console.error('Sign message error:', error);
            throw error;
        }
    }
}

// Инициализация менеджера кошельков
let walletManager = null;

document.addEventListener('DOMContentLoaded', function() {
    walletManager = new WalletManager();
    
    // Экспортируем для глобального доступа
    window.Z96A.wallet = walletManager;
    
    // Обработка предложений через блокчейн
    setupProposalSubmission();
});

function setupProposalSubmission() {
    const proposalForm = document.getElementById('proposalForm');
    if (!proposalForm) return;
    
    proposalForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!window.Z96A.wallet.isConnected()) {
            window.Z96A.utils.showNotification('Подключите кошелек для отправки предложений', 'error');
            return;
        }
        
        const formData = {
            type: document.getElementById('proposalType').value,
            title: document.getElementById('proposalTitle').value,
            description: document.getElementById('proposalDescription').value,
            location: document.getElementById('proposalLocation').value,
            specifications: document.getElementById('proposalSpecs').value
        };
        
        try {
            // Парсим спецификации если они есть
            let specs = {};
            if (formData.specifications) {
                try {
                    specs = JSON.parse(formData.specifications);
                } catch (e) {
                    console.warn('Invalid JSON in specs, using empty object');
                }
            }
            
            // Создаем транзакцию
            const tx = await window.Z96A.wallet.sendTransaction({
                type: 'proposal',
                data: {
                    proposal_type: formData.type,
                    title: formData.title,
                    description: formData.description,
                    specifications: specs
                }
            });
            
            // Отправляем на сервер
            const response = await fetch('/api/submit-proposal/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    wallet_address: window.Z96A.wallet.getPublicKey(),
                    proposal: {
                        type: formData.type,
                        description: formData.description,
                        specifications: specs,
                        transaction_hash: tx.signature
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.Z96A.utils.showNotification('Предложение успешно отправлено!', 'success');
                
                // Закрываем модальное окно
                const modal = document.getElementById('proposalModal');
                if (modal) {
                    modal.style.display = 'none';
                }
                
                // Очищаем форму
                proposalForm.reset();
                
            } else {
                throw new Error(data.error || 'Submission failed');
            }
            
        } catch (error) {
            console.error('Proposal submission error:', error);
            window.Z96A.utils.showNotification('Ошибка отправки предложения', 'error');
        }
    });
}

// Закрытие модального окна
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('proposalModal');
    if (!modal) return;
    
    const closeBtn = modal.querySelector('.close');
    const cancelBtn = modal.querySelector('.cancel-btn');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Закрытие по клику вне окна
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Открытие модального окна
document.addEventListener('DOMContentLoaded', function() {
    const proposeBtn = document.getElementById('btnPropose');
    const modal = document.getElementById('proposalModal');
    
    if (proposeBtn && modal) {
        proposeBtn.addEventListener('click', () => {
            if (!window.Z96A.wallet.isConnected()) {
                window.Z96A.utils.showNotification('Подключите кошелек для отправки предложений', 'error');
                return;
            }
            modal.style.display = 'block';
        });
    }
});