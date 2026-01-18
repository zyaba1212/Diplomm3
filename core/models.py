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
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class BlockchainTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('wallet_connect', 'Подключение кошелька'),
        ('equipment_proposal', 'Предложение оборудования'),
        ('comment', 'Комментарий'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    solana_tx_hash = models.CharField(max_length=100, unique=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.solana_tx_hash[:15]}..."
    
    class Meta:
        verbose_name = "Блокчейн транзакция"
        verbose_name_plural = "Блокчейн транзакции"


# НОВЫЕ МОДЕЛИ ДЛЯ ИЕРАРХИИ

class Region(models.Model):
    """Континент/Регион"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)  # NA, EU, ASIA и т.д.
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"


class Country(models.Model):
    """Страна"""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='countries')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)  # ISO код
    capital = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"


class City(models.Model):
    """Город - узел сети"""
    CITY_TYPES = [
        ('capital', 'Столица'),
        ('major', 'Крупный город'),
        ('hub', 'Сетевой хаб'),
        ('regional', 'Региональный центр'),
    ]
    
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100)
    city_type = models.CharField(max_length=20, choices=CITY_TYPES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    population = models.IntegerField(blank=True, null=True)
    is_hub = models.BooleanField(default=False)  # Является ли ключевым узлом
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name}, {self.country.name}"
    
    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        unique_together = ['name', 'country']


# МОДЕЛЬ ДЛЯ КАБЕЛЕЙ

class Cable(models.Model):
    """Подводный или наземный кабель"""
    CABLE_TYPES = [
        ('submarine', 'Подводный'),
        ('terrestrial', 'Наземный'),
    ]
    
    cable_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    cable_type = models.CharField(max_length=20, choices=CABLE_TYPES)
    capacity = models.CharField(max_length=50, blank=True)  # "160 Tbps"
    length = models.CharField(max_length=50, blank=True)  # "6600 km"
    owners = models.JSONField(default=list)  # Список владельцев
    year = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#1e90ff')  # HEX цвет
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.cable_type})"
    
    class Meta:
        verbose_name = "Кабель"
        verbose_name_plural = "Кабели"


class CableRoute(models.Model):
    """Маршрут кабеля (промежуточные точки)"""
    cable = models.ForeignKey(Cable, on_delete=models.CASCADE, related_name='route')
    order = models.IntegerField()  # Порядок точки в маршруте
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_name = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.cable.name} - Point {self.order}: {self.location_name}"
    
    class Meta:
        verbose_name = "Точка маршрута кабеля"
        verbose_name_plural = "Точки маршрутов кабелей"
        ordering = ['cable', 'order']
        unique_together = ['cable', 'order']


# ОБНОВЛЕННАЯ МОДЕЛЬ СЕТЕВЫХ ЭЛЕМЕНТОВ

class NetworkElement(models.Model):
    ELEMENT_TYPES = [
        # Существующие
        ('satellite', 'Спутник'),
        ('ground_station', 'Наземная станция'),
        ('router', 'Маршрутизатор'),
        ('switch', 'Коммутатор'),
        ('server', 'Сервер'),
        ('cable', 'Кабель'),
        ('user_device', 'Пользовательское устройство'),
        # НОВЫЕ ТИПЫ
        ('core_router', 'Core Router (Магистральный)'),
        ('ix', 'Internet Exchange (IX)'),
        ('olt', 'OLT (Optical Line Terminal)'),
        ('dslam', 'DSLAM'),
        ('multiplexer', 'Мультиплексор'),
        ('modem', 'Модем'),
        ('base_station', 'Базовая станция'),
        ('data_center', 'Центр обработки данных'),
        ('repeater', 'Ретранслятор'),
    ]
    
    NETWORK_TYPES = [
        ('existing', 'Существующая сеть'),
        ('proposed', 'Предложенное решение'),
    ]
    
    element_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPES)
    network_type = models.CharField(max_length=20, choices=NETWORK_TYPES)
    
    # Геолокация
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='network_elements')
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(default=0)
    
    description = models.TextField()
    image_url = models.URLField(max_length=500, blank=True, null=True)
    specifications = models.JSONField(default=dict)
    
    # Блокчейн связи
    proposed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    proposal_tx = models.ForeignKey(BlockchainTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_element_type_display()})"
    
    class Meta:
        verbose_name = "Сетевой элемент"
        verbose_name_plural = "Сетевые элементы"


class NetworkConnection(models.Model):
    """Соединение между элементами сети"""
    from_element = models.ForeignKey(NetworkElement, related_name='connections_from', on_delete=models.CASCADE)
    to_element = models.ForeignKey(NetworkElement, related_name='connections_to', on_delete=models.CASCADE)
    connection_type = models.CharField(max_length=50)
    bandwidth = models.CharField(max_length=50, blank=True)
    latency = models.CharField(max_length=50, blank=True)
    
    class Meta:
        unique_together = ['from_element', 'to_element']
        verbose_name = "Соединение"
        verbose_name_plural = "Соединения"
    
    def __str__(self):
        return f"{self.from_element.name} → {self.to_element.name}"


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
    
    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"


class Comment(models.Model):
    """Комментарий пользователя"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    def __str__(self):
        return f"Comment by {self.user.nickname}: {self.content[:30]}..."
    
    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"


class Proposal(models.Model):
    """Предложение пользователя"""
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
    
    class Meta:
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"