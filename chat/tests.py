from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Chat, Message, Profile


class ChatViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='manager',
                                                password='password')
        Profile.objects.create(user=self.manager, role='manager')
        self.client_user = User.objects.create_user(username='client',
                                                    password='password')
        Profile.objects.create(user=self.client_user, role='client')
        self.another_client = User.objects.create_user(
            username='another_client', password='password')
        Profile.objects.create(user=self.another_client, role='client')

    def test_manager_can_create_chat(self):
        self.client.login(username='manager', password='password')
        data = {'client': self.client_user.id}
        response = self.client.post('/chats/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         msg="Менеджер должен иметь возможность создать чат")
        self.assertEqual(Chat.objects.count(), 1,
                         msg="Должен быть создан один чат")

    def test_client_cannot_create_chat(self):
        self.client.login(username='client', password='password')
        data = {'client': self.another_client.id}
        response = self.client.post('/chats/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         msg="Клиент не должен иметь возможность создать чат")
        self.assertEqual(Chat.objects.count(), 0,
                         msg="Чат не должен быть создан")

    def test_manager_can_only_see_their_chats(self):
        self.client.login(username='manager', password='password')
        Chat.objects.create(manager=self.manager, client=self.client_user)
        Chat.objects.create(manager=self.manager, client=self.another_client)

        response = self.client.get('/chats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg="Менеджер должен иметь возможность видеть свои чаты")
        self.assertEqual(len(response.data), 2,
                         msg="Менеджер должен видеть два чата")

    def test_total_unread_count_for_manager(self):
        chat = Chat.objects.create(manager=self.manager,
                                   client=self.client_user)
        Message.objects.create(chat=chat, sender=self.client_user,
                               text="client msg1", is_read=False)
        Message.objects.create(chat=chat, sender=self.client_user,
                               text="client msg2", is_read=False)
        self.client.login(username='manager', password='password')
        response = self.client.get('/chats/total_unread_count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg="Статус должен быть 200 при обращении к "
                             "+total_unread_count")
        self.assertEqual(response.data['unread_count'], 2,
                         msg="Ожидаем 2 непрочитанных сообщения от клиента")

    def test_total_unread_count_for_client(self):
        chat = Chat.objects.create(manager=self.manager,
                                   client=self.client_user)
        Message.objects.create(chat=chat, sender=self.manager,
                               text="manager msg1", is_read=False)
        Message.objects.create(chat=chat, sender=self.manager,
                               text="manager msg2", is_read=False)
        self.client.login(username='client', password='password')
        response = self.client.get('/chats/total_unread_count/')
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg="Статус должен быть 200 при обращении к "
                             "total_unread_count")
        self.assertEqual(response.data['unread_count'], 2,
                         msg="Ожидаем 2 непрочитанных сообщения от менеджера")

    def test_manager_can_update_chat(self):
        self.client.login(username='manager', password='password')
        chat = Chat.objects.create(manager=self.manager,
                                   client=self.client_user)
        data = {'client': self.another_client.id}
        response = self.client.patch(f'/chats/{chat.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg="Менеджер должен иметь возможность изменять чат")

        chat.refresh_from_db()
        self.assertEqual(chat.client.id, self.another_client.id,
                         msg="Клиент чата должен измениться на another_client")

    def test_client_cannot_update_chat(self):
        self.client.login(username='client', password='password')
        chat = Chat.objects.create(manager=self.manager,
                                   client=self.client_user)

        data = {'client': self.another_client.id}
        response = self.client.patch(f'/chats/{chat.id}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         msg="Клиент не должен иметь права изменять чат")
        chat.refresh_from_db()
        self.assertNotEqual(chat.client.id, self.another_client.id,
                            msg="Чат не должен был измениться")

    def test_manager_can_delete_chat(self):
        self.client.login(username='manager', password='password')
        chat = Chat.objects.create(manager=self.manager,
                                   client=self.client_user)

        response = self.client.delete(f'/chats/{chat.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT,
                         msg="Менеджер должен иметь возможность удалить чат")
        self.assertFalse(Chat.objects.filter(id=chat.id).exists(),
                         msg="Чат не должен существовать после удаления")

    def test_client_cannot_delete_chat(self):
        self.client.login(username='client', password='password')
        chat = Chat.objects.create(manager=self.manager,
                                   client=self.client_user)

        response = self.client.delete(f'/chats/{chat.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         msg="Клиент не должен иметь права удалять чат")
        self.assertTrue(Chat.objects.filter(id=chat.id).exists(),
                        msg="Чат по-прежнему должен существовать")


class ChatMessageViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.manager = User.objects.create_user(username='manager',
                                                password='password')
        Profile.objects.create(user=self.manager, role='manager')
        self.client_user = User.objects.create_user(username='client',
                                                    password='password')
        Profile.objects.create(user=self.client_user, role='client')

        self.chat = Chat.objects.create(manager=self.manager,
                                        client=self.client_user)

    def test_manager_can_send_message_in_their_chat(self):
        self.client.login(username='manager', password='password')
        data = {'text': 'Message from manager'}
        response = self.client.post(f'/chats/{self.chat.id}/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)

    def test_client_can_send_message_in_their_chat(self):
        self.client.login(username='client', password='password')
        data = {'text': 'Test message', 'chat': self.chat.id}
        response = self.client.post(f'/chats/{self.chat.id}/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_manager_can_read_messages(self):  # New test
        self.client.login(username='client', password='password')
        message = Message.objects.create(chat=self.chat,
                                         sender=self.client_user,
                                         text="Непрочитанное "
                                              "сообщение клиента",
                                         is_read=False)

        self.client.logout()  # Logout client
        self.client.login(username='manager', password='password')
        response = self.client.get(f'/chats/{self.chat.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Message.objects.get(id=message.id).is_read)

    def test_client_can_read_messages(self):
        self.client.login(username='manager', password='password')
        message = Message.objects.create(chat=self.chat, sender=self.manager,
                                         text="Непрочитанное "
                                              "сообщение менеджера",
                                         is_read=False)

        self.client.logout()
        self.client.login(username='client', password='password')
        response = self.client.get(f'/chats/{self.chat.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Message.objects.get(id=message.id).is_read)

    def test_messages_marked_as_read_on_list(self):
        Message.objects.create(chat=self.chat, sender=self.client_user,
                               text="Непрочитанное сообщение клиента 1",
                               is_read=False)
        Message.objects.create(chat=self.chat, sender=self.manager,
                               text="Непрочитанное сообщение менеджера 1",
                               is_read=False)

        self.client.login(username='client', password='password')
        self.client.get(f'/chats/{self.chat.id}/messages/')

        self.assertTrue(all(msg.is_read for msg in
                            Message.objects.filter(chat=self.chat,
                                                   sender=self.manager)))

        Message.objects.create(chat=self.chat, sender=self.client_user,
                               text="Непрочитанное сообщение клиента 2",
                               is_read=False)

        self.client.logout()
        self.client.login(username='manager', password='password')
        self.client.get(f'/chats/{self.chat.id}/messages/')
        self.assertTrue(all(msg.is_read for msg in
                            Message.objects.filter(chat=self.chat,
                                                   sender=self.client_user)))
