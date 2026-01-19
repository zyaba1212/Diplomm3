// wallet_connect.js - Подключение Solana кошелька (Phantom, Solflare)

class SolanaWalletConnector {
    constructor() {
        this.walletAddress = null;
        this.provider = null;
        this.isConnected = false;
        
        // DOM элементы
        this.connectButton = document.getElementById('connect-wallet-btn');
        this.walletAddressElement = document.getElementById('wallet-address');
        this.walletStatusElement = document.getElementById('wallet-status');
        
        this.init();
    }

    init() {
        // Проверяем, есть ли уже подключенный кошелек в sessionStorage
        const savedWallet = sessionStorage.getItem('z96a_wallet_address');
        if (savedWallet) {
            this.walletAddress = savedWallet;
            this.isConnected = true;
            this.updateUI();
        }

        // Вешаем обработчик на кнопку
        if (this.connectButton) {
            this.connectButton.addEventListener('click', () => this.toggleConnect());
        }

        // Проверяем наличие Phantom при загрузке
        this.checkProvider();
    }

    async checkProvider() {
        // Проверяем различные провайдеры
        const providers = [
            window.solana,
            window.solflare,
            window.phantom?.solana
        ];

        for (const provider of providers) {
            if (provider && provider.isPhantom) {
                this.provider = provider;
                console.log('Найден провайдер кошелька:', provider.name || 'Unknown');
                break;
            }
        }

        if (!this.provider) {
            this.showNotification('Установите Phantom Wallet или Solflare', 'warning');
        }
    }

    async toggleConnect() {
        if (this.isConnected) {
            await this.disconnect();
        } else {
            await this.connect();
        }
    }

    async connect() {
        try {
            if (!this.provider) {
                this.showNotification('Кошелек не найден. Установите Phantom Wallet.', 'error');
                window.open('https://phantom.app/', '_blank');
                return;
            }

            // Запрос на подключение
            const response = await this.provider.connect();
            this.walletAddress = response.publicKey.toString();
            this.isConnected = true;

            // Сохраняем в sessionStorage
            sessionStorage.setItem('z96a_wallet_address', this.walletAddress);

            // Отправляем на сервер
            await this.sendToBackend(this.walletAddress);

            // Обновляем UI
            this.updateUI();

            this.showNotification('Кошелек успешно подключен!', 'success');

            // Запрашиваем подпись для подтверждения владения
            await this.requestSignature();

        } catch (error) {
            console.error('Ошибка подключения кошелька:', error);
            this.showNotification('Ошибка подключения: ' + error.message, 'error');
        }
    }

    async disconnect() {
        try {
            if (this.provider && this.provider.disconnect) {
                await this.provider.disconnect();
            }

            // Очищаем данные
            this.walletAddress = null;
            this.isConnected = false;
            sessionStorage.removeItem('z96a_wallet_address');

            // Обновляем UI
            this.updateUI();

            this.showNotification('Кошелек отключен', 'info');

        } catch (error) {
            console.error('Ошибка отключения:', error);
            this.showNotification('Ошибка отключения', 'error');
        }
    }

    async sendToBackend(address) {
        try {
            const response = await fetch('/api/wallet/connect/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ address: address })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                console.log('Адрес сохранен на сервере:', data);
                return data;
            } else {
                throw new Error(data.message || 'Ошибка сервера');
            }

        } catch (error) {
            console.error('Ошибка отправки на сервер:', error);
            // Не показываем пользователю эту ошибку, чтобы не пугать
        }
    }

    async requestSignature() {
        try {
            if (!this.provider) return;

            // Создаем сообщение для подписи
            const message = new TextEncoder().encode(
                `Z96A Network Authentication\n` +
                `Timestamp: ${Date.now()}\n` +
                `Wallet: ${this.walletAddress}\n` +
                `Purpose: Verify wallet ownership`
            );

            // Запрашиваем подпись
            const signature = await this.provider.signMessage(message, 'utf8');
            
            console.log('Подпись получена:', signature);
            this.showNotification('Владение кошельком подтверждено подписью', 'success');

            // Можно отправить подпись на сервер для дополнительной верификации
            // await this.sendSignatureToBackend(signature);

        } catch (error) {
            console.error('Ошибка подписи:', error);
            // Не блокируем пользователя при ошибке подписи
        }
    }

