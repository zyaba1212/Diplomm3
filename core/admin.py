from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from import_export.admin import ImportExportModelAdmin
from .models import (
    User, NetworkNode, Equipment, NetworkConnection, 
    NodeEquipment, UserProposal, Comment, NewsArticle,
    SiteSettings, GlobeSettings, CablePath
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'nickname', 'wallet_address', 'is_verified', 'reputation_score', 'date_joined')
    list_filter = ('is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'nickname', 'wallet_address', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('nickname', 'wallet_address', 'email', 'avatar')}),
        (_('Permissions'), {'fields': ('is_verified', 'reputation_score', 'solana_balance', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    ordering = ('-date_joined',)

class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'node_type', 'city', 'country', 'network_type', 'is_active', 'created_at')
    list_filter = ('node_type', 'network_type', 'country', 'is_active')
    search_fields = ('name', 'city', 'country', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('id', 'name', 'node_type', 'network_type')}),
        (_('Location'), {'fields': ('latitude', 'longitude', 'altitude', 'country', 'city')}),
        (_('Specifications'), {'fields': ('capacity_gbps', 'is_active', 'description')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )

class EquipmentAdmin(ImportExportModelAdmin):
    list_display = ('name', 'equipment_type', 'manufacturer', 'model', 'power_consumption_w', 'throughput_gbps')
    list_filter = ('equipment_type', 'manufacturer')
    search_fields = ('name', 'manufacturer', 'model', 'description')
    readonly_fields = ('id', 'created_at', 'equipment_image_preview')
    fieldsets = (
        (None, {'fields': ('id', 'name', 'equipment_type')}),
        (_('Manufacturer Info'), {'fields': ('manufacturer', 'model', 'datasheet_url')}),
        (_('Specifications'), {'fields': ('specifications', 'power_consumption_w', 'throughput_gbps')}),
        (_('Description & Image'), {'fields': ('description', 'image', 'equipment_image_preview')}),
        (_('Timestamps'), {'fields': ('created_at',)}),
    )
    
    def equipment_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" height="150" style="object-fit:contain;" />', obj.image.url)
        return "-"
    equipment_image_preview.short_description = _('Image Preview')

class NetworkConnectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'connection_type', 'from_node', 'to_node', 'capacity_gbps', 'is_active')
    list_filter = ('connection_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('id',)
    fieldsets = (
        (None, {'fields': ('id', 'name', 'connection_type')}),
        (_('Connection'), {'fields': ('from_node', 'to_node', 'geojson_path')}),
        (_('Specifications'), {'fields': ('length_km', 'capacity_gbps', 'latency_ms', 'is_active')}),
        (_('Equipment'), {'fields': ('equipment_used', 'description')}),
    )

class NodeEquipmentAdmin(admin.ModelAdmin):
    list_display = ('node', 'equipment', 'quantity', 'status', 'installation_date')
    list_filter = ('status', 'installation_date')
    search_fields = ('node__name', 'equipment__name')
    readonly_fields = ('id',)

class UserProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'proposal_type', 'status', 'target_node', 'created_at')
    list_filter = ('proposal_type', 'status', 'created_at')
    search_fields = ('title', 'description', 'user__nickname', 'solana_tx_signature')
    readonly_fields = ('id', 'created_at', 'updated_at', 'solana_tx_link')
    fieldsets = (
        (None, {'fields': ('id', 'title', 'proposal_type', 'status')}),
        (_('User Info'), {'fields': ('user', 'solana_tx_signature', 'solana_tx_link')}),
        (_('Proposal Details'), {'fields': ('target_node', 'proposed_equipment', 'quantity', 'justification')}),
        (_('Content'), {'fields': ('description',)}),
        (_('Admin'), {'fields': ('admin_notes',)}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
    
    def solana_tx_link(self, obj):
        url = f"https://solscan.io/tx/{obj.solana_tx_signature}"
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.solana_tx_signature[:20] + "...")
    solana_tx_link.short_description = _('Solana Transaction')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_preview', 'upvotes', 'downvotes', 'is_pinned', 'created_at')
    list_filter = ('is_pinned', 'created_at')
    search_fields = ('content', 'user__nickname')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = _('Content')

class NewsArticleAdmin(ImportExportModelAdmin):
    list_display = ('title', 'source', 'author', 'published_date', 'is_featured')
    list_filter = ('source', 'is_featured', 'published_date')
    search_fields = ('title', 'content', 'author', 'tags')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        (None, {'fields': ('id', 'title', 'excerpt', 'is_featured')}),
        (_('Content'), {'fields': ('content',)}),
        (_('Source Info'), {'fields': ('source', 'source_url', 'author', 'published_date')}),
        (_('Categories'), {'fields': ('category', 'tags')}),
        (_('Timestamps'), {'fields': ('created_at',)}),
    )

class CablePathAdmin(admin.ModelAdmin):
    list_display = ('cable', 'sequence', 'latitude', 'longitude', 'depth')
    list_filter = ('cable',)
    ordering = ('cable', 'sequence')

admin.site.register(User, CustomUserAdmin)
admin.site.register(NetworkNode, NetworkNodeAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(NetworkConnection, NetworkConnectionAdmin)
admin.site.register(NodeEquipment, NodeEquipmentAdmin)
admin.site.register(UserProposal, UserProposalAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(NewsArticle, NewsArticleAdmin)
admin.site.register(SiteSettings)
admin.site.register(GlobeSettings)
admin.site.register(CablePath, CablePathAdmin)

# Customize admin interface
admin.site.site_header = "Z96A - Network Architecture Administration"
admin.site.site_title = "Z96A Admin"
admin.site.index_title = "Welcome to Z96A Administration"