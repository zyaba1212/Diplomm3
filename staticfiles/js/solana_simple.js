// Создайте файл D:\Diplom3\static\js\solana_simple.js
document.addEventListener('DOMContentLoaded', function() {
    const connectBtn = document.getElementById('connect-wallet-btn');
    const walletInfo = document.getElementById('wallet-info');
    const walletAddress = document.getElementById('wallet-address');
    const disconnectBtn = document.getElementById('disconnect-wallet-btn');
    
    // Проверяем Phantom Wallet
    const isPhantomInstalled = window.solana && window.solana.isPhantom;
    
    if (!isPhantomInstalled) {
        connectBtn.innerHTML = 'Install Phantom Wallet';
        connectBtn.onclick = () => window.open('https://phantom.app/', '_blank');
        return;
    }
    
    connectBtn.onclick = async function() {
        try {
            // Запрос на подключение
            const response = await window.solana.connect();
            const publicKey = response.publicKey.toString();
            
            // Сохраняем в localStorage для простоты
            localStorage.setItem('solana_wallet', publicKey);
            
            // Показываем информацию
            walletAddress.textContent = `${publicKey.slice(0, 4)}...${publicKey.slice(-4)}`;
            walletInfo.style.display = 'block';
            connectBtn.style.display = 'none';
            
            // Отправляем на сервер (опционально)
            fetch('/api/connect-wallet/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({wallet_address: publicKey})
            });
            
        } catch (error) {
            console.error('Connection error:', error);
            alert('Failed to connect wallet');
        }
    };
    
    disconnectBtn.onclick = function() {
        localStorage.removeItem('solana_wallet');
        walletInfo.style.display = 'none';
        connectBtn.style.display = 'block';
    };
    
    // Проверяем уже подключенный кошелёк
    const savedWallet = localStorage.getItem('solana_wallet');
    if (savedWallet) {
        walletAddress.textContent = `${savedWallet.slice(0, 4)}...${savedWallet.slice(-4)}`;
        walletInfo.style.display = 'block';
        connectBtn.style.display = 'none';
    }
    
    // Вспомогательная функция для CSRF токена
    function getCookie(name) {
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
});