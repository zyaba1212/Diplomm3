from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('network/', views.network_architecture, name='network_architecture'),
    path('news/', views.news, name='news'),
    path('discussion/', views.discussion, name='discussion'),
    path('about/', views.about, name='about'),
    path('roadmap/', views.roadmap, name='roadmap'),
    path('api/wallet/connect/', views.connect_wallet, name='connect_wallet'),
    path('api/node/<int:node_id>/', views.get_node_details, name='node_details'),
]