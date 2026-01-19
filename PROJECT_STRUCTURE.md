# Z96A Network Project Structure

## Overview
Modern Django project for submarine cable visualization with blockchain integration.

## Directory Structure
z96a-project/
├── .env.example # Environment template
├── .gitignore # Git ignore rules
├── requirements.txt # Python dependencies
├── manage.py # Django management
├── db.sqlite3 # Database (dev)
├── README.md # Project documentation
├── docker-compose.yml # Docker orchestration
│
├── core/ # Main Django app
│ ├── init.py
│ ├── admin.py # Admin configuration
│ ├── apps.py # App config
│ ├── models.py # Database models
│ ├── views.py # View functions
│ ├── urls.py # URL routing
│ ├── blockchain.py # Blockchain implementation
│ ├── parser.py # Data parsing utilities
│ ├── context_processors.py
│ │
│ ├── migrations/ # Database migrations
│ ├── services/ # Business logic layer
│ │ ├── init.py
│ │ ├── blockchain_service.py
│ │ ├── cable_service.py
│ │ └── user_service.py
│ │
│ ├── utils/ # Utility functions
│ │ ├── init.py
│ │ ├── validators.py
│ │ └── helpers.py
│ │
│ └── tests/ # Test suite
│ ├── init.py
│ ├── test_models.py
│ ├── test_views.py
│ └── test_blockchain.py
│
├── templates/ # HTML templates
│ ├── base.html
│ ├── index.html
│ ├── about.html
│ ├── architecture.html
│ ├── discussion.html
│ ├── news.html
│ ├── roadmap.html
│ └── admin/
│ └── custom_admin.html
│
├── static/ # Static assets
│ ├── css/
│ │ ├── main.css
│ │ ├── globe.css
│ │ └── admin.css
│ │
│ ├── js/
│ │ ├── main.js
│ │ ├── globe.js
│ │ ├── wallet.js
│ │ ├── news.js
│ │ └── discussion.js
│ │
│ ├── data/
│ │ └── cables.json
│ │
│ ├── images/
│ │ ├── favicon.ico
│ │ ├── earth_texture.jpg
│ │ └── icons/
│ │
│ └── fonts/
│ └── CGXYZ_PC.ttf
│
├── media/ # User uploaded files
│ └── equipment_images/
│
├── logs/ # Application logs
│ ├── django.log
│ └── blockchain.log
│
└── z96a/ # Project configuration
├── init.py
├── settings.py # Main settings
├── urls.py # Root URLs
├── wsgi.py # WSGI config
└── asgi.py # ASGI config

## Technology Stack

### Backend
- **Framework**: Django 5.0
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Cache**: Redis
- **Blockchain**: Custom implementation with RSA signatures
- **API**: Django REST Framework

### Frontend
- **3D Visualization**: Three.js
- **Styling**: CSS3 with Flexbox/Grid
- **Interactivity**: Vanilla JavaScript + WebSocket
- **Responsive Design**: Mobile-first approach

### DevOps
- **Containerization**: Docker + Docker Compose
- **Environment**: Python 3.11+
- **CI/CD**: GitHub Actions (optional)
- **Monitoring**: Custom logging + Sentry

## Security Features
- Environment-based configuration
- CSRF protection on all forms
- SQL injection prevention
- XSS protection
- Rate limiting
- Secure session management

## Deployment
See `docker-compose.yml` for containerized deployment or use traditional WSGI deployment with Gunicorn.

## Development
1. Copy `.env.example` to `.env`
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start server: `python manage.py runserver`

## Testing
Run tests with: `python manage.py test core`