from rest_framework import permissions
from .models import Chat


class IsParticipant(permissions.BasePermission):
    def has_permission(self, request, view):
        if 'chat_id' in view.kwargs:
            chat = Chat.objects.get(id=view.kwargs['chat_id'])
            return request.user in [chat.manager, chat.client]
        return True

    def has_object_permission(self, request, view, obj):
        return request.user in [obj.chat.manager, obj.chat.client]
