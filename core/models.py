"""
Database models for Z96A Network
Enhanced with proper relationships, methods, and validators.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
import json


class TimeStampedModel(models.Model):
    """Abstract base model with created/modified timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True


class Region(models.Model):
    """Geographical region for organizing cables"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3498db')  # HEX color
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'


class Cable(TimeStampedModel):
    """Submarine internet cable model with enhanced fields"""
    
    # Status choices
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('under_construction', 'Under Construction'),
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('decommissioned', 'Decommissioned'),
        ('damaged', 'Damaged'),
    ]
    
    # Cable types
    TYPE_CHOICES = [
        ('fiber', 'Fiber Optic'),
        ('copper', 'Copper'),
        ('hybrid', 'Hybrid'),
        ('satellite', 'Satellite Link'),
    ]
    
    cable_id = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    alternative_name = models.CharField(max_length=200, blank=True)
    
    # Technical specifications
    length = models.FloatField(help_text="Length in kilometers", validators=[MinValueValidator(0)])
    capacity = models.FloatField(help_text="Capacity in Tbps", validators=[MinValueValidator(0)])
    fibers = models.IntegerField(default=4, validators=[MinValueValidator(1)])
    pairs = models.IntegerField(default=2, validators=[MinValueValidator(1)])
    
    # Status and type
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    cable_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='fiber')
    
    # Dates
    planned_rfs = models.DateField(null=True, blank=True, verbose_name="Planned Ready for Service")
    actual_rfs = models.DateField(null=True, blank=True, verbose_name="Actual Ready for Service")
    
    # Ownership and operators
    owners = models.TextField(help_text="Comma-separated list of owners", blank=True)
    suppliers = models.TextField(help_text="Comma-separated list of suppliers", blank=True)
    
    # Cost information
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Cost in USD")
    currency = models.CharField(max_length=3, default='USD')
    
    # Geographical data
    coordinates = models.JSONField(default=dict, help_text="GeoJSON LineString of cable route")
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='cables')
    
    # URLs and documentation
    url = models.URLField(max_length=500, blank=True, validators=[URLValidator()])
    documentation_url = models.URLField(max_length=500, blank=True, validators=[URLValidator()])
    
    # Metadata
    notes = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    data_source = models.CharField(max_length=100, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.cable_id}) - {self.get_status_display()}"
    
    def get_owners_list(self):
        """Returns list of owners"""
        return [owner.strip() for owner in self.owners.split(',') if owner.strip()]
    
    def get_suppliers_list(self):
        """Returns list of suppliers"""
        return [supplier.strip() for supplier in self.suppliers.split(',') if supplier.strip()]
    
    def get_coordinates_list(self):
        """Returns coordinates as list of [lng, lat] pairs"""
        if self.coordinates and 'coordinates' in self.coordinates:
            return self.coordinates['coordinates']
        return []
    
    def calculate_capacity_per_km(self):
        """Calculates capacity per kilometer"""
        if self.length > 0:
            return self.capacity / self.length
        return 0
    
    def is_active(self):
        """Check if cable is active"""
        return self.status == 'active'
    
    def get_status_color(self):
        """Returns CSS color based on status"""
        colors = {
            'planned': '#3498db',  # Blue
            'under_construction': '#f39c12',  # Orange
            'active': '#2ecc71',  # Green
            'maintenance': '#9b59b6',  # Purple
            'decommissioned': '#95a5a6',  # Gray
            'damaged': '#e74c3c',  # Red
        }
        return colors.get(self.status, '#95a5a6')
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['cable_type']),
            models.Index(fields=['region']),
            models.Index(fields=['is_featured']),
        ]
        verbose_name = 'Submarine Cable'
        verbose_name_plural = 'Submarine Cables'


class LandingPoint(TimeStampedModel):
    """Landing point where cable connects to shore"""
    
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Technical details
    facility_type = models.CharField(max_length=100, blank=True)
    is_connected_to_grid = models.BooleanField(default=True)
    power_supply = models.CharField(max_length=100, blank=True)
    
    # Cable connections
    cables = models.ManyToManyField(Cable, related_name='landing_points', blank=True)
    
    # Contact information
    operator = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    
    # Security
    security_level = models.CharField(max_length=50, blank=True)
    access_restrictions = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name}, {self.country}"
    
    def get_cables_count(self):
        """Returns number of connected cables"""
        return self.cables.count()
    
    def get_active_cables(self):
        """Returns active cables at this landing point"""
        return self.cables.filter(status='active')
    
    def get_coordinates(self):
        """Returns coordinates as tuple (lat, lng)"""
        return (self.latitude, self.longitude)
    
    class Meta:
        ordering = ['country', 'city', 'name']
        unique_together = ['name', 'country', 'city']
        verbose_name = 'Landing Point'
        verbose_name_plural = 'Landing Points'


class Equipment(TimeStampedModel):
    """Network equipment model"""
    
    EQUIPMENT_TYPES = [
        ('repeater', 'Optical Repeater'),
        ('branching', 'Branching Unit'),
        ('terminal', 'Terminal Equipment'),
        ('power_feed', 'Power Feed Equipment'),
        ('monitoring', 'Monitoring Equipment'),
    ]
    
    MANUFACTURERS = [
        ('nokia', 'Nokia'),
        ('huawei', 'Huawei'),
        ('cisco', 'Cisco'),
        ('juniper', 'Juniper'),
        ('ericsson', 'Ericsson'),
        ('zte', 'ZTE'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    equipment_id = models.CharField(max_length=100, unique=True)
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_TYPES)
    manufacturer = models.CharField(max_length=50, choices=MANUFACTURERS)
    model = models.CharField(max_length=100)
    
    # Specifications
    specifications = models.JSONField(default=dict, blank=True)
    installation_date = models.DateField(null=True, blank=True)
    warranty_until = models.DateField(null=True, blank=True)
    
    # Location
    cable = models.ForeignKey(Cable, on_delete=models.CASCADE, related_name='equipment')
    distance_from_start = models.FloatField(
        help_text="Distance from cable start in kilometers",
        validators=[MinValueValidator(0)]
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    depth = models.FloatField(null=True, blank=True, help_text="Depth in meters")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    
    # Media
    image = models.ImageField(upload_to='equipment_images/', null=True, blank=True)
    documentation = models.FileField(upload_to='equipment_docs/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_equipment_type_display()} - {self.name} ({self.equipment_id})"
    
    def get_specifications_summary(self):
        """Returns formatted specifications"""
        specs = []
        if 'power' in self.specifications:
            specs.append(f"Power: {self.specifications['power']}")
        if 'frequency' in self.specifications:
            specs.append(f"Frequency: {self.specifications['frequency']}")
        if 'range' in self.specifications:
            specs.append(f"Range: {self.specifications['range']}")
        return ', '.join(specs)
    
    def requires_maintenance(self):
        """Check if equipment requires maintenance"""
        if not self.next_maintenance:
            return False
        return self.next_maintenance <= timezone.now().date()
    
    class Meta:
        ordering = ['cable', 'distance_from_start']
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'


class BlockchainTransaction(TimeStampedModel):
    """Blockchain transaction model with enhanced fields"""
    
    TRANSACTION_TYPES = [
        ('transfer', 'Transfer'),
        ('reward', 'Reward'),
        ('penalty', 'Penalty'),
        ('mining_reward', 'Mining Reward'),
        ('system', 'System Transaction'),
        ('purchase', 'Purchase'),
        ('refund', 'Refund'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
    ]
    
    # Transaction identification
    tx_id = models.CharField(max_length=64, unique=True, db_index=True)
    block_hash = models.CharField(max_length=64, blank=True, db_index=True)
    block_index = models.IntegerField(null=True, blank=True, db_index=True)
    
    # Parties involved
    sender = models.CharField(max_length=200, db_index=True)
    recipient = models.CharField(max_length=200, db_index=True)
    
    # Transaction details
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Cryptographic data
    public_key = models.TextField(blank=True)
    signature = models.TextField(blank=True)
    tx_hash = models.CharField(max_length=64, blank=True, db_index=True)
    
    # Metadata
    description = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=8, default=0)
    gas_price = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    gas_used = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    
    # Related objects
    cable = models.ForeignKey(Cable, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    equipment = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Timestamps
    blockchain_timestamp = models.FloatField(null=True, blank=True)
    confirmation_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.tx_id[:16]}... - {self.sender} → {self.recipient}: {self.amount} ZETA"
    
    def is_confirmed(self):
        """Check if transaction is confirmed"""
        return self.status == 'confirmed'
    
    def get_confirmation_time_display(self):
        """Returns formatted confirmation time"""
        if self.confirmation_time:
            return self.confirmation_time.strftime('%Y-%m-%d %H:%M:%S')
        return "Not confirmed"
    
    def get_transaction_url(self):
        """Returns transaction explorer URL (if applicable)"""
        if self.tx_hash:
            return f"/blockchain/transaction/{self.tx_hash}/"
        return f"/blockchain/transaction/{self.tx_id}/"
    
    def verify_signature(self):
        """Verify transaction signature"""
        from core.blockchain import BlockchainTransaction as BCTransaction
        try:
            tx_data = {
                'tx_id': self.tx_id,
                'sender': self.sender,
                'recipient': self.recipient,
                'amount': float(self.amount),
                'transaction_type': self.transaction_type,
                'description': self.description,
                'timestamp': self.blockchain_timestamp or self.created_at.timestamp(),
                'public_key': self.public_key,
                'signature': self.signature,
            }
            tx = BCTransaction.from_dict(tx_data)
            return tx.verify_signature()
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'status']),
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['cable', 'status']),
        ]
        verbose_name = 'Blockchain Transaction'
        verbose_name_plural = 'Blockchain Transactions'


class News(TimeStampedModel):
    """News and announcements model"""
    
    CATEGORIES = [
        ('project', 'Project News'),
        ('cable', 'Cable News'),
        ('technology', 'Technology'),
        ('partnership', 'Partnership'),
        ('event', 'Event'),
        ('maintenance', 'Maintenance'),
        ('incident', 'Incident'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)
    
    # Categorization
    category = models.CharField(max_length=20, choices=CATEGORIES, default='project')
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    
    # Media
    image = models.ImageField(upload_to='news_images/', null=True, blank=True)
    image_caption = models.CharField(max_length=200, blank=True)
    
    # Publication
    is_published = models.BooleanField(default=False)
    published_date = models.DateTimeField(null=True, blank=True)
    author = models.CharField(max_length=100, blank=True)
    
    # Related content
    related_cables = models.ManyToManyField(Cable, blank=True, related_name='news')
    source_url = models.URLField(blank=True, validators=[URLValidator()])
    
    # Engagement
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        """Returns list of tags"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
        self.save(update_fields=['views'])
    
    def publish(self):
        """Publish the news item"""
        self.is_published = True
        self.published_date = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-published_date', '-created_at']
        verbose_name = 'News'
        verbose_name_plural = 'News'
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['is_published', 'published_date']),
        ]