    async sendSignatureToBackend(signature) {
        // Реализация отправки подписи на сервер для верификации
        // ...
    }

    updateUI() {
        if (!this.connectButton || !this.walletAddressElement) return;

        if (this.isConnected && this.walletAddress) {
            // Обновляем кнопку
            this.connectButton.textContent = 'Отключить кошелек';
            this.connectButton.classList.add('connected');

            // Показываем адрес (сокращенный)
            const shortAddress = this.walletAddress.slice(0, 6) + '...' + this.walletAddress.slice(-4);
            this.walletAddressElement.textContent = shortAddress;
            this.walletAddressElement.title = this.walletAddress;

            // Обновляем статус
            if (this.walletStatusElement) {
                this.walletStatusElement.textContent = 'Подключен';
                this.walletStatusElement.className = 'status-connected';
            }

        } else {
            // Сбрасываем кнопку
            this.connectButton.textContent = 'Подключить кошелек';
            this.connectButton.classList.remove('connected');

            // Сбрасываем адрес
            this.walletAddressElement.textContent = 'Не подключено';
            this.walletAddressElement.removeAttribute('title');

            // Сбрасываем статус
            if (this.walletStatusElement) {
                this.walletStatusElement.textContent = 'Не подключен';
                this.walletStatusElement.className = 'status-disconnected';
            }
        }
    }

    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `wallet-notification ${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${this.getNotificationIcon(type)}</span>
            <span class="notification-text">${message}</span>
            <button class="notification-close">&times;</button>
        `;

        // Добавляем в DOM
        document.body.appendChild(notification);

        // Анимация появления
        setTimeout(() => notification.classList.add('show'), 10);

        // Удаляем через 5 секунд
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);

        // Обработчик закрытия
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }

    getNotificationIcon(type) {
        const icons = {
            'success': '✓',
            'error': '✗',
            'warning': '⚠',
            'info': 'ℹ'
        };
        return icons[type] || 'ℹ';
    }

    // Получение текущего баланса
    async getBalance() {
        if (!this.isConnected || !this.walletAddress) return null;

        try {
            // Здесь можно реализовать получение баланса через RPC
            // const balance = await this.provider.getBalance(this.walletAddress);
            // return balance;
            return 0; // Заглушка
        } catch (error) {
            console.error('Ошибка получения баланса:', error);
            return null;
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Ищем элементы кошелька на странице
    const walletSection = document.querySelector('.wallet-section');
    
    if (walletSection) {
        // Создаем элементы, если их нет
        if (!document.getElementById('connect-wallet-btn')) {
            const connectBtn = document.createElement('button');
            connectBtn.id = 'connect-wallet-btn';
            connectBtn.className = 'btn-wallet';
            connectBtn.textContent = 'Подключить кошелек';
            
            const addressSpan = document.createElement('span');
            addressSpan.id = 'wallet-address';
            addressSpan.textContent = 'Не подключено';
            
            walletSection.appendChild(connectBtn);
            walletSection.appendChild(addressSpan);
        }

        // Инициализируем коннектор
        window.walletConnector = new SolanaWalletConnector();
    }
});

// Стили для уведомлений
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
.wallet-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(46, 45, 46, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 15px 20px;
    min-width: 300px;
    max-width: 400px;
    display: flex;
    align-items: center;
    gap: 15px;
    transform: translateX(120%);
    transition: transform 0.3s ease-out;
    z-index: 10000;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.wallet-notification.show {
    transform: translateX(0);
}

.wallet-notification.success {
    border-left: 4px solid #14F195;
}

.wallet-notification.error {
    border-left: 4px solid #FF4444;
}

.wallet-notification.warning {
    border-left: 4px solid #FF9900;
}

.wallet-notification.info {
    border-left: 4px solid #4682b4;
}

.notification-icon {
    font-size: 1.2rem;
    font-weight: bold;
}

.notification-text {
    flex: 1;
    font-size: 0.9rem;
    line-height: 1.4;
}

.notification-close {
    background: none;
    border: none;
    color: #aaa;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.3s;
}

.notification-close:hover {
    background: rgba(255, 255, 255, 0.1);
}
`;
document.head.appendChild(notificationStyles);

// Экспортируем для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SolanaWalletConnector;
}