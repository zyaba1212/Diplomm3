from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with wallet integration"""
    wallet_address = models.CharField(max_length=255, unique=True, blank=True, null=True)
    nickname = models.CharField(max_length=50, unique=True)
    avatar = models.ImageField(upload_to='user_avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    solana_balance = models.FloatField(default=0.0)
    reputation_score = models.IntegerField(default=0)
    
    # Добавляем related_name чтобы избежать конфликтов
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='core_user_set',  # Изменяем related_name
        related_query_name='core_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='core_user_set',  # Изменяем related_name
        related_query_name='core_user',
    )
    
    def save(self, *args, **kwargs):
        if not self.nickname and self.wallet_address:
            # Generate nickname from wallet address
            self.nickname = f"User_{self.wallet_address[-8:]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nickname} ({self.wallet_address})"

# Добавьте эти модели после класса User

class NetworkNode(models.Model):
    """Узел сети (город, ЦОД, точка обмена)"""
    NODE_TYPES = [
        ('city', 'Город'),
        ('datacenter', 'Дата-центр'),
        ('ix', 'Точка обмена (IX)'),
        ('cable_station', 'Кабельная станция'),
    ]
    
    NETWORK_TYPES = [
        ('existing', 'Существующая сеть'),
        ('proposed', 'Предлагаемая сеть'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название")
    node_type = models.CharField(max_length=50, choices=NODE_TYPES, verbose_name="Тип узла")
    network_type = models.CharField(max_length=50, choices=NETWORK_TYPES, default='existing', verbose_name="Тип сети")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    altitude = models.FloatField(default=0, verbose_name="Высота")
    country = models.CharField(max_length=100, verbose_name="Страна")
    city = models.CharField(max_length=100, verbose_name="Город")
    capacity_gbps = models.FloatField(default=1, verbose_name="Пропускная способность (Гбит/с)")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    
    def __str__(self):
        return f"{self.name} ({self.get_node_type_display()})"

class Equipment(models.Model):
    """Оборудование сети"""
    EQUIPMENT_TYPES = [
        ('router', 'Маршрутизатор'),
        ('switch', 'Коммутатор'),
        ('server', 'Сервер'),
        ('cable', 'Кабель'),
        ('antenna', 'Антенна'),
        ('satellite', 'Спутник'),
        ('modem', 'Модем'),
        ('multiplexer', 'Мультиплексор'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название")
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_TYPES, verbose_name="Тип оборудования")
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name="Производитель")
    model = models.CharField(max_length=100, blank=True, verbose_name="Модель")
    specifications = models.JSONField(default=dict, blank=True, verbose_name="Характеристики")
    power_consumption_w = models.IntegerField(default=0, verbose_name="Потребляемая мощность (Вт)")
    throughput_gbps = models.FloatField(default=1, verbose_name="Пропускная способность (Гбит/с)")
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True, verbose_name="Изображение")
    datasheet_url = models.URLField(blank=True, verbose_name="Ссылка на документацию")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    
    def __str__(self):
        return f"{self.name} ({self.get_equipment_type_display()})"

class NetworkConnection(models.Model):
    """Соединение между узлами сети"""
    CONNECTION_TYPES = [
        ('undersea_cable', 'Подводный кабель'),
        ('terrestrial_fiber', 'Наземное волокно'),
        ('wireless', 'Беспроводное'),
        ('satellite', 'Спутниковое'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название")
    connection_type = models.CharField(max_length=50, choices=CONNECTION_TYPES, verbose_name="Тип соединения")
    from_node = models.ForeignKey(NetworkNode, related_name='outgoing_connections', on_delete=models.CASCADE, verbose_name="Из узла")
    to_node = models.ForeignKey(NetworkNode, related_name='incoming_connections', on_delete=models.CASCADE, verbose_name="В узел")
    length_km = models.FloatField(default=0, verbose_name="Длина (км)")
    capacity_gbps = models.FloatField(default=1, verbose_name="Пропускная способность (Гбит/с)")
    latency_ms = models.FloatField(default=10, verbose_name="Задержка (мс)")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    description = models.TextField(blank=True, verbose_name="Описание")
    geojson_path = models.JSONField(default=dict, blank=True, verbose_name="GeoJSON путь")
    equipment_used = models.ManyToManyField(Equipment, blank=True, verbose_name="Используемое оборудование")
    
    def __str__(self):
        return f"{self.name} ({self.get_connection_type_display()})"

class NodeEquipment(models.Model):
    """Оборудование, установленное в узле"""
    node = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, verbose_name="Узел")
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, verbose_name="Оборудование")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    status = models.CharField(max_length=50, default='operational', verbose_name="Статус")
    installation_date = models.DateField(null=True, blank=True, verbose_name="Дата установки")
    
    def __str__(self):
        return f"{self.equipment.name} в {self.node.name}"

class UserProposal(models.Model):
    """Предложения пользователей"""
    PROPOSAL_TYPES = [
        ('new_equipment', 'Новое оборудование'),
        ('upgrade', 'Обновление'),
        ('new_node', 'Новый узел'),
        ('new_connection', 'Новое соединение'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('implemented', 'Реализовано'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    proposal_type = models.CharField(max_length=50, choices=PROPOSAL_TYPES, verbose_name="Тип предложения")
    description = models.TextField(verbose_name="Описание")
    target_node = models.ForeignKey(NetworkNode, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Целевой узел")
    proposed_equipment = models.ForeignKey(Equipment, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Предлагаемое оборудование")
    quantity = models.IntegerField(default=1, verbose_name="Количество")
    justification = models.TextField(blank=True, verbose_name="Обоснование")
    solana_tx_signature = models.CharField(max_length=255, verbose_name="Подпись транзакции Solana")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    admin_notes = models.TextField(blank=True, verbose_name="Заметки администратора")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    
    def __str__(self):
        return f"{self.title} от {self.user.nickname}"

class Comment(models.Model):
    """Комментарии пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    content = models.TextField(verbose_name="Содержание")
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, verbose_name="Родительский комментарий")  # <-- ДОБАВЬ ЭТУ СТРОКУ
    upvotes = models.IntegerField(default=0, verbose_name="Голосов за")
    downvotes = models.IntegerField(default=0, verbose_name="Голосов против")
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    
    def __str__(self):
        return f"Комментарий от {self.user.nickname}"

