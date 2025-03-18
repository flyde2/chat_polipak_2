from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_CHOICES = (
        ('manager', 'Manager'),
        ('client', 'Client'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)


class Chat(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='managed_chats')
    client = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='client_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('manager', 'client')


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE,
                             related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
