from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, ChatMessageViewSet

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'chats/(?P<chat_id>\d+)/messages', ChatMessageViewSet,
                basename='messages')

urlpatterns = [
    path('', include(router.urls)),
]
