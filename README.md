## Модели
### Chat
- manager (User) - менеджер чата
- client (User) - клиент чата
- created_at - дата создания

### Message
- chat (Chat) - принадлежность к чату
- sender (User) - отправитель
- text - текст сообщения
- created_at - дата отправки
- is_read - статус прочтения


## API Endpoints

### Чат-комнаты
GET /api/chats/  
- Получение списка чатов (для менеджеров - их чаты, для клиентов - где они участники)

POST /api/chats/  
- Создание нового чата (только для менеджеров)
json
{
    "client": 1
}


### Сообщения в чате
GET /api/chats/{chat_id}/messages/  
- Получение истории сообщений
- Автоматически помечает сообщения как прочитанные:
  - Для менеджеров - сообщения от клиента
  - Для клиентов - сообщения от менеджера

POST /api/chats/{chat_id}/messages/  
- Отправка нового сообщения
json
{
    "text": "Сообщение"
}


## Правила доступа
1. Только аутентифицированные пользователи
2. Создавать чаты могут только менеджеры
3. Клиенты могут писать только в своих чатах
4. Просматривать чат могут только его участники
5. Повторное создание чата с тем же клиентом запрещено



