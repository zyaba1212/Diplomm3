"""
URL configuration for core app
Organized with proper namespacing and API endpoints
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    CableListView, CableDetailView, NewsListView, NewsDetailView,
    DiscussionView, DiscussionDetailView, WalletView, BlockchainAPIView
)

# API Router
router = DefaultRouter()
# Add API viewsets here if needed

app_name = 'core'

urlpatterns = [
    # ==================== MAIN PAGES ====================
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('architecture/', views.architecture, name='architecture'),
    path('roadmap/', views.roadmap, name='roadmap'),
    
    # ==================== CABLES ====================
    path('cables/', CableListView.as_view(), name='cable_list'),
    path('cables/<str:cable_id>/', CableDetailView.as_view(), name='cable_detail'),
    
    # ==================== NEWS ====================
    path('news/', NewsListView.as_view(), name='news_list'),
    path('news/<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
    
    # ==================== DISCUSSIONS ====================
    path('discussion/', DiscussionView.as_view(), name='discussion_list'),
    path('discussion/<int:discussion_id>/', DiscussionDetailView.as_view(), name='discussion_detail'),
    
    # ==================== WALLET & BLOCKCHAIN ====================
    path('wallet/', WalletView.as_view(), name='wallet'),
    path('blockchain/api/', BlockchainAPIView.as_view(), name='blockchain_api'),
    
    # ==================== USER ACCOUNTS ====================
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    path('accounts/logout/', auth_views.LogoutView.as_view(
        template_name='auth/logout.html',
        next_page='/'
    ), name='logout'),
    
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html'
    ), name='password_change'),
    
    path('accounts/password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='auth/password_change_done.html'
    ), name='password_change_done'),
    
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # ==================== API ENDPOINTS ====================
    path('api/cables/', views.api_cables, name='api_cables'),
    path('api/wallet/balance/', views.api_wallet_balance, name='api_wallet_balance'),
    path('api/transaction/', views.api_create_transaction, name='api_create_transaction'),
    path('api/blockchain/', views.api_blockchain_info, name='api_blockchain_info'),
    
    # ==================== UTILITIES ====================
    path('health/', views.health_check, name='health_check'),
    
    # ==================== ADMIN ====================
    path('admin/', include('core.admin_urls')),  # Custom admin URLs
    
    # ==================== ERROR HANDLERS ====================
    path('404/', views.handler404, name='handler404'),
    path('500/', views.handler500, name='handler500'),
]

# Include API router URLs
urlpatterns += [
    path('api/v1/', include(router.urls)),
]

# Add debug URLs in development
from django.conf import settings
if settings.DEBUG:
    from django.urls import include
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]