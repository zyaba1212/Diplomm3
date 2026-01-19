/**
 * Z96A - Основной JavaScript файл проекта
 * Версия: 1.0.0
 * Автор: Зыблиенко Дмитрий
 */

// ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
window.walletConnected = false;
window.walletAddress = null;
window.userProfile = null;
window.solana = null;

// ===== ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ =====
document.addEventListener('DOMContentLoaded', function() {
    console.log('Z96A Platform initialized');
    
    // Инициализация основных функций
    initSidebars();
    initLanguageSwitcher();
    initWalletConnection();
    initNotifications();
    initScrollAnimations();
    initMobileMenu();
    
    // Проверка обновлений
    checkForUpdates();
});

// ===== УПРАВЛЕНИЕ БОКОВЫМИ ПАНЕЛЯМИ =====
function initSidebars() {
    // Восстановление состояния из localStorage
    const leftSidebarState = localStorage.getItem('sidebar-left-state');
    const rightSidebarState = localStorage.getItem('sidebar-right-state');
    
    if (leftSidebarState === 'collapsed') {
        collapseSidebar('news-sidebar');
    }
    
    if (rightSidebarState === 'collapsed') {
        collapseSidebar('comments-sidebar');
    }
    
    // Обработчики для кнопок
    document.querySelectorAll('.sidebar-toggle').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const sidebarId = this.closest('.sidebar-left, .sidebar-right').id;
            toggleSidebar(sidebarId);
        });
    });
    
    document.querySelectorAll('.sidebar-close').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const sidebarId = this.closest('.sidebar-left, .sidebar-right').id;
            closeSidebar(sidebarId);
        });
    });
}

function toggleSidebar(sidebarId) {
    const sidebar = document.getElementById(sidebarId);
    if (!sidebar) return;
    
    sidebar.classList.toggle('collapsed');
    
    // Сохранение состояния
    const state = sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded';
    localStorage.setItem(`${sidebarId}-state`, state);
    
    // Обновление иконки
    const toggleIcon = sidebar.querySelector('.toggle-icon');
    if (toggleIcon) {
        if (sidebar.classList.contains('collapsed')) {
            if (sidebarId === 'news-sidebar') {
                toggleIcon.textContent = '→';
            } else {
                toggleIcon.textContent = '←';
            }
        } else {
            if (sidebarId === 'news-sidebar') {
                toggleIcon.textContent = '←';
            } else {
                toggleIcon.textContent = '→';
            }
        }
    }
    
    // Уведомление о изменении
    showNotification('Настройки панели сохранены', 'info');
}

function collapseSidebar(sidebarId) {
    const sidebar = document.getElementById(sidebarId);
    if (sidebar) {
        sidebar.classList.add('collapsed');
        const toggleIcon = sidebar.querySelector('.toggle-icon');
        if (toggleIcon) {
            if (sidebarId === 'news-sidebar') {
                toggleIcon.textContent = '→';
            } else {
                toggleIcon.textContent = '←';
            }
        }
    }
}

function closeSidebar(sidebarId) {
    const sidebar = document.getElementById(sidebarId);
    if (sidebar) {
        sidebar.style.display = 'none';
        localStorage.setItem(`${sidebarId}-state`, 'hidden');
        showNotification('Панель скрыта', 'info');
    }
}

// ===== ПЕРЕКЛЮЧЕНИЕ ЯЗЫКА =====
function initLanguageSwitcher() {
    const langButtons = document.querySelectorAll('.lang-btn');
    const currentLang = localStorage.getItem('z96a-language') || 'ru';
    
    // Установка активного языка
    langButtons.forEach(btn => {
        if (btn.dataset.lang === currentLang) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
        
        btn.addEventListener('click', function() {
            const lang = this.dataset.lang;
            switchLanguage(lang);
        });
    });
    
    // Загрузка переводов
    loadTranslations(currentLang);
}

function switchLanguage(lang) {
    if (lang === localStorage.getItem('z96a-language')) {
        return;
    }
    
    // Обновление кнопок
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.lang === lang) {
            btn.classList.add('active');
        }
    });
    
    // Сохранение в localStorage
    localStorage.setItem('z96a-language', lang);
    
    // Загрузка переводов
    loadTranslations(lang);
    
    // Обновление страницы
    applyTranslations(lang);
    
    showNotification(`Язык изменен на ${lang === 'ru' ? 'Русский' : 'English'}`, 'success');
}

