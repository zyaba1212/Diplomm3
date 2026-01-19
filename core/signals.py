"""
Сигналы Django для автоматических действий при событиях
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserProposal, Comment


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создание профиля при создании пользователя Django"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=UserProposal)
def update_user_reputation_on_proposal(sender, instance, created, **kwargs):
    """Обновление репутации пользователя при изменении статуса предложения"""
    if not created and instance.status_changed():
        user_profile = instance.user
        
        # Начисление/снятие репутации в зависимости от статуса
        reputation_changes = {
            'APPROVED': 10,
            'REJECTED': -5,
            'IMPLEMENTED': 25,
        }
        
        if instance.status in reputation_changes:
            user_profile.reputation += reputation_changes[instance.status]
            user_profile.save()


@receiver(post_save, sender=Comment)
def update_discussion_stats(sender, instance, created, **kwargs):
    """Обновление статистики обсуждения при добавлении комментария"""
    if created:
        discussion = instance.discussion
        discussion.comment_count = discussion.comments.count()
        discussion.save(update_fields=['comment_count'])


@receiver(pre_save, sender=UserProfile)
def validate_nickname_uniqueness(sender, instance, **kwargs):
    """Проверка уникальности никнейма перед сохранением"""
    if instance.nickname:
        # Проверяем, не занят ли никнейм другим пользователем
        existing = UserProfile.objects.filter(
            nickname=instance.nickname
        ).exclude(id=instance.id).exists()
        
        if existing:
            # Генерируем уникальный никнейм
            from .blockchain import generate_nickname
            while True:
                new_nickname = generate_nickname()
                if not UserProfile.objects.filter(nickname=new_nickname).exists():
                    instance.nickname = new_nickname
                    break