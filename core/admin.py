from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    UserProfile, BlockchainTransaction, NetworkElement,
    NetworkConnection, NewsArticle, Comment, Proposal
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

@admin.register(BlockchainTransaction)
class BlockchainTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'user', 'solana_tx_hash', 'verified', 'created_at')
    list_filter = ('transaction_type', 'verified', 'created_at')
    search_fields = ('solana_tx_hash', 'user__nickname', 'user__wallet_address')
    readonly_fields = ('created_at',)

@admin.register(NetworkElement)
class NetworkElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'element_type', 'network_type', 'latitude', 'longitude', 'is_active')
    list_filter = ('element_type', 'network_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'element_id')
    filter_horizontal = ()

@admin.register(NetworkConnection)
class NetworkConnectionAdmin(admin.ModelAdmin):
    list_display = ('from_element', 'to_element', 'connection_type')
    list_filter = ('connection_type',)
    search_fields = ('from_element__name', 'to_element__name')

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_date', 'is_active')
    list_filter = ('source', 'is_active', 'published_date')
    search_fields = ('title', 'content')
    readonly_fields = ('parsed_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_preview', 'created_at', 'likes')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__nickname')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'proposal_type', 'status', 'created_at')
    list_filter = ('status', 'proposal_type', 'created_at')
    search_fields = ('description', 'user__nickname')
    readonly_fields = ('created_at',)
    actions = ['approve_proposals', 'reject_proposals']
    
    def approve_proposals(self, request, queryset):
        queryset.update(status='approved')
    approve_proposals.short_description = _("Approve selected proposals")
    
    def reject_proposals(self, request, queryset):
        queryset.update(status='rejected')
    reject_proposals.short_description = _("Reject selected proposals")

admin.site.unregister(User)
admin.site.register(User, UserAdmin)