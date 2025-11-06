from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import logging
import asyncio
import threading
import websockets

from app.controllers.book_controller import router as book_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.chat_controller import router as chat_router
from app.database import create_tables
from app.services.websocket_server import websocket_handler  # Импортируем новый обработчик

# Импорты моделей для Alembic
from app.models import book, user, chat

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Личная библиотека",
    description="API для управления личной библиотекой книг с чатом поддержки",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
    ],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Личная библиотека",
        version="1.0.0",
        description="API для управления личной библиотекой книг с чатом поддержки",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите JWT токен в формате: Bearer <token>"
        }
    }
    
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "patch", "delete"]:
                if not path.startswith("/auth"):
                    openapi_schema["paths"][path][method]["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

async def run_websocket_server():
    """Запуск WebSocket сервера"""
    try:
        # Пробуем разные порты если 8080 занят
        ports = [8080, 8081, 8082, 8083]
        for port in ports:
            try:
                # Используем новую сигнатуру без path
                server = await websockets.serve(
                    websocket_handler, 
                    "localhost", 
                    port
                )
                print(f"✅ WebSocket Chat Server запущен на ws://localhost:{port}")
                print(f"📝 Протокол: WebSocket")
                print(f"🎯 Назначение: Чат технической поддержки")
                print(f"👥 Участники: Пользователи ↔ Администраторы")
                
                # Бесконечный цикл ожидания
                await asyncio.Future()
                return
                
            except OSError as e:
                if "10048" in str(e) or "Address already in use" in str(e):
                    print(f"⚠️  Порт {port} занят, пробуем следующий...")
                    continue
                else:
                    raise e
        
        print("❌ Все порты заняты! WebSocket сервер не запущен.")
        
    except Exception as e:
        print(f"❌ Не удалось запустить WebSocket сервер: {e}")

def start_websocket_server():
    """Запуск WebSocket сервера в отдельном потоке"""
    try:
        # Создаем новую event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_websocket_server())
    except Exception as e:
        print(f"❌ Ошибка в WebSocket сервере: {e}")

@app.on_event("startup")
def on_startup():
    """Запуск приложения"""
    create_tables()
    print("✅ База данных инициализирована")
    
    # Запускаем WebSocket сервер в отдельном потоке
    websocket_thread = threading.Thread(target=start_websocket_server, daemon=True)
    websocket_thread.start()
    print("🔄 Запуск WebSocket сервера в фоновом режиме...")

# Подключаем роутеры
app.include_router(book_router)
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в личную библиотеку!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "personal-library-api"}

@app.get("/websocket-info")
def websocket_info():
    """Информация о WebSocket соединении"""
    return {
        "websocket_url": "ws://localhost:8080",
        "protocol": "WebSocket",
        "purpose": "Чат технической поддержки",
        "features": [
            "Аутентификация по JWT токену",
            "Общение пользователей с администраторами", 
            "Сохранение истории сообщений",
            "Уведомления о новых пользователях"
        ]
    }