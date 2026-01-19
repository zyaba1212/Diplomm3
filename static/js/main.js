// Z96A Main JavaScript
let walletState = {
    connected: false,
    address: null,
    nickname: null,
    balance: 0
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('Z96A Network Architecture loaded');
    
    // Загружаем сохраненное состояние кошелька
    loadWalletState();
    
    // Инициализация
    initNavigation();
    initTheme();
    initWalletIntegration();
    initLanguageSwitcher();
    
    // Инициализация модальных окон
    initModals();
    
    // Инициализация уведомлений
    initNotifications();
});

function loadWalletState() {
    try {
        const saved = localStorage.getItem('z96a_wallet_state');
        if (saved) {
            const state = JSON.parse(saved);
            walletState = {
                ...walletState,
                ...state
            };
            
            if (walletState.connected && walletState.address) {
                updateWalletUI();
            }
        }
    } catch (error) {
        console.error('Error loading wallet state:', error);
    }
}

function saveWalletState() {
    try {
        localStorage.setItem('z96a_wallet_state', JSON.stringify(walletState));
    } catch (error) {
        console.error('Error saving wallet state:', error);
    }
}

function initNavigation() {
    // Подсветка активной навигации
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath || 
            (linkPath !== '/' && currentPath.startsWith(linkPath)) ||
            (linkPath === '/' && currentPath === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function initTheme() {
    // Инициализация темы
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

function initWalletIntegration() {
    // Инициализация интеграции с кошельком
    const walletBtn = document.getElementById('wallet-btn');
    if (walletBtn) {
        walletBtn.addEventListener('click', toggleWalletConnection);
        updateWalletUI();
    }
    
    // Добавляем контекстное меню для отключения
    addWalletContextMenu();
}

async function toggleWalletConnection() {
    if (walletState.connected) {
        await disconnectWallet();
    } else {
        await connectWallet();
    }
}

async function connectWallet() {
    try {
        // Проверяем доступность Solana
        if (!window.solana || !window.solana.isPhantom) {
            showNotification('Please install Phantom wallet!', 'error');
            
            // Показать модальное окно с инструкцией
            showWalletInstallModal();
            return;
        }
        
        // Подключаемся к кошельку
        const resp = await window.solana.connect();
        const publicKey = resp.publicKey.toString();
        
        // Обновляем состояние
        walletState = {
            connected: true,
            address: publicKey,
            nickname: generateNickname(publicKey),
            balance: await getWalletBalance(publicKey)
        };
        
        saveWalletState();
        updateWalletUI();
        
        showNotification(`Wallet connected: ${walletState.nickname}`, 'success');
        
        // Обновляем статистику пользователя
        updateUserStats();
        
    } catch (error) {
        console.error('Wallet connection error:', error);
        showNotification('Failed to connect wallet: ' + error.message, 'error');
    }
}

async function disconnectWallet() {
    try {
        if (window.solana && window.solana.disconnect) {
            await window.solana.disconnect();
        }
        
        walletState = {
            connected: false,
            address: null,
            nickname: null,
            balance: 0
        };
        
        saveWalletState();
        updateWalletUI();
        
        showNotification('Wallet disconnected', 'info');
        
    } catch (error) {
        console.error('Wallet disconnect error:', error);
        showNotification('Error disconnecting wallet', 'error');
    }
}

function updateWalletUI() {
    const walletBtn = document.getElementById('wallet-btn');
    if (!walletBtn) return;
    
    if (walletState.connected && walletState.address) {
        walletBtn.innerHTML = `
            <span class="wallet-icon">🔗</span>
            <span class="wallet-info">
                <span class="wallet-nickname">${walletState.nickname}</span>
                <span class="wallet-address">${walletState.address.slice(0, 6)}...${walletState.address.slice(-4)}</span>
            </span>
        `;
        walletBtn.classList.add('connected');
        walletBtn.title = `Click to disconnect\nBalance: ${walletState.balance.toFixed(2)} SOL`;
        
        // Показываем меню пользователя
        showUserMenu();
        
    } else {
        walletBtn.innerHTML = `
            <span class="wallet-icon">👛</span>
            <span>Connect Wallet</span>
        `;
        walletBtn.classList.remove('connected');
        walletBtn.title = 'Click to connect wallet';
        
        // Скрываем меню пользователя
        hideUserMenu();
    }
}

function generateNickname(address) {
    // Генерируем никнейм на основе адреса кошелька
    const hexPart = address.slice(-8);
    const adjectives = ['Cosmic', 'Digital', 'Network', 'Crypto', 'Block', 'Chain', 'Data', 'Byte'];
    const nouns = ['Pioneer', 'Explorer', 'Architect', 'Node', 'Validator', 'Router', 'Gateway'];
    
    const adj = adjectives[parseInt(hexPart.slice(0, 2), 16) % adjectives.length];
    const noun = nouns[parseInt(hexPart.slice(2, 4), 16) % nouns.length];
    
    return `${adj}${noun}`;
}

async function getWalletBalance(address) {
    try {
        // В реальном приложении здесь будет запрос к Solana RPC
        // Для демонстрации возвращаем случайное значение
        return Math.random() * 10;
    } catch (error) {
        console.error('Error getting wallet balance:', error);
        return 0;
    }
}

function addWalletContextMenu() {
    const walletBtn = document.getElementById('wallet-btn');
    if (!walletBtn) return;
    
    // Добавляем контекстное меню по правому клику
    walletBtn.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        
        if (walletState.connected) {
            showWalletContextMenu(e.clientX, e.clientY);
        }
    });
}

function showWalletContextMenu(x, y) {
    // Удаляем старое меню если есть
    const oldMenu = document.getElementById('wallet-context-menu');
    if (oldMenu) oldMenu.remove();
    
    const menu = document.createElement('div');
    menu.id = 'wallet-context-menu';
    menu.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        background: rgba(30, 30, 46, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid var(--color-space-purple);
        border-radius: 8px;
        padding: 10px 0;
        min-width: 200px;
        z-index: 1000;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    `;
    
    menu.innerHTML = `
        <div class="context-menu-header" style="padding: 10px 15px; border-bottom: 1px solid var(--color-border);">
            <div style="font-weight: bold; color: var(--color-neon-blue);">${walletState.nickname}</div>
            <div style="font-size: 0.8rem; color: var(--color-text-secondary); font-family: monospace;">
                ${walletState.address}
            </div>
        </div>
        <div class="context-menu-item" style="padding: 10px 15px; cursor: pointer; transition: background 0.3s ease;" 
             onclick="copyWalletAddress()">
            📋 Copy Address
        </div>
        <div class="context-menu-item" style="padding: 10px 15px; cursor: pointer; transition: background 0.3s ease;"
             onclick="viewOnSolscan()">
            🔍 View on Solscan
        </div>
        <div class="context-menu-item" style="padding: 10px 15px; border-top: 1px solid var(--color-border); cursor: pointer; transition: background 0.3s ease; color: #ff4444;"
             onclick="disconnectWallet()">
            🚫 Disconnect Wallet
        </div>
    `;
    
    document.body.appendChild(menu);
    
    // Закрываем меню при клике вне его
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 0);
}

function copyWalletAddress() {
    if (!walletState.address) return;
    
    navigator.clipboard.writeText(walletState.address)
        .then(() => {
            showNotification('Wallet address copied to clipboard!', 'success');
            document.getElementById('wallet-context-menu')?.remove();
        })
        .catch(err => {
            console.error('Failed to copy:', err);
            showNotification('Failed to copy address', 'error');
        });
}

function viewOnSolscan() {
    if (!walletState.address) return;
    
    window.open(`https://solscan.io/account/${walletState.address}`, '_blank');
    document.getElementById('wallet-context-menu')?.remove();
}

function showUserMenu() {
    let userMenu = document.getElementById('user-menu');
    if (!userMenu) {
        userMenu = document.createElement('div');
        userMenu.id = 'user-menu';
        userMenu.className = 'user-menu';
        userMenu.style.cssText = `
            position: absolute;
            top: 70px;
            right: 20px;
            background: rgba(30, 30, 46, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid var(--color-space-purple);
            border-radius: 10px;
            padding: 20px;
            min-width: 250px;
            z-index: 999;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        `;
        
        document.querySelector('.header-content').appendChild(userMenu);
    }
    
    userMenu.innerHTML = `
        <div class="user-info">
            <div class="user-avatar" style="width: 50px; height: 50px; background: linear-gradient(135deg, var(--color-neon-blue), var(--color-neon-purple)); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: white; margin-bottom: 15px;">
                ${walletState.nickname?.charAt(0) || 'U'}
            </div>
            <h4 style="margin: 0 0 5px 0; color: var(--color-neon-blue);">${walletState.nickname}</h4>
            <div style="font-family: monospace; font-size: 0.8rem; color: var(--color-text-secondary); margin-bottom: 15px;">
                ${walletState.address}
            </div>
            <div class="user-stats" style="display: grid; gap: 10px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between;">
                    <span>Reputation:</span>
                    <span style="color: var(--color-neon-blue); font-weight: bold;">0</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>SOL Balance:</span>
                    <span style="color: var(--color-neon-blue); font-weight: bold;">${walletState.balance.toFixed(2)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Proposals:</span>
                    <span style="color: var(--color-neon-blue); font-weight: bold;">0</span>
                </div>
            </div>
            <button onclick="showProposalForm()" style="width: 100%; padding: 10px; background: linear-gradient(135deg, var(--color-neon-blue), var(--color-neon-purple)); border: none; border-radius: 5px; color: white; cursor: pointer; font-weight: bold; margin-bottom: 10px;">
                ✨ Submit Proposal
            </button>
            <button onclick="disconnectWallet()" style="width: 100%; padding: 10px; background: rgba(255, 68, 68, 0.2); border: 1px solid #ff4444; border-radius: 5px; color: #ff4444; cursor: pointer;">
                🚫 Disconnect
            </button>
        </div>
    `;
    
    // Закрываем меню при клике вне его
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!userMenu.contains(e.target) && !document.getElementById('wallet-btn').contains(e.target)) {
                userMenu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 0);
}

function hideUserMenu() {
    const userMenu = document.getElementById('user-menu');
    if (userMenu) {
        userMenu.remove();
    }
}

function showWalletInstallModal() {
    // Создаем модальное окно с инструкцией по установке Phantom
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h3>🔧 Install Phantom Wallet</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p>To use all features of Z96A Network Architecture, you need to install Phantom wallet:</p>
                
                <div style="margin: 20px 0;">
                    <h4>For Chrome/Brave:</h4>
                    <a href="https://chrome.google.com/webstore/detail/phantom/bfnaelmomeimhlpmgjnjophhpkkoljpa" target="_blank" style="display: block; padding: 10px; background: #9d4edd; color: white; text-align: center; border-radius: 5px; text-decoration: none; margin: 10px 0;">
                        Install Phantom for Chrome
                    </a>
                </div>
                
                <div style="margin: 20px 0;">
                    <h4>For Firefox:</h4>
                    <a href="https://addons.mozilla.org/en-US/firefox/addon/phantom-app/" target="_blank" style="display: block; padding: 10px; background: #ff9900; color: white; text-align: center; border-radius: 5px; text-decoration: none; margin: 10px 0;">
                        Install Phantom for Firefox
                    </a>
                </div>
                
                <p style="font-size: 0.9rem; color: var(--color-text-secondary);">
                    After installation, refresh this page and click "Connect Wallet" again.
                </p>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function showProposalForm() {
    // Здесь будет форма для подачи предложений
    showNotification('Proposal form will be available soon!', 'info');
}

function updateUserStats() {
    // Здесь будет обновление статистики пользователя с сервера
    console.log('Updating user stats...');
}

function initLanguageSwitcher() {
    const langBtn = document.querySelector('.lang-btn');
    if (!langBtn) return;
    
    langBtn.addEventListener('click', function() {
        const currentLang = document.documentElement.lang || 'en';
        const newLang = currentLang === 'en' ? 'ru' : 'en';
        
        // Устанавливаем cookie для языка
        document.cookie = `django_language=${newLang}; path=/; max-age=31536000`;
        
        // Показываем уведомление
        showNotification(`Language switched to ${newLang === 'en' ? 'English' : 'Russian'}`, 'info');
        
        // Перезагружаем страницу
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    });
}

function initModals() {
    // Инициализация модальных окон
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-close') || 
            e.target.classList.contains('modal-overlay')) {
            e.target.closest('.modal-overlay')?.remove();
        }
    });
}

function initNotifications() {
    // Добавляем стили для уведомлений
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
            max-width: 400px;
            word-break: break-word;
        }
        
        .notification-success {
            background: linear-gradient(135deg, #00c851, #007e33);
            color: white;
        }
        
        .notification-error {
            background: linear-gradient(135deg, #ff4444, #cc0000);
            color: white;
        }
        
        .notification-info {
            background: linear-gradient(135deg, #33b5e5, #0099cc);
            color: white;
        }
        
        .notification-warning {
            background: linear-gradient(135deg, #ffbb33, #ff8800);
            color: white;
        }
    `;
    document.head.appendChild(style);
}

function showNotification(message, type = 'info') {
    // Удаляем старые уведомления
    const oldNotifications = document.querySelectorAll('.notification');
    oldNotifications.forEach(n => {
        n.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => n.remove(), 300);
    });
    
    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Экспортируем функции для использования в других скриптах
window.Z96A = {
    connectWallet,
    disconnectWallet,
    showNotification,
    copyWalletAddress,
    viewOnSolscan,
    showProposalForm
};