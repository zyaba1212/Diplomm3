"""
Django admin configuration for Z96A Network
Enhanced with custom actions, filters, and views.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Cable, LandingPoint, Equipment, BlockchainTransaction,
    News, Discussion, UserProfile, SystemLog, Region
)


# Custom admin site header
admin.site.site_header = "Z96A Network Administration"
admin.site.site_title = "Z96A Admin"
admin.site.index_title = "Dashboard"


class RegionAdmin(admin.ModelAdmin):
    """Admin for Region model"""
    list_display = ['name', 'code', 'cables_count', 'color_display']
    list_filter = ['name']
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'code': ['name']}
    
    def cables_count(self, obj):
        return obj.cables.count()
    cables_count.short_description = 'Cables'
    
    def color_display(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'


class CableAdmin(admin.ModelAdmin):
    """Admin for Cable model with enhanced features"""
    
    list_display = [
        'name', 'cable_id', 'status_badge', 'length', 'capacity', 
        'region', 'is_featured', 'created_at'
    ]
    
    list_filter = [
        'status', 'cable_type', 'region', 'is_featured',
        'created_at', 'actual_rfs'
    ]
    
    search_fields = [
        'name', 'cable_id', 'alternative_name', 'owners',
        'suppliers', 'notes'
    ]
    
    readonly_fields = [
        'created_at', 'updated_at', 'last_updated',
        'capacity_per_km', 'owners_list', 'suppliers_list'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('cable_id', 'name', 'alternative_name', 'region')
        }),
        ('Technical Specifications', {
            'fields': ('length', 'capacity', 'fibers', 'pairs', 'cable_type')
        }),
        ('Status and Dates', {
            'fields': ('status', 'planned_rfs', 'actual_rfs')
        }),
        ('Ownership and Cost', {
            'fields': ('owners', 'suppliers', 'cost', 'currency')
        }),
        ('Geographical Data', {
            'fields': ('coordinates', 'url', 'documentation_url')
        }),
        ('Metadata', {
            'fields': ('notes', 'is_featured', 'data_source')
        }),
        ('Read-only Information', {
            'fields': ('capacity_per_km', 'owners_list', 'suppliers_list'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_active', 'mark_as_featured', 'export_as_json',
        'calculate_statistics'
    ]
    
    def status_badge(self, obj):
        colors = {
            'planned': 'blue',
            'under_construction': 'orange',
            'active': 'green',
            'maintenance': 'purple',
            'decommissioned': 'gray',
            'damaged': 'red',
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def capacity_per_km(self, obj):
        return f"{obj.calculate_capacity_per_km():.4f} Tbps/km"
    capacity_per_km.short_description = 'Capacity per km'
    
    def owners_list(self, obj):
        return ', '.join(obj.get_owners_list())
    owners_list.short_description = 'Owners (parsed)'
    
    def suppliers_list(self, obj):
        return ', '.join(obj.get_suppliers_list())
    suppliers_list.short_description = 'Suppliers (parsed)'
    
    # Custom actions
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f"{updated} cable(s) marked as active."
        )
    mark_as_active.short_description = "Mark selected cables as active"
    
    def mark_as_featured(self, request, queryset):
        for cable in queryset:
            cable.is_featured = not cable.is_featured
            cable.save()
        
        self.message_user(
            request,
            f"Featured status toggled for {queryset.count()} cable(s)."
        )
    mark_as_featured.short_description = "Toggle featured status"
    
    def export_as_json(self, request, queryset):
        """Export selected cables as JSON"""
        import json
        from django.http import HttpResponse
        
        data = []
        for cable in queryset:
            cable_data = {
                'cable_id': cable.cable_id,
                'name': cable.name,
                'length': cable.length,
                'capacity': cable.capacity,
                'status': cable.status,
                'coordinates': cable.coordinates,
                'owners': cable.get_owners_list(),
                'suppliers': cable.get_suppliers_list(),
            }
            data.append(cable_data)
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="cables_export.json"'
        return response
    export_as_json.short_description = "Export selected cables as JSON"
    
    def calculate_statistics(self, request, queryset):
        """Calculate statistics for selected cables"""
        total_length = queryset.aggregate(Sum('length'))['length__sum'] or 0
        total_capacity = queryset.aggregate(Sum('capacity'))['capacity__sum'] or 0
        avg_length = queryset.aggregate(Avg('length'))['length__avg'] or 0
        active_count = queryset.filter(status='active').count()
        
        self.message_user(
            request,
            f"Statistics for {queryset.count()} cable(s):\n"
            f"• Total length: {total_length:,.0f} km\n"
            f"• Total capacity: {total_capacity:,.1f} Tbps\n"
            f"• Average length: {avg_length:,.0f} km\n"
            f"• Active cables: {active_count}"
        )
    calculate_statistics.short_description = "Calculate statistics"


class LandingPointAdmin(admin.ModelAdmin):
    """Admin for LandingPoint model"""
    
    list_display = [
        'name', 'country', 'city', 'cables_count',
        'latitude', 'longitude', 'facility_type'
    ]
    
    list_filter = ['country', 'facility_type', 'is_connected_to_grid']
    search_fields = ['name', 'country', 'city', 'operator']
    filter_horizontal = ['cables']
    readonly_fields = ['cables_count_display', 'coordinates_display']
    
    def cables_count(self, obj):
        count = obj.cables.count()
        return format_html(
            '<span style="background-color: #e3f2fd; color: #1976d2; '
            'padding: 2px 6px; border-radius: 10px; font-weight: bold;">{}</span>',
            count
        )
    cables_count.short_description = 'Cables'
    
    def cables_count_display(self, obj):
        return obj.cables.count()
    cables_count_display.short_description = 'Connected cables count'
    
    def coordinates_display(self, obj):
        return f"{obj.latitude}, {obj.longitude}"
    coordinates_display.short_description = 'Coordinates'
    
    fieldsets = (
        ('Location', {
            'fields': ('name', 'country', 'city', 'latitude', 'longitude')
        }),
        ('Technical Details', {
            'fields': ('facility_type', 'is_connected_to_grid', 'power_supply')
        }),
        ('Connections', {
            'fields': ('cables', 'cables_count_display')
        }),
        ('Contact Information', {
            'fields': ('operator', 'contact_email', 'contact_phone')
        }),
        ('Security', {
            'fields': ('security_level', 'access_restrictions'),
            'classes': ('collapse',)
        }),
    )


class EquipmentAdmin(admin.ModelAdmin):
    """Admin for Equipment model"""
    
    list_display = [
        'name', 'equipment_id', 'equipment_type', 'manufacturer',
        'cable', 'is_active_badge', 'installation_date'
    ]
    
    list_filter = [
        'equipment_type', 'manufacturer', 'is_active',
        'cable', 'installation_date'
    ]
    
    search_fields = [
        'name', 'equipment_id', 'model', 'specifications'
    ]
    
    readonly_fields = [
        'specifications_display', 'requires_maintenance_display',
        'location_display'
    ]
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #4caf50; color: white; '
                'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; '
            'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def specifications_display(self, obj):
        return obj.get_specifications_summary()
    specifications_display.short_description = 'Specifications Summary'
    
    def requires_maintenance_display(self, obj):
        if obj.requires_maintenance():
            return format_html(
                '<span style="color: #ff9800; font-weight: bold;">YES '
                '(Due: {})</span>'.format(obj.next_maintenance)
            )
        return "No"
    requires_maintenance_display.short_description = 'Requires Maintenance'
    
    def location_display(self, obj):
        if obj.latitude and obj.longitude:
            return f"Lat: {obj.latitude}, Lng: {obj.longitude}, Depth: {obj.depth}m"
        return f"Distance from start: {obj.distance_from_start}km"
    location_display.short_description = 'Location Details'
    
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'equipment_id', 'equipment_type', 'manufacturer', 'model')
        }),
        ('Specifications', {
            'fields': ('specifications', 'specifications_display')
        }),
        ('Location', {
            'fields': ('cable', 'distance_from_start', 'latitude', 'longitude', 'depth')
        }),
        ('Status and Maintenance', {
            'fields': (
                'is_active', 'installation_date', 'warranty_until',
                'last_maintenance', 'next_maintenance',
                'requires_maintenance_display'
            )
        }),
        ('Media', {
            'fields': ('image', 'documentation'),
            'classes': ('collapse',)
        }),
        ('Location Details', {
            'fields': ('location_display',),
            'classes': ('collapse',)
        }),
    )


class BlockchainTransactionAdmin(admin.ModelAdmin):
    """Admin for BlockchainTransaction model"""
    
    list_display = [
        'tx_id_short', 'sender', 'recipient', 'amount',
        'transaction_type_badge', 'status_badge', 'confirmed_at',
        'cable_link'
    ]
    
    list_filter = [
        'transaction_type', 'status', 'created_at',
        'block_index', 'cable'
    ]
    
    search_fields = [
        'tx_id', 'sender', 'recipient', 'description',
        'tx_hash', 'block_hash'
    ]
    
    readonly_fields = [
        'tx_id', 'tx_hash', 'block_hash', 'block_index',
        'created_at', 'updated_at', 'confirmation_time',
        'signature_verified', 'transaction_url'
    ]
    
    def tx_id_short(self, obj):
        return f"{obj.tx_id[:16]}..."
    tx_id_short.short_description = 'Transaction ID'
    tx_id_short.admin_order_field = 'tx_id'
    
    def transaction_type_badge(self, obj):
        colors = {
            'transfer': '#2196f3',
            'reward': '#4caf50',
            'penalty': '#f44336',
            'mining_reward': '#ff9800',
            'system': '#9c27b0',
            'purchase': '#3f51b5',
            'refund': '#009688',
        }
        color = colors.get(obj.transaction_type, '#607d8b')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#4caf50',
            'failed': '#f44336',
            'rejected': '#9e9e9e',
        }
        color = colors.get(obj.status, '#607d8b')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def confirmed_at(self, obj):
        if obj.confirmation_time:
            return obj.confirmation_time.strftime('%Y-%m-%d %H:%M')
        return "-"
    confirmed_at.short_description = 'Confirmed'
    
    def cable_link(self, obj):
        if obj.cable:
            return format_html(
                '<a href="/admin/core/cable/{}/change/">{}</a>',
                obj.cable.id, obj.cable.name
            )
        return "-"
    cable_link.short_description = 'Cable'
    
    def signature_verified(self, obj):
        if obj.verify_signature():
            return format_html(
                '<span style="color: #4caf50; font-weight: bold;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-weight: bold;">✗ Invalid</span>'
        )
    signature_verified.short_description = 'Signature'
    
    def transaction_url(self, obj):
        return format_html(
            '<a href="{}" target="_blank">View in Explorer</a>',
            obj.get_transaction_url()
        )
    transaction_url.short_description = 'Explorer Link'
    
    actions = ['confirm_transactions', 'reject_transactions', 'resend_to_blockchain']
    
    def confirm_transactions(self, request, queryset):
        updated = queryset.update(
            status='confirmed',
            confirmation_time=timezone.now()
        )
        self.message_user(
            request,
            f"{updated} transaction(s) confirmed."
        )
    confirm_transactions.short_description = "Confirm selected transactions"
    
    def reject_transactions(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(
            request,
            f"{updated} transaction(s) rejected."
        )
    reject_transactions.short_description = "Reject selected transactions"
    
    def resend_to_blockchain(self, request, queryset):
        from core.services.blockchain_service import BlockchainService
        service = BlockchainService()
        
        successful = 0
        failed = 0
        
        for transaction in queryset.filter(status__in=['pending', 'failed']):
            try:
                # Convert to dict and resend
                tx_data = {
                    'tx_id': transaction.tx_id,
                    'sender': transaction.sender,
                    'recipient': transaction.recipient,
                    'amount': float(transaction.amount),
                    'transaction_type': transaction.transaction_type,
                    'description': transaction.description,
                    'public_key': transaction.public_key,
                    'signature': transaction.signature,
                }
                
                success, message = service.add_transaction(tx_data)
                if success:
                    successful += 1
                    transaction.status = 'pending'
                    transaction.save()
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
        
        self.message_user(
            request,
            f"Resent {successful} transaction(s) successfully, {failed} failed."
        )
    resend_to_blockchain.short_description = "Resend to blockchain"
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('tx_id', 'sender', 'recipient', 'amount', 'fee')
        }),
        ('Type and Status', {
            'fields': ('transaction_type', 'status', 'description')
        }),
        ('Blockchain Data', {
            'fields': ('tx_hash', 'block_hash', 'block_index', 'public_key', 'signature')
        }),
        ('Verification', {
            'fields': ('signature_verified',),
            'classes': ('collapse',)
        }),
        ('Related Objects', {
            'fields': ('cable', 'equipment'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmation_time', 'blockchain_timestamp'),
            'classes': ('collapse',)
        }),
        ('Explorer', {
            'fields': ('transaction_url',),
            'classes': ('collapse',)
        }),
    )


class NewsAdmin(admin.ModelAdmin):
    """Admin for News model"""
    
    list_display = [
        'title', 'category_badge', 'is_published_badge',
        'published_date', 'views', 'likes', 'author'
    ]
    
    list_filter = ['category', 'is_published', 'published_date', 'tags']
    search_fields = ['title', 'content', 'excerpt', 'author', 'tags']
    prepopulated_fields = {'slug': ['title']}
    readonly_fields = ['views', 'likes', 'shares', 'created_at', 'updated_at']
    filter_horizontal = ['related_cables']
    
    def category_badge(self, obj):
        colors = {
            'project': '#2196f3',
            'cable': '#4caf50',
            'technology': '#9c27b0',
            'partnership': '#ff9800',
            'event': '#3f51b5',
            'maintenance': '#009688',
            'incident': '#f44336',
        }
        color = colors.get(obj.category, '#607d8b')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def is_published_badge(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="background-color: #4caf50; color: white; '
                'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Published</span>'
            )
        return format_html(
            '<span style="background-color: #ff9800; color: white; '
            'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Draft</span>'
        )
    is_published_badge.short_description = 'Status'
    
    actions = ['publish_news', 'unpublish_news', 'reset_views']
    
    def publish_news(self, request, queryset):
        for news in queryset:
            news.publish()
        
        self.message_user(
            request,
            f"{queryset.count()} news item(s) published."
        )
    publish_news.short_description = "Publish selected news"
    
    def unpublish_news(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f"{updated} news item(s) unpublished."
        )
    unpublish_news.short_description = "Unpublish selected news"
    
    def reset_views(self, request, queryset):
        updated = queryset.update(views=0)
        self.message_user(
            request,
            f"View count reset for {updated} news item(s)."
        )
    reset_views.short_description = "Reset view counts"
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Media', {
            'fields': ('image', 'image_caption')
        }),
        ('Publication', {
            'fields': ('is_published', 'published_date', 'author', 'source_url')
        }),
        ('Related Content', {
            'fields': ('related_cables',)
        }),
        ('Engagement', {
            'fields': ('views', 'likes', 'shares'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class DiscussionAdmin(admin.ModelAdmin):
    """Admin for Discussion model"""
    
    list_display = [
        'content_preview', 'author_name', 'content_type_badge',
        'is_approved_badge', 'is_featured_badge', 'vote_score',
        'reply_count', 'created_at'
    ]
    
    list_filter = [
        'content_type', 'is_approved', 'is_featured', 'is_pinned',
        'cable', 'news', 'created_at'
    ]
    
    search_fields = [
        'title', 'content', 'author_name', 'author_email'
    ]
    
    readonly_fields = [
        'upvotes', 'downvotes', 'reply_count', 'user_agent',
        'created_at', 'updated_at', 'edited_at',
        'vote_score_display', 'is_reply_display'
    ]
    
    actions = [
        'approve_discussions', 'reject_discussions',
        'feature_discussions', 'pin_discussions'
    ]
    
    def content_preview(self, obj):
        content = obj.title if obj.title else obj.content[:100]
        return format_html('<strong>{}</strong>', content)
    content_preview.short_description = 'Content'
    
    def content_type_badge(self, obj):
        colors = {
            'cable': '#2196f3',
            'news': '#4caf50',
            'general': '#9e9e9e',
            'technical': '#ff9800',
            'suggestion': '#9c27b0',
        }
        color = colors.get(obj.content_type, '#607d8b')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 6px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_content_type_display()
        )
    content_type_badge.short_description = 'Type'
    
    def is_approved_badge(self, obj):
        if obj.is_approved:
            return format_html(
                '<span style="background-color: #4caf50; color: white; '
                'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Approved</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; '
            'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Pending</span>'
        )
    is_approved_badge.short_description = 'Approved'
    
    def is_featured_badge(self, obj):
        if obj.is_featured:
            return format_html(
                '<span style="background-color: #ff9800; color: white; '
                'padding: 2px 6px; border-radius: 10px; font-size: 11px;">Featured</span>'
            )
        return "-"
    is_featured_badge.short_description = 'Featured'
    
    def vote_score_display(self, obj):
        return obj.vote_score()
    vote_score_display.short_description = 'Vote Score'
    
    def is_reply_display(self, obj):
        return "Yes" if obj.parent else "No"
    is_reply_display.short_description = 'Is Reply?'
    
    def approve_discussions(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f"{updated} discussion(s) approved."
        )
    approve_discussions.short_description = "Approve selected discussions"
    
    def reject_discussions(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f"{updated} discussion(s) rejected."
        )
    reject_discussions.short_description = "Reject selected discussions"
    
    def feature_discussions(self, request, queryset):
        for discussion in queryset:
            discussion.is_featured = not discussion.is_featured
            discussion.save()
        
        self.message_user(
            request,
            f"Featured status toggled for {queryset.count()} discussion(s)."
        )
    feature_discussions.short_description = "Toggle featured status"
    
    def pin_discussions(self, request, queryset):
        for discussion in queryset:
            discussion.is_pinned = not discussion.is_pinned
            discussion.save()
        
        self.message_user(
            request,
            f"Pinned status toggled for {queryset.count()} discussion(s)."
        )
    pin_discussions.short_description = "Toggle pinned status"
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'content_type')
        }),
        ('Author Information', {
            'fields': ('author_name', 'author_email', 'user', 'author_ip')
        }),
        ('Relationships', {
            'fields': ('parent', 'cable', 'news')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured', 'is_pinned')
        }),
        ('Engagement', {
            'fields': ('upvotes', 'downvotes', 'reply_count', 'vote_score_display')
        }),
        ('Metadata', {
            'fields': ('user_agent', 'edited_at', 'edit_reason', 'is_reply_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    
    readonly_fields = [
        'wallet_address', 'balance', 'total_earned',
        'total_spent', 'transactions_count', 'discussions_count'
    ]
    
    fieldsets = (
        ('Blockchain Wallet', {
            'fields': ('wallet_address', 'public_key', 'balance')
        }),
        ('Statistics', {
            'fields': ('total_earned', 'total_spent', 'transactions_count', 'discussions_count'),
            'classes': ('collapse',)
        }),
        ('Profile Information', {
            'fields': ('avatar', 'bio', 'location', 'website')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'newsletter_subscription', 'theme'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('two_factor_enabled', 'last_login_ip', 'last_login_date'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_code', 'verification_expires'),
            'classes': ('collapse',)
        }),
        ('Cables', {
            'fields': ('cables_viewed', 'cables_favorited'),
            'classes': ('collapse',)
        }),
    )


class CustomUserAdmin(UserAdmin):
    """Custom User admin with profile inline"""
    inlines = [UserProfileInline]
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'date_joined',
        'profile_balance', 'profile_verified'
    ]
    
    def profile_balance(self, obj):
        if hasattr(obj, 'profile'):
            return f"{obj.profile.balance} ZETA"
        return "No profile"
    profile_balance.short_description = 'Balance'
    
    def profile_verified(self, obj):
        if hasattr(obj, 'profile'):
            if obj.profile.is_verified:
                return format_html(
                    '<span style="color: #4caf50;">✓ Verified</span>'
                )
            return format_html(
                '<span style="color: #ff9800;">Not verified</span>'
            )
        return "-"
    profile_verified.short_description = 'Verified'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


class SystemLogAdmin(admin.ModelAdmin):
    """Admin for SystemLog model"""
    
    list_display = [
        'created_at', 'level_badge', 'category_badge',
        'message_preview', 'source', 'user'
    ]
    
    list_filter = ['level', 'category', 'created_at', 'source']
    search_fields = ['message', 'details', 'source', 'traceback']
    readonly_fields = ['all_fields']
    date_hierarchy = 'created_at'
    
    def level_badge(self, obj):
        colors = {
            'debug': '#9e9e9e',
            'info': '#2196f3',
            'warning': '#ff9800',
            'error': '#f44336',
            'critical': '#d32f2f',
        }
        color = colors.get(obj.level, '#607d8b')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_level_display().upper()
        )
    level_badge.short_description = 'Level'
    
    def category_badge(self, obj):
        colors = {
            'blockchain': '#9c27b0',
            'cable': '#4caf50',
            'user': '#2196f3',
            'system': '#ff9800',
            'security': '#f44336',
            'api': '#3f51b5',
        }
        color = colors.get(obj.category, '#607d8b')
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def message_preview(self, obj):
        return obj.message[:100] + ('...' if len(obj.message) > 100 else '')
    message_preview.short_description = 'Message'
    
    def all_fields(self, obj):
        """Display all fields in a readable format"""
        fields = [
            f"<strong>Level:</strong> {obj.get_level_display()}",
            f"<strong>Category:</strong> {obj.get_category_display()}",
            f"<strong>Message:</strong> {obj.message}",
            f"<strong>Source:</strong> {obj.source or 'N/A'}",
            f"<strong>User:</strong> {obj.user or 'N/A'}",
            f"<strong>IP Address:</strong> {obj.ip_address or 'N/A'}",
            f"<strong>Request:</strong> {obj.request_method} {obj.request_path}",
            f"<strong>Created:</strong> {obj.created_at}",
        ]
        
        if obj.details:
            details_json = json.dumps(obj.details, indent=2)
            fields.append(f"<strong>Details:</strong><pre>{details_json}</pre>")
        
        if obj.traceback:
            fields.append(f"<strong>Traceback:</strong><pre>{obj.traceback}</pre>")
        
        return format_html('<br>'.join(fields))
    all_fields.short_description = 'Log Details'
    
    actions = ['delete_old_logs', 'export_logs']
    
    def delete_old_logs(self, request, queryset):
        """Delete logs older than 30 days"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=30)
        
        old_logs = SystemLog.objects.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        self.message_user(
            request,
            f"Deleted {count} log(s) older than 30 days."
        )
    delete_old_logs.short_description = "Delete logs older than 30 days"
    
    def export_logs(self, request, queryset):
        """Export selected logs as JSON"""
        import json
        from django.http import HttpResponse
        
        data = []
        for log in queryset:
            log_data = {
                'level': log.level,
                'category': log.category,
                'message': log.message,
                'source': log.source,
                'user': str(log.user) if log.user else None,
                'created_at': log.created_at.isoformat(),
                'details': log.details,
            }
            data.append(log_data)
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="system_logs_export.json"'
        return response
    export_logs.short_description = "Export selected logs as JSON"