class Discussion(TimeStampedModel):
    """Discussion/comment model with threading"""
    
    CONTENT_TYPES = [
        ('cable', 'Cable Discussion'),
        ('news', 'News Discussion'),
        ('general', 'General Discussion'),
        ('technical', 'Technical Discussion'),
        ('suggestion', 'Suggestion'),
    ]
    
    # Content
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='general')
    
    # Author (can be anonymous)
    author_name = models.CharField(max_length=100, blank=True)
    author_email = models.EmailField(blank=True)
    author_ip = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    
    # Parent relationship for threading
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Related objects
    cable = models.ForeignKey(Cable, on_delete=models.CASCADE, null=True, blank=True, related_name='discussions')
    news = models.ForeignKey(News, on_delete=models.CASCADE, null=True, blank=True, related_name='discussions')
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    # Engagement
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    
    # Metadata
    user_agent = models.TextField(blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    edit_reason = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        if self.title:
            return f"{self.title} by {self.author_name or 'Anonymous'}"
        return f"Comment by {self.author_name or 'Anonymous'}"
    
    def vote_score(self):
        """Calculate vote score"""
        return self.upvotes - self.downvotes
    
    def is_reply(self):
        """Check if this is a reply"""
        return self.parent is not None
    
    def get_replies(self):
        """Get all replies"""
        return self.replies.filter(is_approved=True).order_by('created_at')
    
    def update_reply_count(self):
        """Update reply count"""
        self.reply_count = self.replies.filter(is_approved=True).count()
        self.save(update_fields=['reply_count'])
    
    def mark_as_edited(self, reason=""):
        """Mark discussion as edited"""
        self.edited_at = timezone.now()
        self.edit_reason = reason
        self.save(update_fields=['edited_at', 'edit_reason'])
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'Discussion'
        verbose_name_plural = 'Discussions'
        indexes = [
            models.Index(fields=['cable', 'is_approved']),
            models.Index(fields=['news', 'is_approved']),
            models.Index(fields=['parent', 'is_approved']),
            models.Index(fields=['content_type', 'is_approved']),
        ]


class UserProfile(TimeStampedModel):
    """Extended user profile with blockchain integration"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Blockchain wallet
    wallet_address = models.CharField(max_length=64, unique=True, db_index=True)
    public_key = models.TextField(blank=True)
    private_key_encrypted = models.TextField(blank=True)  # Encrypted in database
    
    # Balance information
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    pending_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_earned = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_spent = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    # Profile information
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True, validators=[URLValidator()])
    
    # Statistics
    cables_viewed = models.ManyToManyField(Cable, blank=True, related_name='viewed_by')
    cables_favorited = models.ManyToManyField(Cable, blank=True, related_name='favorited_by')
    discussions_count = models.IntegerField(default=0)
    transactions_count = models.IntegerField(default=0)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=False)
    theme = models.CharField(max_length=20, default='light', choices=[('light', 'Light'), ('dark', 'Dark')])
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_date = models.DateTimeField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    verification_expires = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_display_name(self):
        """Get user's display name"""
        if self.user.get_full_name():
            return self.user.get_full_name()
        return self.user.username
    
    def increment_transaction_count(self):
        """Increment transaction count"""
        self.transactions_count += 1
        self.save(update_fields=['transactions_count'])
    
    def update_balance(self, amount):
        """Update user balance"""
        self.balance += amount
        if amount > 0:
            self.total_earned += amount
        else:
            self.total_spent += abs(amount)
        self.save(update_fields=['balance', 'total_earned', 'total_spent'])
    
    def get_favorite_cables(self):
        """Get user's favorite cables"""
        return self.cables_favorited.all()
    
    def get_viewed_cables(self):
        """Get cables viewed by user"""
        return self.cables_viewed.all()
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['wallet_address']),
            models.Index(fields=['balance']),
            models.Index(fields=['user', 'is_verified']),
        ]


