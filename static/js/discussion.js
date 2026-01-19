// D:\Diplom\static\js\discussion.js - ПОЛНЫЙ КОД

document.addEventListener('DOMContentLoaded', function() {
    console.log('Discussion JS loaded');
    
    // Элементы
    const messageList = document.getElementById('message-list');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const usernameInput = document.getElementById('username-input');
    const connectBtn = document.getElementById('connect-btn');
    
    // WebSocket
    let socket = null;
    let username = localStorage.getItem('discussion_username') || `User${Math.floor(Math.random() * 1000)}`;
    
    // Установка имени пользователя
    if (usernameInput) {
        usernameInput.value = username;
        usernameInput.addEventListener('change', function() {
            username = this.value.trim() || username;
            localStorage.setItem('discussion_username', username);
        });
    }
    
    // Функция подключения WebSocket
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/discussion/`;
        
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function() {
            console.log('WebSocket connected');
            if (connectBtn) connectBtn.disabled = true;
            addSystemMessage('Подключено к чату');
            
            // Отправляем информацию о пользователе
            socket.send(JSON.stringify({
                type: 'join',
                username: username
            }));
        };
        
        socket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };
        
        socket.onclose = function() {
            console.log('WebSocket disconnected');
            if (connectBtn) connectBtn.disabled = false;
            addSystemMessage('Отключено от чата');
            
            // Переподключение через 3 секунды
            setTimeout(connectWebSocket, 3000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    }
    
    // Обработка сообщений WebSocket
    function handleWebSocketMessage(data) {
        switch(data.type) {
            case 'message':
                addMessage(data.username, data.message, data.timestamp);
                break;
            case 'user_join':
                addSystemMessage(`${data.username} присоединился к чату`);
                break;
            case 'user_leave':
                addSystemMessage(`${data.username} покинул чат`);
                break;
            case 'history':
                if (Array.isArray(data.messages)) {
                    data.messages.forEach(msg => {
                        addMessage(msg.username, msg.message, msg.timestamp, true);
                    });
                }
                break;
            case 'error':
                addSystemMessage(`Ошибка: ${data.message}`);
                break;
        }
    }
    
    // Добавление сообщения пользователя
    function addMessage(user, text, timestamp, isHistory = false) {
        if (!messageList) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${user === username ? 'own-message' : ''}`;
        
        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong class="username">${user}</strong>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-text">${escapeHtml(text)}</div>
        `;
        
        if (isHistory) {
            messageList.insertBefore(messageDiv, messageList.firstChild);
        } else {
            messageList.appendChild(messageDiv);
            messageList.scrollTop = messageList.scrollHeight;
        }
    }
    
    // Добавление системного сообщения
    function addSystemMessage(text) {
        if (!messageList) return;
        
        const systemDiv = document.createElement('div');
        systemDiv.className = 'system-message';
        systemDiv.textContent = text;
        messageList.appendChild(systemDiv);
        messageList.scrollTop = messageList.scrollHeight;
    }
    
    // Отправка сообщения
    function sendMessage(text) {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            addSystemMessage('Нет подключения к чату');
            return;
        }
        
        if (!text.trim()) return;
        
        const messageData = {
            type: 'message',
            username: username,
            message: text,
            timestamp: new Date().toISOString()
        };
        
        socket.send(JSON.stringify(messageData));
        
        // Очищаем поле ввода
        if (messageInput) {
            messageInput.value = '';
        }
    }
    
    // Экранирование HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Обработка формы
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (messageInput && messageInput.value.trim()) {
                sendMessage(messageInput.value.trim());
            }
        });
    }
    
    // Обработка кнопки подключения
    if (connectBtn) {
        connectBtn.addEventListener('click', function() {
            if (!socket || socket.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            }
        });
    }
    
    // Горячие клавиши
    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.value.trim()) {
                    sendMessage(this.value.trim());
                }
            }
        });
    }
    
    // Автоподключение при загрузке
    connectWebSocket();
    
    // Загрузка истории сообщений
    function loadMessageHistory() {
        fetch('/api/discussion/history/')
            .then(response => response.json())
            .then(data => {
                if (data.messages && Array.isArray(data.messages)) {
                    data.messages.forEach(msg => {
                        addMessage(msg.username, msg.message, msg.timestamp, true);
                    });
                }
            })
            .catch(error => console.error('Error loading history:', error));
    }
    
    // Загружаем историю через 1 секунду после подключения
    setTimeout(loadMessageHistory, 1000);
});