function loadTranslations(lang) {
    // В реальном проекте здесь будет загрузка JSON файла с переводами
    const translations = {
        ru: {
            // Общие фразы
            'connect_wallet': 'Подключить кошелек',
            'disconnect': 'Отключить',
            'loading': 'Загрузка...',
            'error': 'Ошибка',
            'success': 'Успешно',
            'warning': 'Предупреждение',
            'info': 'Информация',
            
            // Навигация
            'home': 'Главная',
            'architecture': 'Архитектура',
            'news': 'Новости',
            'discussion': 'Обсуждение',
            'about': 'О проекте',
            'roadmap': 'Дорожная карта',
            
            // Боковая панель новостей
            'latest_news': 'Последние новости',
            'all_news': 'Все новости',
            'no_news': 'Новости загружаются...',
            
            // Подвал
            'copyright': 'Все права защищены',
            'privacy': 'Политика конфиденциальности',
            'terms': 'Условия использования',
        },
        en: {
            // Common phrases
            'connect_wallet': 'Connect Wallet',
            'disconnect': 'Disconnect',
            'loading': 'Loading...',
            'error': 'Error',
            'success': 'Success',
            'warning': 'Warning',
            'info': 'Information',
            
            // Navigation
            'home': 'Home',
            'architecture': 'Architecture',
            'news': 'News',
            'discussion': 'Discussion',
            'about': 'About',
            'roadmap': 'Roadmap',
            
            // News sidebar
            'latest_news': 'Latest News',
            'all_news': 'All News',
            'no_news': 'Loading news...',
            
            // Footer
            'copyright': 'All rights reserved',
            'privacy': 'Privacy Policy',
            'terms': 'Terms of Service',
        }
    };
    
    window.appTranslations = translations[lang] || translations.ru;
}

function applyTranslations(lang) {
    // Применение переводов к элементам страницы
    const elements = document.querySelectorAll('[data-translate]');
    
    elements.forEach(element => {
        const key = element.dataset.translate;
        if (window.appTranslations && window.appTranslations[key]) {
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = window.appTranslations[key];
            } else {
                element.textContent = window.appTranslations[key];
            }
        }
    });
    
    // Обновление meta тегов
    document.documentElement.lang = lang;
}

// ===== ПОДКЛЮЧЕНИЕ КОШЕЛЬКА =====
function initWalletConnection() {
    // Проверка сохраненного кошелька
    const savedWallet = localStorage.getItem('z96a-wallet-address');
    const savedNickname = localStorage.getItem('z96a-user-nickname');
    const savedReputation = localStorage.getItem('z96a-user-reputation');
    
    if (savedWallet) {
        window.walletAddress = savedWallet;
        window.walletConnected = true;
        window.userProfile = {
            nickname: savedNickname || 'User',
            reputation: savedReputation ? parseInt(savedReputation) : 0
        };
        updateWalletUI();
    }
    
    // Проверка поддержки Solana
    if (typeof window.solana !== 'undefined') {
        window.solana = window.solana;
        console.log('Solana wallet detected');
    }
}

async function connectWallet() {
    try {
        showNotification('Подключение кошелька...', 'info');
        
        // Проверка поддержки Solana
        if (typeof window.solana === 'undefined') {
            throw new Error('Пожалуйста, установите кошелек Phantom или другой Solana кошелек');
        }
        
        // Запрос подключения
        const response = await window.solana.connect();
        const walletAddress = response.publicKey.toString();
        
        // Сохранение данных
        window.walletAddress = walletAddress;
        window.walletConnected = true;
        
        // Получение информации о пользователе
        const userInfo = await getUserInfo(walletAddress);
        window.userProfile = userInfo;
        
        // Сохранение в localStorage
        localStorage.setItem('z96a-wallet-address', walletAddress);
        localStorage.setItem('z96a-user-nickname', userInfo.nickname);
        localStorage.setItem('z96a-user-reputation', userInfo.reputation);
        
        // Обновление интерфейса
        updateWalletUI();
        
        // Отправка на сервер
        await registerWalletConnection(walletAddress, userInfo);
        
        showNotification('Кошелек успешно подключен!', 'success');
        
    } catch (error) {
        console.error('Wallet connection error:', error);
        showNotification(`Ошибка подключения: ${error.message}`, 'error');
    }
}

