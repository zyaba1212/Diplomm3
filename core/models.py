from django.db import models
from django.contrib.auth.models import User
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=100, unique=True)
    nickname = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nickname} ({self.wallet_address[:10]}...)"

class BlockchainTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('wallet_connect', 'Подключение кошелька'),
        ('equipment_proposal', 'Предложение оборудования'),
        ('comment', 'Комментарий'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    solana_tx_hash = models.CharField(max_length=100, unique=True)
    data = models.JSONField(default=dict)  # Stores transaction details
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.solana_tx_hash[:15]}..."

class NetworkElement(models.Model):
    ELEMENT_TYPES = [
        ('satellite', 'Спутник'),
        ('ground_station', 'Наземная станция'),
        ('router', 'Маршрутизатор'),
        ('switch', 'Коммутатор'),
        ('server', 'Сервер'),
        ('cable', 'Кабель'),
        ('user_device', 'Пользовательское устройство'),
    ]
    
    NETWORK_TYPES = [
        ('existing', 'Существующая сеть'),
        ('proposed', 'Предложенное решение'),
    ]
    
    element_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPES)
    network_type = models.CharField(max_length=20, choices=NETWORK_TYPES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(default=0)  # For 3D positioning
    description = models.TextField()
    image_url = models.URLField(max_length=500, blank=True, null=True)
    specifications = models.JSONField(default=dict)
    proposed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    proposal_tx = models.ForeignKey(BlockchainTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_element_type_display()})"

class NetworkConnection(models.Model):
    from_element = models.ForeignKey(NetworkElement, related_name='connections_from', on_delete=models.CASCADE)
    to_element = models.ForeignKey(NetworkElement, related_name='connections_to', on_delete=models.CASCADE)
    connection_type = models.CharField(max_length=50)
    bandwidth = models.CharField(max_length=50, blank=True)
    latency = models.CharField(max_length=50, blank=True)
    
    class Meta:
        unique_together = ['from_element', 'to_element']
    
    def __str__(self):
        return f"{self.from_element.name} -> {self.to_element.name}"

class NewsArticle(models.Model):
    SOURCE_CHOICES = [
        ('twitter', 'Twitter/X'),
        ('reddit', 'Reddit'),
        ('habr', 'Habr'),
        ('manual', 'Manual'),
    ]
    
    title = models.CharField(max_length=500)
    content = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    url = models.URLField(max_length=500)
    published_date = models.DateTimeField()
    parsed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title[:50]}... ({self.source})"

class Comment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    def __str__(self):
        return f"Comment by {self.user.nickname}: {self.content[:30]}..."

class Proposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('implemented', 'Внедрено'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    element = models.ForeignKey(NetworkElement, on_delete=models.CASCADE, null=True, blank=True)
    proposal_type = models.CharField(max_length=50)
    description = models.TextField()
    specifications = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Proposal #{self.id} by {self.user.nickname}"