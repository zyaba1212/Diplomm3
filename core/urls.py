from django.urls import path
from . import views
from django.views.i18n import set_language

urlpatterns = [
    path('', views.index, name='index'),
    path('architecture/', views.architecture_view, name='architecture'),
    path('news/', views.news_view, name='news'),
    path('discussion/', views.discussion_view, name='discussion'),
    path('about/', views.about_view, name='about'),
    path('roadmap/', views.roadmap_view, name='roadmap'),
    
    # API endpoints
    path('api/connect-wallet/', views.api_connect_wallet, name='api_connect_wallet'),
    path('api/network-data/', views.api_get_network_data, name='api_network_data'),
    path('api/submit-proposal/', views.api_submit_proposal, name='api_submit_proposal'),
    path('api/news/', views.api_get_news, name='api_get_news'),
    
    # Admin
    path('admin/custom/', views.admin_custom_view, name='admin_custom'),
]