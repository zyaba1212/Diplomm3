// Система комментариев Z96A

class DiscussionManager {
    constructor() {
        this.comments = [];
        this.currentFilter = 'recent';
        this.replyingTo = null;
        
        this.init();
    }
    
    async init() {
        await this.loadComments();
        this.renderComments();
        this.setupEventListeners();
    }
    
    async loadComments() {
        try {
            const response = await fetch('/api/comments/');
            const data = await response.json();
            this.comments = data.comments || [];
            console.log('Загружено комментариев:', this.comments.length);
        } catch (error) {
            console.error('Ошибка загрузки комментариев:', error);
            this.loadDemoComments();
        }
    }
    
    loadDemoComments() {
        this.comments = [
            {
                id: 1,
                user: { nickname: 'TechExplorer_2024' },
                content: 'Отличный проект! Визуализация глобальной сети выглядит впечатляюще. Особенно интересна идея с оффлайн-транзакциями.',
                created_at: new Date(Date.now() - 3600000).toISOString(),
                likes: 15,
                dislikes: 0,
                replies: []
            },
            {
                id: 2,
                user: { nickname: 'NetworkEngineer' },
                content: 'Было бы здорово добавить больше информации о типах используемого оборудования на разных уровнях сети.',
                created_at: new Date(Date.now() - 7200000).toISOString(),
                likes: 8,
                dislikes: 1,
                replies: [
                    {
                        id: 3,
                        user: { nickname: 'Gr3g' },
                        content: 'Согласен! Планируется добавить подробные спецификации для каждого элемента.',
                        created_at: new Date(Date.now() - 3600000).toISOString(),
                        likes: 5,
                        dislikes: 0
                    }
                ]
            }
        ];
    }
    
    renderComments() {
        const container = document.getElementById('commentsContainer');
        if (!container) return;
        
        const sortedComments = this.sortComments(this.comments);
        const topLevelComments = sortedComments.filter(c => !c.parent);
        
        if (topLevelComments.length === 0) {
            container.innerHTML = `
                
                    
                    Пока нет комментариев. Будьте первым!
                
            `;
            return;
        }
        
        let html = '';
        topLevelComments.forEach(comment => {
            html += this.renderComment(comment);
        });
        
        container.innerHTML = html;
        this.attachCommentEventListeners();
    }
    
    renderComment(comment, isReply = false) {
        const timeAgo = this.getTimeAgo(comment.created_at);
        const replyClass = isReply ? 'comment-reply' : '';
        
        let html = `
            
                
                    
                        
                        ${comment.user.nickname}
                    
                    ${timeAgo}
                
                ${this.escapeHtml(comment.content)}
                
                    
                         ${comment.likes || 0}
                    
                    
                         ${comment.dislikes || 0}
                    
                    
                         Ответить
                    
                
        `;
        
        // Рендерим ответы
        if (comment.replies && comment.replies.length > 0) {
            html += '';
            comment.replies.forEach(reply => {
                html += this.renderComment(reply, true);
            });
            html += '';
        }
        
        html += '';
        return html;
    }
    
    sortComments(comments) {
        switch(this.currentFilter) {
            case 'recent':
                return comments.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            case 'popular':
                return comments.sort((a, b) => (b.likes - b.dislikes) - (a.likes - a.dislikes));
            case 'oldest':
                return comments.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            default:
                return comments;
        }
    }
    
    setupEventListeners() {
        // Форма нового комментария
        const commentForm = document.getElementById('commentForm');
        if (commentForm) {
            commentForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        // Фильтры
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                if (filter) {
                    this.currentFilter = filter;
                    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    this.renderComments();
                }
            });
        });
    }
    
    attachCommentEventListeners() {
        // Лайки
        document.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const commentId = parseInt(e.currentTarget.dataset.id);
                this.likeComment(commentId);
            });
        });
        
        // Дизлайки
        document.querySelectorAll('.dislike-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const commentId = parseInt(e.currentTarget.dataset.id);
                this.dislikeComment(commentId);
            });
        });
        
        // Ответы
        document.querySelectorAll('.reply-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const commentId = parseInt(e.currentTarget.dataset.id);
                this.startReply(commentId);
            });
        });
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (!window.Z96A.wallet || !window.Z96A.wallet.isConnected()) {
            window.Z96A.utils.showNotification('Подключите кошелек для отправки комментариев', 'error');
            return;
        }
        
        const textarea = document.getElementById('commentText');
        const content = textarea.value.trim();
        
        if (!content) {
            window.Z96A.utils.showNotification('Комментарий не может быть пустым', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/comments/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet_address: window.Z96A.wallet.getPublicKey(),
                    content: content,
                    parent_id: this.replyingTo
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.Z96A.utils.showNotification('Комментарий успешно добавлен!', 'success');
                textarea.value = '';
                this.replyingTo = null;
                this.cancelReply();
                await this.loadComments();
                this.renderComments();
            } else {
                throw new Error(data.error || 'Failed to post comment');
            }
        } catch (error) {
            console.error('Error posting comment:', error);
            window.Z96A.utils.showNotification('Ошибка отправки комментария', 'error');
        }
    }
    
    async likeComment(commentId) {
        if (!window.Z96A.wallet || !window.Z96A.wallet.isConnected()) {
            window.Z96A.utils.showNotification('Подключите кошелек', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/${commentId}/like/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet_address: window.Z96A.wallet.getPublicKey()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadComments();
                this.renderComments();
            }
        } catch (error) {
            console.error('Error liking comment:', error);
        }
    }
    
    async dislikeComment(commentId) {
        if (!window.Z96A.wallet || !window.Z96A.wallet.isConnected()) {
            window.Z96A.utils.showNotification('Подключите кошелек', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/${commentId}/dislike/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wallet_address: window.Z96A.wallet.getPublicKey()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadComments();
                this.renderComments();
            }
        } catch (error) {
            console.error('Error disliking comment:', error);
        }
    }
    
    startReply(commentId) {
        this.replyingTo = commentId;
        const comment = this.findCommentById(commentId);
        
        const replyInfo = document.createElement('div');
        replyInfo.className = 'reply-info';
        replyInfo.innerHTML = `
            Ответ на комментарий ${comment.user.nickname}
            
                
            
        `;
        
        const form = document.getElementById('commentForm');
        const existing = form.querySelector('.reply-info');
        if (existing) existing.remove();
        
        form.insertBefore(replyInfo, form.firstChild);
        document.getElementById('commentText').focus();
    }
    
    cancelReply() {
        this.replyingTo = null;
        const replyInfo = document.querySelector('.reply-info');
        if (replyInfo) replyInfo.remove();
    }
    
    findCommentById(id) {
        for (let comment of this.comments) {
            if (comment.id === id) return comment;
            if (comment.replies) {
                const found = comment.replies.find(r => r.id === id);
                if (found) return found;
            }
        }
        return null;
    }
    
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'только что';
        if (seconds < 3600) return `${Math.floor(seconds / 60)} мин. назад`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} ч. назад`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)} дн. назад`;
        
        return date.toLocaleDateString('ru-RU');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Инициализация
let discussionManager = null;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('commentsContainer')) {
        discussionManager = new DiscussionManager();
        window.Z96A.discussion = discussionManager;
    }
});