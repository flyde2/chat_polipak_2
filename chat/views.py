from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from .permissions import IsParticipant
from rest_framework.permissions import IsAuthenticated


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.profile.role == 'manager':
            return Chat.objects.filter(manager=user)
        elif user.profile.role == 'client':
            return Chat.objects.filter(client=user)
        return Chat.objects.none()

    def perform_create(self, serializer):
        if self.request.user.profile.role != 'manager':
            raise PermissionDenied("Только менеджеры могут создавать чаты.")
        client = serializer.validated_data['client']
        if client.profile.role != 'client':
            raise ValidationError("Указанный пользователь не клиент.")
        if client == self.request.user:
            raise ValidationError("Менеджер не может "
                                  "создать чат с самими собой.")
        if Chat.objects.filter(manager=self.request.user,
                               client=client).exists():
            raise ValidationError("Чат уже существует.")
        serializer.save(manager=self.request.user)

    @action(detail=False, methods=['get'])
    def total_unread_count(self, request):
        user = request.user
        if user.profile.role == 'manager':
            unread_count = Message.objects.filter(
                chat__manager=user,
                sender__profile__role='client',
                is_read=False
            ).count()
        else:
            unread_count = Message.objects.filter(
                chat__client=user,
                sender__profile__role='manager',
                is_read=False
            ).count()
        return Response({'unread_count': unread_count})


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipant]

    def get_chat(self):
        chat_id = self.kwargs.get('chat_id')
        return get_object_or_404(Chat, id=chat_id)

    def get_queryset(self):
        chat = self.get_chat()
        return Message.objects.filter(chat=chat)

    def perform_create(self, serializer):
        chat = self.get_chat()
        user = self.request.user
        if user.profile.role == 'client' and user != chat.client:
            raise PermissionDenied(
                "Клиент может отправлять только сообщения в своем чате.")
        serializer.save(chat=chat, sender=user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        user = request.user
        chat = self.get_chat()
        if user.profile.role == 'manager':
            Message.objects.filter(chat=chat, sender=chat.client,
                                   is_read=False).update(is_read=True)
        elif user.profile.role == 'client':
            Message.objects.filter(chat=chat, sender=chat.manager,
                                   is_read=False).update(is_read=True)
        return response