class SystemLog(TimeStampedModel):
    """System logging for monitoring and debugging"""
    
    LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    CATEGORY_CHOICES = [
        ('blockchain', 'Blockchain'),
        ('cable', 'Cable'),
        ('user', 'User'),
        ('system', 'System'),
        ('security', 'Security'),
        ('api', 'API'),
    ]
    
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Source information
    source = models.CharField(max_length=200, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Trace information
    traceback = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.message[:100]}"
    
    def is_error(self):
        """Check if log is error level or higher"""
        return self.level in ['error', 'critical']
    
    def get_formatted_details(self):
        """Get formatted JSON details"""
        return json.dumps(self.details, indent=2)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        indexes = [
            models.Index(fields=['level', 'category']),
            models.Index(fields=['created_at', 'level']),
            models.Index(fields=['user', 'created_at']),
        ]


# Utility functions
def generate_wallet_address():
    """Generate unique wallet address"""
    import hashlib
    import time
    import random
    
    data = f"{time.time()}{random.random()}".encode()
    return hashlib.sha256(data).hexdigest()[:32]


def validate_coordinates(coords):
    """Validate coordinates format"""
    if not isinstance(coords, (list, tuple)):
        return False
    
    for coord in coords:
        if not isinstance(coord, (list, tuple)) or len(coord) != 2:
            return False
        
        lng, lat = coord
        if not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
            return False
    
    return True