class Z96AAdminSite(admin.AdminSite):
    """Custom admin site with dashboard"""
    
    site_header = "Z96A Network Administration"
    site_title = "Z96A Admin Portal"
    index_title = "Dashboard"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('blockchain-stats/', self.admin_view(self.blockchain_stats_view), name='blockchain-stats'),
            path('system-health/', self.admin_view(self.system_health_view), name='system-health'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view"""
        from django.db.models import Count, Sum, Avg
        
        # Basic statistics
        stats = {
            'total_cables': Cable.objects.count(),
            'active_cables': Cable.objects.filter(status='active').count(),
            'total_landing_points': LandingPoint.objects.count(),
            'total_equipment': Equipment.objects.count(),
            'total_transactions': BlockchainTransaction.objects.count(),
            'pending_transactions': BlockchainTransaction.objects.filter(status='pending').count(),
            'total_news': News.objects.count(),
            'published_news': News.objects.filter(is_published=True).count(),
            'total_discussions': Discussion.objects.count(),
            'approved_discussions': Discussion.objects.filter(is_approved=True).count(),
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
        }
        
        # Cable statistics
        cable_stats = Cable.objects.aggregate(
            total_length=Sum('length'),
            total_capacity=Sum('capacity'),
            avg_length=Avg('length'),
            avg_capacity=Avg('capacity')
        )
        
        # Blockchain statistics
        blockchain_stats = BlockchainTransaction.objects.aggregate(
            total_amount=Sum('amount'),
            avg_amount=Avg('amount'),
            total_fee=Sum('fee')
        )
        
        # Recent activities
        recent_transactions = BlockchainTransaction.objects.order_by('-created_at')[:10]
        recent_news = News.objects.filter(is_published=True).order_by('-published_date')[:5]
        recent_discussions = Discussion.objects.filter(is_approved=True).order_by('-created_at')[:5]
        
        context = {
            **self.each_context(request),
            'stats': stats,
            'cable_stats': cable_stats,
            'blockchain_stats': blockchain_stats,
            'recent_transactions': recent_transactions,
            'recent_news': recent_news,
            'recent_discussions': recent_discussions,
            'title': 'Dashboard Overview',
        }
        
        return render(request, 'admin/custom_dashboard.html', context)
    
    def blockchain_stats_view(self, request):
        """Blockchain statistics view"""
        from core.services.blockchain_service import BlockchainService
        
        blockchain = BlockchainService.get_blockchain()
        chain_info = blockchain.to_dict() if blockchain else {}
        
        # Transaction statistics
        tx_stats = BlockchainTransaction.objects.aggregate(
            total=Count('id'),
            confirmed=Count('id', filter=models.Q(status='confirmed')),
            pending=Count('id', filter=models.Q(status='pending')),
            failed=Count('id', filter=models.Q(status='failed')),
            total_amount=Sum('amount'),
            total_fee=Sum('fee')
        )
        
        # Transaction types
        tx_types = BlockchainTransaction.objects.values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-count')
        
        context = {
            **self.each_context(request),
            'chain_info': chain_info,
            'tx_stats': tx_stats,
            'tx_types': tx_types,
            'title': 'Blockchain Statistics',
        }
        
        return render(request, 'admin/blockchain_stats.html', context)
    
    def system_health_view(self, request):
        """System health monitoring view"""
        
        # Log statistics
        log_stats = SystemLog.objects.aggregate(
            total=Count('id'),
            errors=Count('id', filter=models.Q(level__in=['error', 'critical'])),
            warnings=Count('id', filter=models.Q(level='warning')),
            today=Count('id', filter=models.Q(created_at__date=timezone.now().date()))
        )
        
        # Recent errors
        recent_errors = SystemLog.objects.filter(
            level__in=['error', 'critical']
        ).order_by('-created_at')[:10]
        
        # Disk space (simplified)
        import os
        from django.conf import settings
        
        db_size = os.path.getsize(settings.DATABASES['default']['NAME']) if os.path.exists(
            settings.DATABASES['default']['NAME']) else 0
        
        # Convert to MB
        db_size_mb = db_size / (1024 * 1024)
        
        context = {
            **self.each_context(request),
            'log_stats': log_stats,
            'recent_errors': recent_errors,
            'db_size_mb': f"{db_size_mb:.2f} MB",
            'title': 'System Health',
        }
        
        return render(request, 'admin/system_health.html', context)


# Register models with custom admin site
admin_site = Z96AAdminSite(name='z96a_admin')

# Unregister default User admin and register custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register all models
admin.site.register(Region, RegionAdmin)
admin.site.register(Cable, CableAdmin)
admin.site.register(LandingPoint, LandingPointAdmin)
admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(BlockchainTransaction, BlockchainTransactionAdmin)
admin.site.register(News, NewsAdmin)
admin.site.register(Discussion, DiscussionAdmin)
admin.site.register(SystemLog, SystemLogAdmin)

# Also register with custom admin site
admin_site.register(Region, RegionAdmin)
admin_site.register(Cable, CableAdmin)
admin_site.register(LandingPoint, LandingPointAdmin)
admin_site.register(Equipment, EquipmentAdmin)
admin_site.register(BlockchainTransaction, BlockchainTransactionAdmin)
admin_site.register(News, NewsAdmin)
admin_site.register(Discussion, DiscussionAdmin)
admin_site.register(SystemLog, SystemLogAdmin)
admin_site.register(User, CustomUserAdmin)