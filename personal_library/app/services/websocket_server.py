import asyncio
import websockets
import json
from typing import Set, Dict
from app.utils.jwt import verify_token

class ChatServer:
    """
    Класс чата, реализующий всю логику работы с WebSocket соединениями
    Соответствует требованиям методички 2.5
    """
    
    def __init__(self):
        # Хранилище подключенных клиентов
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        # Связь пользователей с их соединениями
        self.user_connections: Dict[int, websockets.WebSocketServerProtocol] = {}
        # Администраторы онлайн
        self.admin_connections: Set[websockets.WebSocketServerProtocol] = set()
        
        print("✅ ChatServer инициализирован")

    async def on_open(self, websocket: websockets.WebSocketServerProtocol):
        """Функция обработки подключения нового клиента"""
        self.connected_clients.add(websocket)
        print(f"🔗 Новое подключение. Всего клиентов: {len(self.connected_clients)}")
        
        # Отправляем приветственное сообщение
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket соединение установлено. Пройдите аутентификацию.'
        }))

    async def on_close(self, websocket: websockets.WebSocketServerProtocol):
        """Функция обработки закрытия соединения с клиентом"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        
        # Удаляем из user_connections
        user_id = None
        for uid, ws in list(self.user_connections.items()):
            if ws == websocket:
                user_id = uid
                break
        if user_id:
            del self.user_connections[user_id]
            print(f"👋 Пользователь {user_id} отключился")
        
        # Удаляем из admin_connections
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
            print(f"👋 Администратор отключился")
        
        print(f"🔌 Соединение закрыто. Осталось клиентов: {len(self.connected_clients)}")

    async def on_error(self, websocket: websockets.WebSocketServerProtocol, error: Exception):
        """Функция обработки ошибочного закрытия соединения"""
        print(f"❌ WebSocket ошибка: {error}")
        await self.on_close(websocket)

    async def on_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Основная функция обработки входящих сообщений"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'auth':
                await self.handle_auth(websocket, data)
            elif message_type == 'message':
                await self.handle_user_message(websocket, data)
            elif message_type == 'admin_message':
                await self.handle_admin_message(websocket, data)
            elif message_type == 'get_history':
                await self.handle_get_history(websocket, data)
            else:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'Неизвестный тип сообщения'
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Неверный формат JSON'
            }))
        except Exception as e:
            print(f"❌ Ошибка обработки сообщения: {e}")
            await self.on_error(websocket, e)

    async def handle_auth(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Обработка аутентификации"""
        token = data.get('token')
        user_data = verify_token(token)
        
        if not user_data:
            await websocket.send(json.dumps({
                'type': 'auth_error',
                'message': 'Неверный токен'
            }))
            return

        user_id = user_data.get('user_id')
        role = user_data.get('role')
        
        if role == 'admin':
            self.admin_connections.add(websocket)
            await websocket.send(json.dumps({
                'type': 'auth_success',
                'role': role,
                'message': 'Вы подключены как администратор'
            }))
            print(f"🛡️ Администратор {user_id} подключился к чату")
        else:
            self.user_connections[user_id] = websocket
            await websocket.send(json.dumps({
                'type': 'auth_success',
                'role': role,
                'message': 'Вы подключены к чату поддержки'
            }))
            print(f"👤 Пользователь {user_id} подключился к чату")
            
            # Уведомляем всех администраторов о новом пользователе
            await self.notify_admins_about_new_user(user_id)

    async def handle_user_message(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Обработка сообщений от пользователей"""
        token = data.get('token')
        user_data = verify_token(token)
        
        if not user_data:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Требуется аутентификация'
            }))
            return
        
        user_id = user_data.get('user_id')
        message_text = data.get('message', '').strip()
        
        if not message_text:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Сообщение не может быть пустым'
            }))
            return
        
        # Сохраняем сообщение в базу данных
        from app.database import SessionLocal
        from app.models.chat import ChatMessage
        
        db = SessionLocal()
        try:
            db_message = ChatMessage(
                user_id=user_id,
                message=message_text,
                is_admin=0  # Сообщение от пользователя
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            # Отправляем сообщение всем администраторам
            await self.broadcast_to_admins({
                'type': 'user_message',
                'user_id': user_id,
                'message': message_text,
                'timestamp': db_message.created_at.isoformat(),
                'message_id': db_message.id
            })
            
            # Подтверждение пользователю
            await websocket.send(json.dumps({
                'type': 'message_sent',
                'message_id': db_message.id,
                'timestamp': db_message.created_at.isoformat()
            }))
            
            print(f"💬 Пользователь {user_id} отправил сообщение: {message_text}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщения: {e}")
            db.rollback()
        finally:
            db.close()

    async def handle_admin_message(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Обработка сообщений от администраторов"""
        token = data.get('token')
        user_data = verify_token(token)
        
        if not user_data or user_data.get('role') != 'admin':
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Требуются права администратора'
            }))
            return
        
        target_user_id = data.get('target_user_id')
        message_text = data.get('message', '').strip()
        
        if not target_user_id or not message_text:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Не указан пользователь или сообщение'
            }))
            return
        
        # Сохраняем сообщение в базу данных
        from app.database import SessionLocal
        from app.models.chat import ChatMessage
        
        db = SessionLocal()
        try:
            db_message = ChatMessage(
                user_id=target_user_id,  # Сохраняем от имени пользователя, но помечаем как админское
                message=message_text,
                is_admin=1  # Сообщение от администратора
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            # Отправляем сообщение конкретному пользователю
            if target_user_id in self.user_connections:
                await self.user_connections[target_user_id].send(json.dumps({
                    'type': 'admin_message',
                    'message': message_text,
                    'timestamp': db_message.created_at.isoformat(),
                    'message_id': db_message.id
                }))
            
            # Подтверждение администратору
            await websocket.send(json.dumps({
                'type': 'message_sent',
                'message_id': db_message.id,
                'timestamp': db_message.created_at.isoformat()
            }))
            
            print(f"🛡️ Админ ответил пользователю {target_user_id}: {message_text}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщения админа: {e}")
            db.rollback()
        finally:
            db.close()

    async def handle_get_history(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Обработка запроса истории сообщений"""
        token = data.get('token')
        user_data = verify_token(token)
        
        if not user_data:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Требуется аутентификация'
            }))
            return
        
        from app.database import SessionLocal
        from app.models.chat import ChatMessage
        
        db = SessionLocal()
        try:
            user_id = user_data.get('user_id')
            role = user_data.get('role')
            
            if role == 'admin':
                # Админы видят все сообщения
                messages = db.query(ChatMessage).order_by(ChatMessage.created_at).limit(50).all()
            else:
                # Пользователи видят только свои сообщения
                messages = db.query(ChatMessage).filter(
                    ChatMessage.user_id == user_id
                ).order_by(ChatMessage.created_at).limit(50).all()
            
            await websocket.send(json.dumps({
                'type': 'chat_history',
                'messages': [
                    {
                        'id': msg.id,
                        'user_id': msg.user_id,
                        'message': msg.message,
                        'is_admin': msg.is_admin,
                        'created_at': msg.created_at.isoformat()
                    } for msg in messages
                ]
            }))
            
        except Exception as e:
            print(f"❌ Ошибка получения истории: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Ошибка получения истории сообщений'
            }))
        finally:
            db.close()

    async def broadcast_to_admins(self, message: dict):
        """Рассылка сообщения всем администраторам"""
        message_json = json.dumps(message)
        for admin_ws in self.admin_connections:
            try:
                await admin_ws.send(message_json)
            except Exception as e:
                print(f"❌ Ошибка отправки админу: {e}")

    async def notify_admins_about_new_user(self, user_id: int):
        """Уведомление администраторов о новом подключенном пользователе"""
        await self.broadcast_to_admins({
            'type': 'user_connected',
            'user_id': user_id,
            'message': f'Пользователь {user_id} подключился к чату'
        })

    async def handler(self, websocket: websockets.WebSocketServerProtocol):
        """Основной обработчик WebSocket соединений (новая сигнатура)"""
        await self.on_open(websocket)
        try:
            async for message in websocket:
                await self.on_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket соединение закрыто клиентом")
        except Exception as e:
            print(f"❌ Ошибка в WebSocket обработчике: {e}")
            await self.on_error(websocket, e)
        finally:
            await self.on_close(websocket)

# Глобальный экземпляр чат-сервера
chat_server = ChatServer()

# Функция-обработчик для WebSocket сервера (исправленная сигнатура)
async def websocket_handler(websocket: websockets.WebSocketServerProtocol):
    """
    Обработчик WebSocket соединений
    Новая сигнатура без параметра path для совместимости с websockets>=11.0
    """
    await chat_server.handler(websocket)