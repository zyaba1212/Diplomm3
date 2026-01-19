from django.urls import path 
from core.views import home, network_architecture, news, discussion, about, roadmap, connect_wallet 
 
urlpatterns = [ 
    path('', home, name='home'), 
    path('network/', network_architecture, name='network_architecture'), 
    path('news/', news, name='news'), 
    path('discussion/', discussion, name='discussion'), 
    path('about/', about, name='about'), 
    path('roadmap/', roadmap, name='roadmap'), 
    path('api/wallet/connect/', connect_wallet, name='connect_wallet'), 
] 
