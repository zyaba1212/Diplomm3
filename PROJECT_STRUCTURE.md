# Полная структура проекта Z96A

## Иерархия папок и файлов

```
D:\Diplom\
├── core\
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── blockchain.py
│   ├── parser.py
│   ├── context_processors.py
│   └── migrations\
│       ├── __init__.py
│       └── 0001_initial.py
├── z96a\
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── templates\
│   ├── base.html
│   ├── index.html
│   ├── architecture.html
│   ├── news.html
│   ├── discussion.html
│   ├── about.html
│   ├── roadmap.html
│   └── admin\
│       └── custom_admin.html
├── static\
│   ├── css\
│   │   ├── main.css
│   │   ├── globe.css
│   │   └── admin.css
│   ├── js\
│   │   ├── main.js
│   │   ├── globe.js
│   │   ├── wallet.js
│   │   ├── news.js
│   │   └── discussion.js
│   ├── fonts\
│   │   └── CGXYZ_PC.ttf
│   ├── images\
│   │   ├── favicon.ico
│   │   ├── equipment\
│   │   └── icons\
│   └── data\
│       └── cables.json
├── locale\
│   ├── ru\
│   │   └── LC_MESSAGES\
│   │       ├── django.po
│   │       └── django.mo
│   └── en\
│       └── LC_MESSAGES\
│           ├── django.po
│           └── django.mo
├── media\
│   └── equipment_images\
├── manage.py
├── requirements.txt
└── db.sqlite3
```

## Команды для создания структуры (PowerShell)

```powershell
# Переход в директорию проекта
cd D:\Diplom

# Создание папок
New-Item -ItemType Directory -Force -Path "locale\ru\LC_MESSAGES"
New-Item -ItemType Directory -Force -Path "locale\en\LC_MESSAGES"
New-Item -ItemType Directory -Force -Path "static\js"
New-Item -ItemType Directory -Force -Path "static\css"
New-Item -ItemType Directory -Force -Path "static\fonts"
New-Item -ItemType Directory -Force -Path "static\images\equipment"
New-Item -ItemType Directory -Force -Path "static\images\icons"
New-Item -ItemType Directory -Force -Path "static\data"
New-Item -ItemType Directory -Force -Path "templates\admin"
New-Item -ItemType Directory -Force -Path "media\equipment_images"
```

## Кодировка файлов

Все файлы должны быть сохранены в кодировке UTF-8.

## Основные компоненты

1. **Модели (core/models.py)** - База данных
2. **Представления (core/views.py)** - Логика приложения
3. **Шаблоны (templates/)** - HTML страницы
4. **Статические файлы (static/)** - CSS, JS, изображения
5. **Блокчейн (core/blockchain.py)** - Интеграция с Solana
6. **Парсер (core/parser.py)** - Парсинг новостей
7. **Админ-панель (templates/admin/)** - Кастомная админка
