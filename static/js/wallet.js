// Простой wallet.js для теста 
document.addEventListener('DOMContentLoaded', function() { 
    console.log('Wallet script loaded'); 
    const connectBtn = document.getElementById('connect-wallet-btn'); 
    const walletInfo = document.getElementById('wallet-info'); 
    const walletAddress = document.getElementById('wallet-address'); 
    const disconnectBtn = document.getElementById('disconnect-wallet-btn'); 
Режим вывода команд на экран (ECHO) включен.
    if (!connectBtn) { 
        console.log('Кнопка кошелька не найдена, возможно не на этой странице'); 
        return; 
    } 
Режим вывода команд на экран (ECHO) включен.
    const testAddress = 'DmZh8QVRQz1PwGkUqLpQq7wqJzKqJqJqJqJqJqJqJqJqJqJqJqJqJqJq'; 
Режим вывода команд на экран (ECHO) включен.
    connectBtn.addEventListener('click', function() { 
        console.log('Кнопка кошелька нажата'); 
        walletAddress.textContent = testAddress.slice(0, 8) + '...' + testAddress.slice(-8); 
        connectBtn.style.display = 'none'; 
        walletInfo.style.display = 'flex'; 
        localStorage.setItem('z96a_wallet', testAddress); 
        alert('Кошелёк подключен (тестовый режим)'); 
    }); 
Режим вывода команд на экран (ECHO) включен.
    if (disconnectBtn) { 
        disconnectBtn.addEventListener('click', function() { 
            localStorage.removeItem('z96a_wallet'); 
            connectBtn.style.display = 'block'; 
            walletInfo.style.display = 'none'; 
        }); 
    } 
Режим вывода команд на экран (ECHO) включен.
    const savedWallet = localStorage.getItem('z96a_wallet'); 
    if (savedWallet) { 
        walletAddress.textContent = savedWallet.slice(0, 8) + '...' + savedWallet.slice(-8); 
        connectBtn.style.display = 'none'; 
        walletInfo.style.display = 'flex'; 
    } 
}); 
