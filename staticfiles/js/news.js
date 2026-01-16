// Парсер и отображение новостей

class NewsManager {
    constructor() {
        this.articles = [];
        this.currentSource = 'all';
        this.currentPage = 1;
        this.articlesPerPage = 10;
        this.isLoading = false;
        
        this.init();
    }
    
    async init() {
        await this.loadArticles();
        this.renderNewsPanel();
        this.setupEventListeners();
        this.setupAutoRefresh();
    }
    
    async loadArticles() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            const response = await fetch('/api/news/');
            const data = await response.json();
            
            this.articles = data.articles || [];
            this.renderNewsPanel();
            
        } catch (error) {
            console.error('Error loading news:', error);
            this.showError('Ошибка загрузки новостей');
            // Загружаем демо данные
            this.loadDemoArticles();
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    loadDemoArticles() {
        this.articles = [
            {
                id: 1,
                title: 'Новые технологии в инфокоммуникационных сетях',
                content_preview: 'Развитие сетей 6G и квантовой связи открывает новые возможности для обработки транзакций в условиях отсутствия соединения...',
                source: 'habr',
                url: '#',
                published_date: '2024-01-15 10:30'
            },
            {
                id: 2,
                title: 'Starlink расширяет покрытие в удаленных регионах',
                content_preview: 'Компания SpaceX продолжает запуск спутников для обеспечения интернетом труднодоступных районов планеты...',
                source: 'twitter',
                url: '#',
                published_date: '2024-01-14 14:20'
            },
            {
                id: 3,
                title: 'SUI представляет новые решения для оффлайн-транзакций',
                content_preview: 'Блокчейн платформа SUI экспериментирует с радиоволнами и Bluetooth для обработки транзакций без интернета...',
                source: 'reddit',
                url: '#',
                published_date: '2024-01-13 09:15'
            },
            {
                id: 4,
                title: 'Россия запускает спутниковую систему связи',
                content_preview: 'Новая спутниковая система предназначена для обеспечения связи в Арктике и других удаленных регионах...',
                source: 'habr',
                url: '#',
                published_date: '2024-01-12 16:45'
            },
            {
                id: 5,
                title: 'ИИ в сетевой инфраструктуре',
                content_preview: 'Искусственный интеллект помогает оптимизировать маршрутизацию и повышать отказоустойчивость сетей...',
                source: 'twitter',
                url: '#',
                published_date: '2024-01-11 11:30'
            }
        ];
    }
    
    renderNewsPanel() {
        const newsContent = document.getElementById('newsContent');
        if (!newsContent) return;
        
        const filteredArticles = this.filterArticles();
        const paginatedArticles = this.paginateArticles(filteredArticles);
        
        if (paginatedArticles.length === 0) {
            newsContent.innerHTML = `
                <div class="no-news">
                    <i class="fas fa-newspaper"></i>
                    <p>Новости не найдены</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        paginatedArticles.forEach(article => {
            const sourceIcon = this.getSourceIcon(article.source);
            const sourceName = this.getSourceName(article.source);
            const formattedDate = this.formatDate(article.published_date);
            
            html += `
                <div class="news-item" data-id="${article.id}">
                    <div class="news-source">
                        <i class="${sourceIcon}"></i> ${sourceName}
                        <span class="news-date">${formattedDate}</span>
                    </div>
                    <div class="news-title">${article.title}</div>
                    <div class="news-preview">${article.content_preview}</div>
                    <div class="news-actions">
                        <a href="${article.url}" target="_blank" class="read-more">
                            Читать полностью <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            `;
        });
        
        // Добавляем пагинацию если нужно
        if (filteredArticles.length > this.articlesPerPage) {
            const totalPages = Math.ceil(filteredArticles.length / this.articlesPerPage);
            html += this.renderPagination(totalPages);
        }
        
        newsContent.innerHTML = html;
        
        // Добавляем обработчики событий
        this.addArticleEventListeners();
    }
    
    filterArticles() {
        if (this.currentSource === 'all') {
            return this.articles;
        }
        
        return this.articles.filter(article => article.source === this.currentSource);
    }
    
    paginateArticles(articles) {
        const startIndex = (this.currentPage - 1) * this.articlesPerPage;
        const endIndex = startIndex + this.articlesPerPage;
        return articles.slice(startIndex, endIndex);
    }
    
    renderPagination(totalPages) {
        let html = '<div class="news-pagination">';
        
        if (this.currentPage > 1) {
            html += `
                <button class="page-btn prev-btn" data-page="${this.currentPage - 1}">
                    <i class="fas fa-chevron-left"></i> Назад
                </button>
            `;
        }
        
        // Показываем номера страниц
        for (let i = 1; i <= totalPages; i++) {
            if (i === this.currentPage) {
                html += `<span class="page-number active">${i}</span>`;
            } else if (
                i === 1 || 
                i === totalPages || 
                (i >= this.currentPage - 1 && i <= this.currentPage + 1)
            ) {
                html += `<button class="page-number" data-page="${i}">${i}</button>`;
            } else if (i === this.currentPage - 2 || i === this.currentPage + 2) {
                html += `<span class="page-dots">...</span>`;
            }
        }
        
        if (this.currentPage < totalPages) {
            html += `
                <button class="page-btn next-btn" data-page="${this.currentPage + 1}">
                    Далее <i class="fas fa-chevron-right"></i>
                </button>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    getSourceIcon(source) {
        const icons = {
            'twitter': 'fab fa-twitter',
            'reddit': 'fab fa-reddit',
            'habr': 'fas fa-code',
            'manual': 'fas fa-edit'
        };
        return icons[source] || 'fas fa-newspaper';
    }
    
    getSourceName(source) {
        const names = {
            'twitter': 'Twitter/X',
            'reddit': 'Reddit',
            'habr': 'Habr',
            'manual': 'Ручной ввод'
        };
        return names[source] || source;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        
        if (diffHours < 24) {
            return `${diffHours} ч. назад`;
        } else if (diffHours < 48) {
            return 'Вчера';
        } else {
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }
    }
    
    addArticleEventListeners() {
        // Обработка кликов по новостям
        document.querySelectorAll('.news-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.read-more') && !e.target.closest('.news-actions')) {
                    const articleId = item.getAttribute('data-id');
                    this.showArticleDetails(articleId);
                }
            });
        });
        
        // Обработка пагинации
        document.querySelectorAll('.page-number, .page-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (btn.classList.contains('page-number')) {
                    const page = parseInt(btn.getAttribute('data-page'));
                    if (page && page !== this.currentPage) {
                        this.currentPage = page;
                        this.renderNewsPanel();
                        this.scrollToNewsTop();
                    }
                }
                
                if (btn.classList.contains('prev-btn')) {
                    this.currentPage--;
                    this.renderNewsPanel();
                    this.scrollToNewsTop();
                }
                
                if (btn.classList.contains('next-btn')) {
                    this.currentPage++;
                    this.renderNewsPanel();
                    this.scrollToNewsTop();
                }
            });
        });
    }
    
    showArticleDetails(articleId) {
        const article = this.articles.find(a => a.id == articleId);
        if (!article) return;
        
        const modal = document.createElement('div');
        modal.className = 'article-modal';
        
        const sourceIcon = this.getSourceIcon(article.source);
        const sourceName = this.getSourceName(article.source);
        const formattedDate = this.formatDate(article.published_date);
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="article-header">
                    <div class="article-source">
                        <i class="${sourceIcon}"></i> ${sourceName}
                        <span class="article-date">${formattedDate}</span>
                    </div>
                    <button class="close-article">&times;</button>
                </div>
                <div class="article-title">${article.title}</div>
                <div class="article-content">
                    <p>${article.content_preview}</p>
                    <p>Для полного прочтения статьи перейдите по ссылке ниже:</p>
                </div>
                <div class="article-footer">
                    <a href="${article.url}" target="_blank" class="original-link">
                        <i class="fas fa-external-link-alt"></i> Перейти к оригинальной статье
                    </a>
                    <button class="share-article" data-title="${article.title}" data-url="${article.url}">
                        <i class="fas fa-share-alt"></i> Поделиться
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Стили для модального окна статьи
        const styles = `
        .article-modal {
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
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .article-modal .modal-content {
            background: linear-gradient(135deg, #1b1523 0%, #0a1a2d 100%);
            padding: 2rem;
            border-radius: 16px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(108, 99, 255, 0.3);
            box-shadow: 0 0 30px rgba(108, 99, 255, 0.2);
        }
        
        .article-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .article-source {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            color: #00ff9d;
            font-size: 0.9rem;
        }
        
        .article-source i {
            font-size: 1.2rem;
        }
        
        .article-date {
            color: #aaa;
        }
        
        .close-article {
            background: none;
            border: none;
            color: #aaa;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.5rem;
            line-height: 1;
            transition: color 0.3s ease;
        }
        
        .close-article:hover {
            color: white;
        }
        
        .article-title {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 1.5rem;
            color: white;
            line-height: 1.3;
        }
        
        .article-content {
            margin-bottom: 2rem;
            line-height: 1.6;
            color: #ddd;
        }
        
        .article-content p {
            margin-bottom: 1rem;
        }
        
        .article-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }
        
        .original-link {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.8rem 1.2rem;
            background: rgba(108, 99, 255, 0.2);
            border: 1px solid rgba(108, 99, 255, 0.3);
            border-radius: 8px;
            color: white;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .original-link:hover {
            background: rgba(108, 99, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .share-article {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.8rem 1.2rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.3s ease;
        }
        
        .share-article:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        `;
        
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
        
        // Закрытие модального окна
        modal.querySelector('.close-article').addEventListener('click', () => {
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
        
        // Кнопка "Поделиться"
        modal.querySelector('.share-article').addEventListener('click', (e) => {
            const title = e.target.getAttribute('data-title') || article.title;
            const url = e.target.getAttribute('data-url') || article.url;
            this.shareArticle(title, url);
        });
    }
    
    shareArticle(title, url) {
        if (navigator.share) {
            navigator.share({
                title: title,
                text: 'Посмотрите эту статью на Z96A:',
                url: url
            }).then(() => {
                window.Z96A.utils.showNotification('Статья успешно отправлена', 'success');
            }).catch(error => {
                console.log('Error sharing:', error);
            });
        } else {
            // Fallback для браузеров без поддержки Web Share API
            navigator.clipboard.writeText(`${title}\n${url}`).then(() => {
                window.Z96A.utils.showNotification('Ссылка скопирована в буфер обмена', 'success');
            });
        }
    }
    
    setupEventListeners() {
        // Фильтрация по источникам
        document.querySelectorAll('.source-filter').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const source = e.target.getAttribute('data-source');
                if (source && source !== this.currentSource) {
                    this.currentSource = source;
                    this.currentPage = 1;
                    this.renderNewsPanel();
                    
                    // Обновляем активную кнопку
                    document.querySelectorAll('.source-filter').forEach(b => {
                        b.classList.remove('active');
                    });
                    e.target.classList.add('active');
                }
            });
        });
        
        // Кнопка обновления новостей
        document.getElementById('refreshNews')?.addEventListener('click', () => {
            this.loadArticles();
        });
        
        // Поиск по новостям
        const searchInput = document.getElementById('newsSearch');
        if (searchInput) {
            const debouncedSearch = window.Z96A.utils.debounce((query) => {
                this.searchArticles(query);
            }, 300);
            
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }
    }
    
    searchArticles(query) {
        if (!query.trim()) {
            this.renderNewsPanel();
            return;
        }
        
        const searchLower = query.toLowerCase();
        const filtered = this.articles.filter(article => 
            article.title.toLowerCase().includes(searchLower) ||
            article.content_preview.toLowerCase().includes(searchLower)
        );
        
        this.renderSearchResults(filtered);
    }
    
    renderSearchResults(results) {
        const newsContent = document.getElementById('newsContent');
        if (!newsContent) return;
        
        if (results.length === 0) {
            newsContent.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>По вашему запросу ничего не найдено</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="search-header">
                <h4>Результаты поиска: ${results.length} статей</h4>
            </div>
        `;
        
        results.forEach(article => {
            const sourceIcon = this.getSourceIcon(article.source);
            const sourceName = this.getSourceName(article.source);
            const formattedDate = this.formatDate(article.published_date);
            
            html += `
                <div class="news-item" data-id="${article.id}">
                    <div class="news-source">
                        <i class="${sourceIcon}"></i> ${sourceName}
                        <span class="news-date">${formattedDate}</span>
                    </div>
                    <div class="news-title">${article.title}</div>
                    <div class="news-preview">${article.content_preview}</div>
                    <div class="news-actions">
                        <a href="${article.url}" target="_blank" class="read-more">
                            Читать полностью <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            `;
        });
        
        newsContent.innerHTML = html;
        this.addArticleEventListeners();
    }
    
    setupAutoRefresh() {
        // Автоматическое обновление новостей каждые 5 минут
        setInterval(() => {
            this.loadArticles();
        }, 5 * 60 * 1000);
    }
    
    showLoadingIndicator() {
        const newsContent = document.getElementById('newsContent');
        if (!newsContent) return;
        
        newsContent.innerHTML = `
            <div class="loading-news">
                <div class="spinner"></div>
                <p>Загрузка новостей...</p>
            </div>
        `;
        
        // Добавляем стили для спиннера
        const styles = `
        .loading-news {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(108, 99, 255, 0.3);
            border-top: 3px solid #6c63ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .loading-news p {
            color: #aaa;
        }
        `;
        
        const styleEl = document.createElement('style');
        styleEl.textContent = styles;
        document.head.appendChild(styleEl);
        
        // Сохраняем ссылку для удаления
        this.loadingStyle = styleEl;
    }
    
    hideLoadingIndicator() {
        if (this.loadingStyle) {
            this.loadingStyle.remove();
            this.loadingStyle = null;
        }
    }
    
    showError(message) {
        const newsContent = document.getElementById('newsContent');
        if (!newsContent) return;
        
        newsContent.innerHTML = `
            <div class="news-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button class="retry-btn" onclick="newsManager.loadArticles()">
                    Попробовать снова
                </button>
            </div>
        `;
    }
    
    scrollToNewsTop() {
        const newsContent = document.getElementById('newsContent');
        if (newsContent) {
            newsContent.scrollTop = 0;
        }
    }
}

// Глобальный экземпляр менеджера новостей
let newsManager = null;

// Функция для загрузки новостей с главной страницы
function loadNewsArticles() {
    if (!newsManager) {
        newsManager = new NewsManager();
        window.Z96A.news = newsManager;
    } else {
        newsManager.loadArticles();
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем только если есть контейнер новостей
    if (document.getElementById('newsContent')) {
        newsManager = new NewsManager();
        window.Z96A.news = newsManager;
    }
    
    // Добавляем кнопку обновления новостей если ее нет
    const newsHeader = document.querySelector('.news-header');
    if (newsHeader && !document.getElementById('refreshNews')) {
        const refreshBtn = document.createElement('button');
        refreshBtn.id = 'refreshNews';
        refreshBtn.className = 'refresh-btn';
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshBtn.title = 'Обновить новости';
        newsHeader.appendChild(refreshBtn);
        
        refreshBtn.addEventListener('click', () => {
            if (newsManager) {
                newsManager.loadArticles();
            }
        });
    }
    
    // Добавляем фильтры источников если их нет
    const newsPanel = document.getElementById('newsPanel');
    if (newsPanel && !document.querySelector('.source-filters')) {
        const filtersHtml = `
            <div class="source-filters">
                <button class="source-filter active" data-source="all">Все</button>
                <button class="source-filter" data-source="twitter">Twitter</button>
                <button class="source-filter" data-source="reddit">Reddit</button>
                <button class="source-filter" data-source="habr">Habr</button>
            </div>
        `;
        
        const newsContent = document.getElementById('newsContent');
        if (newsContent) {
            newsContent.insertAdjacentHTML('afterbegin', filtersHtml);
        }
    }
    
    // Добавляем поле поиска если его нет
    if (newsPanel && !document.getElementById('newsSearch')) {
        const searchHtml = `
            <div class="news-search">
                <input type="text" id="newsSearch" placeholder="Поиск новостей...">
                <i class="fas fa-search"></i>
            </div>
        `;
        
        const newsContent = document.getElementById('newsContent');
        if (newsContent) {
            const filters = newsContent.querySelector('.source-filters');
            if (filters) {
                filters.insertAdjacentHTML('afterend', searchHtml);
            } else {
                newsContent.insertAdjacentHTML('afterbegin', searchHtml);
            }
        }
    }
});