class NewsArticle(models.Model):

    SOURCE_CHOICES = [
        ('habr', 'Хабр'),
        ('twitter', 'Twitter/X'),
        ('reddit', 'Reddit'),
        ('telegram', 'Telegram'),
        ('other', 'Другое'),
    ]

    """Новости из парсера"""
    CATEGORIES = [
        ('infrastructure', 'Инфраструктура'),
        ('blockchain', 'Блокчейн'),
        ('satellite', 'Спутниковая связь'),
        ('research', 'Исследования'),
        ('general', 'Общее'),
    ]
    
    title = models.CharField(max_length=500, verbose_name="Заголовок")
    excerpt = models.TextField(blank=True, verbose_name="Краткое содержание")
    content = models.TextField(verbose_name="Содержание")
    source = models.CharField(max_length=200, verbose_name="Источник")
    source_url = models.URLField(verbose_name="Ссылка на источник")
    author = models.CharField(max_length=200, blank=True, verbose_name="Автор")
    published_date = models.DateTimeField(verbose_name="Дата публикации")
    category = models.CharField(max_length=50, choices=CATEGORIES, default='general', verbose_name="Категория")
    tags = models.CharField(max_length=500, blank=True, verbose_name="Теги")
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемая")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    
    def __str__(self):
        return self.title

class SiteSettings(models.Model):
    """Настройки сайта"""
    site_name = models.CharField(max_length=200, default="Z96A", verbose_name="Название сайта")
    primary_color = models.CharField(max_length=7, default="#2e2d2e", verbose_name="Основной цвет")
    secondary_color = models.CharField(max_length=7, default="#333135", verbose_name="Вторичный цвет")
    accent_color = models.CharField(max_length=7, default="#1b1523", verbose_name="Акцентный цвет")
    default_language = models.CharField(max_length=10, default="ru", verbose_name="Язык по умолчанию")
    is_maintenance = models.BooleanField(default=False, verbose_name="Режим обслуживания")
    
    def __str__(self):
        return "Настройки сайта"

class GlobeSettings(models.Model):
    """Настройки глобуса"""
    rotation_speed = models.FloatField(default=0.1, verbose_name="Скорость вращения")
    auto_rotate = models.BooleanField(default=True, verbose_name="Автовращение")
    show_equipment = models.BooleanField(default=True, verbose_name="Показывать оборудование")
    show_cables = models.BooleanField(default=True, verbose_name="Показывать кабели")
    zoom_level = models.FloatField(default=1.0, verbose_name="Уровень масштабирования")
    
    def __str__(self):
        return "Настройки глобуса"

class CablePath(models.Model):
    """Путь кабеля (точки маршрута)"""
    cable = models.ForeignKey(NetworkConnection, on_delete=models.CASCADE, verbose_name="Кабель")
    sequence = models.IntegerField(verbose_name="Порядковый номер")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    depth = models.FloatField(null=True, blank=True, verbose_name="Глубина (м)")
    
    class Meta:
        ordering = ['cable', 'sequence']
    
    def __str__(self):
        return f"Точка {self.sequence} кабеля {self.cable.name}"