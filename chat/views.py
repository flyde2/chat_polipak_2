from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
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
        if Chat.objects.filter(manager=self.request.user,
                               client=client).exists():
            raise ValidationError("Чат уже существует.")
        serializer.save(manager=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipant]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        chat = get_object_or_404(Chat, id=chat_id)
        return Message.objects.filter(chat=chat)

    def perform_create(self, serializer):
        chat_id = self.kwargs['chat_id']
        chat = get_object_or_404(Chat, id=chat_id)
        user = self.request.user
        if user.profile.role == 'client' and user != chat.client:
            raise PermissionDenied(
                "Клиент может отправлять только сообщения в своем чате.")
        serializer.save(chat=chat, sender=user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        user = request.user
        chat_id = self.kwargs['chat_id']
        chat = get_object_or_404(Chat, id=chat_id)

        if user.profile.role == 'manager':
            Message.objects.filter(chat=chat, sender=chat.client,
                                   is_read=False).update(is_read=True)
        elif user.profile.role == 'client':
            Message.objects.filter(chat=chat, sender=chat.manager,
                                   is_read=False).update(is_read=True)

        return response
