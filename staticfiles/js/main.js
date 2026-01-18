// Основные функции сайта Z96A

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initLanguageSwitcher();
    initMobileMenu();
    initSmoothScrolling();
    checkWalletConnection();
});

// Инициализация переключателя языка
function initLanguageSwitcher() {
    const languageForms = document.querySelectorAll('.language-form');
    languageForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            localStorage.setItem('preferred_language', this.language.value);
        });
    });
}

// Инициализация мобильного меню
function initMobileMenu() {
    const menuToggle = document.getElementById('mobileMenuToggle');
    const mainNav = document.querySelector('.main-nav');
    
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', function() {
            mainNav.classList.toggle('mobile-active');
            this.classList.toggle('active');
        });
    }
}

// Плавная прокрутка
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// Проверка подключения кошелька
function checkWalletConnection() {
    const connectedWallet = localStorage.getItem('z96a_wallet_address');
    const userNickname = localStorage.getItem('z96a_user_nickname');
    
    if (connectedWallet && userNickname) {
        showUserInfo(connectedWallet, userNickname);
    }
}

// Показать информацию о пользователе
function showUserInfo(walletAddress, nickname) {
    const walletBtn = document.getElementById('connectWalletBtn');
    const userInfo = document.getElementById('userInfo');
    const userNickname = document.getElementById('userNickname');
    
    if (walletBtn && userInfo && userNickname) {
        walletBtn.style.display = 'none';
        userInfo.style.display = 'flex';
        userNickname.textContent = nickname;
    }
}

// Скрыть информацию о пользователе
function hideUserInfo() {
    const walletBtn = document.getElementById('connectWalletBtn');
    const userInfo = document.getElementById('userInfo');
    
    if (walletBtn && userInfo) {
        walletBtn.style.display = 'flex';
        userInfo.style.display = 'none';
    }
}

// Отображение уведомлений
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Закрытие по клику
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Автоматическое закрытие
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

// Форматирование адреса кошелька
function formatWalletAddress(address) {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

// Загрузка данных с API
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        showNotification('Ошибка загрузки данных', 'error');
        throw error;
    }
}

// Стили для уведомлений (динамически добавляем в head)
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    background: rgba(30, 30, 46, 0.95);
    border: 1px solid rgba(108, 99, 255, 0.3);
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 300px;
    max-width: 400px;
    transform: translateX(120%);
    transition: transform 0.3s ease;
    z-index: 9999;
    backdrop-filter: blur(10px);
}

.notification.show {
    transform: translateX(0);
}

.notification-success {
    border-left: 4px solid #00ff9d;
}

.notification-error {
    border-left: 4px solid #ff4757;
}

.notification-info {
    border-left: 4px solid #6c63ff;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    flex: 1;
}

.notification-close {
    background: none;
    border: none;
    color: #aaa;
    font-size: 1.2rem;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background-color 0.3s ease;
}

.notification-close:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
`;

// Добавляем стили уведомлений в head
if (!document.querySelector('#notification-styles')) {
    const styleEl = document.createElement('style');
    styleEl.id = 'notification-styles';
    styleEl.textContent = notificationStyles;
    document.head.appendChild(styleEl);
}

// Утилита для работы с датами
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Обработка ошибок формы
function handleFormError(formElement, error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${error}</span>
    `;
    
    formElement.insertBefore(errorDiv, formElement.firstChild);
    
    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        if (errorDiv.parentNode === formElement) {
            errorDiv.remove();
        }
    }, 5000);
}

// Тема оформления (темная/светлая)
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    const currentTheme = localStorage.getItem('z96a_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    themeToggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const newTheme = current === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('z96a_theme', newTheme);
        
        showNotification(`Тема изменена на ${newTheme === 'dark' ? 'тёмную' : 'светлую'}`);
    });
}

// Инициализация счетчиков
function initCounters() {
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const increment = target / 100;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                counter.textContent = Math.ceil(current);
                setTimeout(updateCounter, 20);
            } else {
                counter.textContent = target;
            }
        };
        
        // Запускаем при появлении в viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success');
    }).catch(err => {
        console.error('Copy failed:', err);
        showNotification('Ошибка копирования', 'error');
    });
}

// Дебаунс для оптимизации
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

// Проверка поддержки WebGL
function checkWebGLSupport() {
    try {
        const canvas = document.createElement('canvas');
        return !!(window.WebGLRenderingContext && 
            (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch (e) {
        return false;
    }
}

// Если WebGL не поддерживается
if (!checkWebGLSupport()) {
    document.addEventListener('DOMContentLoaded', function() {
        showNotification('Ваш браузер не поддерживает WebGL. 3D визуализация может не работать.', 'error');
    });
}

// Экспорт функций для использования в других файлах
window.Z96A = window.Z96A || {};
window.Z96A.utils = {
    showNotification,
    formatWalletAddress,
    formatDate,
    copyToClipboard,
    debounce
};