async function disconnectWallet() {
    try {
        if (window.solana && window.solana.disconnect) {
            await window.solana.disconnect();
        }
        
        // Очистка данных
        window.walletConnected = false;
        window.walletAddress = null;
        window.userProfile = null;
        
        // Очистка localStorage
        localStorage.removeItem('z96a-wallet-address');
        localStorage.removeItem('z96a-user-nickname');
        localStorage.removeItem('z96a-user-reputation');
        
        // Обновление интерфейса
        updateWalletUI();
        
        showNotification('Кошелек отключен', 'info');
        
    } catch (error) {
        console.error('Wallet disconnection error:', error);
        showNotification('Ошибка отключения кошелька', 'error');
    }
}

function updateWalletUI() {
    const connectBtn = document.getElementById('connect-wallet-btn');
    const walletConnected = document.getElementById('wallet-connected');
    const walletAddressElem = document.getElementById('wallet-address');
    const walletNicknameElem = document.getElementById('wallet-nickname');
    const walletReputationElem = document.getElementById('wallet-reputation');
    
    if (window.walletConnected && walletAddressElem && walletNicknameElem && walletReputationElem) {
        // Показать информацию о кошельке
        connectBtn.style.display = 'none';
        walletConnected.style.display = 'flex';
        
        // Обновить данные
        walletAddressElem.textContent = `${window.walletAddress.slice(0, 8)}...${window.walletAddress.slice(-6)}`;
        walletNicknameElem.textContent = window.userProfile?.nickname || 'User';
        walletReputationElem.textContent = `${window.userProfile?.reputation || 0} очков`;
        
    } else {
        // Показать кнопку подключения
        connectBtn.style.display = 'flex';
        if (walletConnected) {
            walletConnected.style.display = 'none';
        }
    }
}

async function getUserInfo(walletAddress) {
    try {
        // Запрос к API для получения информации о пользователе
        const response = await fetch(`${window.APP_CONFIG.apiBaseUrl}wallet-info/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ wallet_address: walletAddress })
        });
        
        if (response.ok) {
            const data = await response.json();
            return data;
        }
        
        // Если пользователь новый, создать профиль
        return {
            nickname: generateNickname(),
            reputation: 0,
            is_new: true
        };
        
    } catch (error) {
        console.error('Error getting user info:', error);
        return {
            nickname: generateNickname(),
            reputation: 0,
            is_new: true
        };
    }
}

async function registerWalletConnection(walletAddress, userInfo) {
    try {
        const response = await fetch(`${window.APP_CONFIG.apiBaseUrl}wallet-connect/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                wallet_address: walletAddress,
                nickname: userInfo.nickname,
                reputation: userInfo.reputation,
                timestamp: new Date().toISOString()
            })
        });
        
        return response.ok;
        
    } catch (error) {
        console.error('Error registering wallet:', error);
        return false;
    }
}

function generateNickname() {
    const adjectives = ['Cosmic', 'Stellar', 'Quantum', 'Digital', 'Neural', 'Cyber'];
    const nouns = ['Explorer', 'Pioneer', 'Voyager', 'Traveler', 'Nomad', 'Seeker'];
    const numbers = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
    
    const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const noun = nouns[Math.floor(Math.random() * nouns.length)];
    
    return `${adjective}${noun}${numbers}`;
}

