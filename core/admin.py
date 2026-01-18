from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профили пользователей'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description')
    search_fields = ('name', 'code')

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'capital', 'region')
    list_filter = ('region',)
    search_fields = ('name', 'code')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city_type', 'is_hub', 'latitude', 'longitude')
    list_filter = ('city_type', 'is_hub', 'country__region')
    search_fields = ('name', 'country__name')

@admin.register(Cable)
class CableAdmin(admin.ModelAdmin):
    list_display = ('name', 'cable_type', 'capacity', 'length', 'year', 'is_active')
    list_filter = ('cable_type', 'is_active', 'year')
    search_fields = ('name', 'cable_id')

@admin.register(CableRoute)
class CableRouteAdmin(admin.ModelAdmin):
    list_display = ('cable', 'order', 'location_name', 'latitude', 'longitude')
    list_filter = ('cable',)
    ordering = ('cable', 'order')

@admin.register(BlockchainTransaction)
class BlockchainTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'user', 'solana_tx_hash', 'verified', 'created_at')
    list_filter = ('transaction_type', 'verified', 'created_at')
    search_fields = ('solana_tx_hash', 'user__nickname')
    readonly_fields = ('created_at',)

@admin.register(NetworkElement)
class NetworkElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'element_type', 'network_type', 'city', 'is_active')
    list_filter = ('element_type', 'network_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'element_id')

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
    list_display = ('user', 'content_preview', 'created_at', 'likes', 'dislikes')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__nickname')
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Содержание'

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'proposal_type', 'status', 'created_at')
    list_filter = ('status', 'proposal_type', 'created_at')
    search_fields = ('description', 'user__nickname')
    readonly_fields = ('created_at',)
    actions = ['approve_proposals', 'reject_proposals']
    
    def approve_proposals(self, request, queryset):
        queryset.update(status='approved')
    approve_proposals.short_description = "Одобрить выбранные предложения"
    
    def reject_proposals(self, request, queryset):
        queryset.update(status='rejected')
    reject_proposals.short_description = "Отклонить выбранные предложения"

admin.site.unregister(User)
admin.site.register(User, UserAdmin)