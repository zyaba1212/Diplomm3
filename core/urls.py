from django.urls import path
from . import views

urlpatterns = [
    # Страницы
    path('', views.index, name='index'),
    path('architecture/', views.architecture_view, name='architecture'),
    path('news/', views.news_view, name='news'),
    path('discussion/', views.discussion_view, name='discussion'),
    path('about/', views.about_view, name='about'),
    path('roadmap/', views.roadmap_view, name='roadmap'),
    
    # API endpoints
    path('api/connect-wallet/', views.api_connect_wallet, name='api_connect_wallet'),
    path('api/network-data/', views.api_get_network_data, name='api_network_data'),
    path('api/cables/', views.api_get_cables, name='api_cables'),
    path('api/hierarchy/', views.api_get_hierarchy, name='api_hierarchy'),
    path('api/comments/', views.api_get_comments, name='api_get_comments'),
    path('api/comments/post/', views.api_post_comment, name='api_post_comment'),
    path('api/comments//like/', views.api_like_comment, name='api_like_comment'),
    path('api/comments//dislike/', views.api_dislike_comment, name='api_dislike_comment'),
    path('api/submit-proposal/', views.api_submit_proposal, name='api_submit_proposal'),
    path('api/news/', views.api_get_news, name='api_get_news'),
]