// ===== УВЕДОМЛЕНИЯ =====
function initNotifications() {
    // Создание контейнера если его нет
    if (!document.getElementById('notifications')) {
        const container = document.createElement('div');
        container.id = 'notifications';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info') {
    const notifications = document.getElementById('notifications');
    if (!notifications) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: '💡'
    };
    
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${icons[type] || '💡'}</span>
            <span>${message}</span>
        </div>
    `;
    
    notifications.appendChild(notification);
    
    // Автоматическое удаление
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode === notifications) {
                notifications.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// ===== АНИМАЦИИ ПРИ ПРОКРУТКЕ =====
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Наблюдение за элементами с анимацией
    document.querySelectorAll('.animate-on-scroll').forEach(element => {
        observer.observe(element);
    });
}

// ===== МОБИЛЬНОЕ МЕНЮ =====
function initMobileMenu() {
    const mobileMenuBtn = document.createElement('button');
    mobileMenuBtn.className = 'mobile-menu-btn';
    mobileMenuBtn.innerHTML = '☰';
    mobileMenuBtn.setAttribute('aria-label', 'Меню');
    
    const headerRight = document.querySelector('.header-right');
    if (headerRight) {
        headerRight.insertBefore(mobileMenuBtn, headerRight.firstChild);
        
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    
    // Создание мобильного меню
    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';
    mobileMenu.innerHTML = `
        <div class="mobile-menu-header">
            <button class="mobile-menu-close">×</button>
        </div>
        <div class="mobile-menu-content"></div>
    `;
    
    document.body.appendChild(mobileMenu);
    
    // Закрытие по клику вне меню
    document.addEventListener('click', function(event) {
        if (!mobileMenu.contains(event.target) && event.target !== mobileMenuBtn) {
            mobileMenu.classList.remove('active');
        }
    });
    
    // Кнопка закрытия
    mobileMenu.querySelector('.mobile-menu-close').addEventListener('click', () => {
        mobileMenu.classList.remove('active');
    });
}

function toggleMobileMenu() {
    const mobileMenu = document.querySelector('.mobile-menu');
    if (!mobileMenu) return;
    
    // Заполнение контентом
    const content = mobileMenu.querySelector('.mobile-menu-content');
    if (content.innerHTML === '') {
        const nav = document.querySelector('.nav-list');
        if (nav) {
            content.innerHTML = nav.innerHTML;
        }
        
        // Добавление дополнительных элементов
        const extraContent = `
            <div class="mobile-menu-extra">
                <div class="language-switcher">
                    <button class="lang-btn active" data-lang="ru">RU</button>
                    <span class="lang-separator">/</span>
                    <button class="lang-btn" data-lang="en">EN</button>
                </div>
                <button class="wallet-connect-btn" onclick="connectWallet()">
                    👛 Подключить кошелек
                </button>
            </div>
        `;
        content.innerHTML += extraContent;
        
        // Обновление обработчиков
        content.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                switchLanguage(this.dataset.lang);
            });
        });
        
        content.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.remove('active');
            });
        });
    }
    
    mobileMenu.classList.toggle('active');
}

// ===== ПРОВЕРКА ОБНОВЛЕНИЙ =====
async function checkForUpdates() {
    try {
        const lastCheck = localStorage.getItem('z96a-last-update-check');
        const now = Date.now();
        
        // Проверять не чаще чем раз в час
        if (lastCheck && (now - parseInt(lastCheck)) < 3600000) {
            return;
        }
        
        const response = await fetch(`${window.APP_CONFIG.apiBaseUrl}check-updates/`);
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('z96a-last-update-check', now.toString());
            
            if (data.update_available) {
                showUpdateNotification(data);
            }
        }
    } catch (error) {
        console.error('Update check failed:', error);
    }
}

function showUpdateNotification(updateData) {
    const notification = document.createElement('div');
    notification.className = 'notification notification-info update-notification';
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">🔄</span>
            <span>Доступно обновление ${updateData.version}</span>
            <button class="update-dismiss">×</button>
        </div>
        <div class="update-details">
            <p>${updateData.description}</p>
            ${updateData.urgent ? '<p class="update-urgent">❗ Срочное обновление</p>' : ''}
            <div class="update-actions">
                <button class="btn btn-sm" onclick="location.reload()">Обновить сейчас</button>
                <button class="btn btn-sm btn-outline" onclick="dismissUpdate()">Напомнить позже</button>
            </div>
        </div>
    `;
    
    const notifications = document.getElementById('notifications');
    if (notifications) {
        notifications.appendChild(notification);
    }
    
    // Кнопка закрытия
    notification.querySelector('.update-dismiss').addEventListener('click', () => {
        notification.remove();
        localStorage.setItem('z96a-update-dismissed', Date.now().toString());
    });
}

function dismissUpdate() {
    const notification = document.querySelector('.update-notification');
    if (notification) {
        notification.remove();
    }
    localStorage.setItem('z96a-update-dismissed', Date.now().toString());
}

// ===== API ВЗАИМОДЕЙСТВИЕ =====
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const url = `${window.APP_CONFIG.apiBaseUrl}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Wallet-Address': window.walletAddress || ''
            },
            credentials: 'same-origin'
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error(`API request failed (${endpoint}):`, error);
        throw error;
    }
}

// ===== УТИЛИТЫ =====
function formatDate(date) {
    return new Date(date).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatNumber(number) {
    return new Intl.NumberFormat('ru-RU').format(number);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== ЭКСПОРТ ФУНКЦИЙ =====
window.connectWallet = connectWallet;
window.disconnectWallet = disconnectWallet;
window.switchLanguage = switchLanguage;
window.showNotification = showNotification;
window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;

// Проверка подключения кошелька при загрузке
window.addEventListener('load', () => {
    if (window.walletConnected) {
        updateWalletUI();
    }
});