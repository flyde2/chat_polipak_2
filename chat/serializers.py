from rest_framework import serializers
from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'manager', 'client', 'created_at', 'unread_count']
        read_only_fields = ['manager', 'created_at']

    def get_unread_count(self, obj):
        user = self.context['request'].user
        if user == obj.manager:
            return obj.messages.filter(sender=obj.client,
                                       is_read=False).count()
        elif user == obj.client:
            return obj.messages.filter(sender=obj.manager,
                                       is_read=False).count()
        return 0


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'timestamp', 'is_read']
        read_only_fields = ['chat', 'sender', 'timestamp', 'is_read']
