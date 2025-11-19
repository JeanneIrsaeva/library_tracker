import React, { useState, useEffect, useRef } from 'react';
import './Chat.css';

const API_BASE_URL = 'http://localhost:8000';

const refreshAuthToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return data.access_token;
    } else {
      throw new Error('Token refresh failed');
    }
  } catch (error) {
    console.error('Token refresh error:', error);
    throw error;
  }
};

const authFetch = async (url, options = {}) => {
  let token = localStorage.getItem('token');
  
  const config = {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  };

  let response = await fetch(url, config);

  if (response.status === 401) {
    try {
      const newToken = await refreshAuthToken();
      config.headers['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, config);
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
      throw new Error('Authentication failed');
    }
  }

  return response;
};

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  const getCurrentUser = () => {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        id: payload.user_id,
        email: payload.email,
        role: payload.role
      };
    } catch (error) {
      console.error('Ошибка декодирования токена:', error);
      return null;
    }
  };

  const currentUser = getCurrentUser();

  const fetchChatHistory = async () => {
    try {
      const response = await authFetch(`${API_BASE_URL}/chat/messages?limit=50`);
      if (response.ok) {
        const data = await response.json();
        const formattedMessages = data.map(msg => ({
          ...msg,
          email: msg.is_admin ? 'Администратор' : (msg.email || `Пользователь ${msg.user_id}`)
        }));
        setMessages(formattedMessages);
      } else {
        console.error('Ошибка при загрузке истории сообщений:', response.status);
      }
    } catch (error) {
      console.error('Ошибка при загрузке истории сообщений:', error);
    }
  };

  const sendMessageViaAPI = async (messageText) => {
    try {
      const response = await authFetch(`${API_BASE_URL}/chat/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: messageText }),
      });

      if (response.ok) {
        const newMessage = await response.json();
        return newMessage;
      } else {
        console.error('Ошибка при отправке сообщения:', response.status);
        return null;
      }
    } catch (error) {
      console.error('Ошибка при отправке сообщения:', error);
      return null;
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('Требуется авторизация для использования чата');
      handleLogout();
      return;
    }

    fetchChatHistory();

    const ws = new WebSocket('ws://localhost:8080');

    ws.onopen = (e) => {
      console.log('WebSocket соединение установлено');
      setIsConnected(true);
      
      ws.send(JSON.stringify({
        type: 'auth',
        token: token
      }));

      setTimeout(() => {
        ws.send(JSON.stringify({
          type: 'get_history',
          token: token
        }));
      }, 500);
    };

    ws.onclose = (e) => {
      console.log('WebSocket соединение закрыто');
      setIsConnected(false);
    };

    ws.onerror = (e) => {
      console.error('WebSocket ошибка:', e);
      setIsConnected(false);
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        console.log('Получено сообщение:', data);

        if (data.type === 'user_message') {
          const newMessage = {
            id: data.message_id || Date.now(),
            user_id: data.user_id,
            message: data.message,
            is_admin: 0, 
            created_at: data.timestamp || new Date().toISOString(),
            email: data.email || `Пользователь ${data.user_id}`
          };
          
          setMessages(prev => [...prev, newMessage]);
          
        } else if (data.type === 'admin_message') {
          const newMessage = {
            id: data.message_id || Date.now(),
            user_id: data.user_id,
            message: data.message,
            is_admin: 1,
            created_at: data.timestamp || new Date().toISOString(),
            email: 'Администратор'
          };
          
          setMessages(prev => [...prev, newMessage]);
          
        } else if (data.type === 'chat_history') {
          
          const formattedMessages = (data.messages || []).map(msg => ({
            ...msg,
            email: msg.is_admin ? 'Администратор' : (msg.email || `Пользователь ${msg.user_id}`)
          }));
          setMessages(formattedMessages);
          
        } else if (data.type === 'message_sent') {
          console.log('Сообщение доставлено:', data.message_id);
          
        } else if (data.type === 'user_connected') {
          console.log(`Пользователь ${data.user_id} подключился к чату`);
          
        } else if (data.type === 'typing_start') {
          setIsTyping(true);
        } else if (data.type === 'typing_stop') {
          setIsTyping(false);
        } else if (data.type === 'auth_error') {
          console.error('Ошибка аутентификации в WebSocket:', data.message);
          handleLogout();
        }
      } catch (error) {
        console.error('Ошибка обработки сообщения:', error);
      }
    };

    setSocket(ws);

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ 
      behavior: 'smooth',
      block: 'end'
    });
  }, [messages, isTyping]);

  const sendMessage = async () => {
    if (!newMessage.trim() || !socket || !isConnected) return;

    const token = localStorage.getItem('token');
    
    
    const messageType = currentUser?.role === 'admin' ? 'admin_message' : 'message';
    
    socket.send(JSON.stringify({
      type: messageType,
      token: token,
      message: newMessage.trim(),
      ...(currentUser?.role === 'admin' && { target_user_id: getTargetUserId() }) 
    }));

    if (currentUser?.role !== 'admin') {
      try {
        await sendMessageViaAPI(newMessage.trim());
      } catch (error) {
        console.error('Ошибка при сохранении сообщения через API:', error);
      }
    }

    if (currentUser?.role !== 'admin') {
      const myMessage = {
        id: Date.now(),
        user_id: currentUser?.id,
        message: newMessage.trim(),
        is_admin: 0,
        created_at: new Date().toISOString(),
        email: 'Вы'
      };
      setMessages(prev => [...prev, myMessage]);
    }

    setNewMessage('');
  };

  const getTargetUserId = () => {
    if (messages.length === 0) return null;
    
    const lastUserMessage = [...messages].reverse().find(msg => !msg.is_admin);
    return lastUserMessage ? lastUserMessage.user_id : null;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInputChange = (e) => {
    setNewMessage(e.target.value);
    
    if (socket && isConnected) {
      const token = localStorage.getItem('token');
      socket.send(JSON.stringify({
        type: 'typing_start',
        token: token
      }));
      
      setTimeout(() => {
        if (socket && isConnected) {
          socket.send(JSON.stringify({
            type: 'typing_stop',
            token: token
          }));
        }
      }, 1000);
    }
  };
  const isMyMessage = (message) => {
    if (currentUser?.role === 'admin') {
      return message.is_admin === 1;
    } else {
      return message.user_id === currentUser?.id && message.is_admin === 0;
    }
  };

  const groupMessagesByDate = (messages) => {
    const groups = {};
    messages.forEach(message => {
      const date = new Date(message.created_at).toLocaleDateString('ru-RU');
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(message);
    });
    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toLocaleDateString() === today.toLocaleDateString()) {
      return 'Сегодня';
    } else if (date.toLocaleDateString() === yesterday.toLocaleDateString()) {
      return 'Вчера';
    } else {
      return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    }
  };

  const getDisplayName = (message) => {
    if (isMyMessage(message)) {
      return currentUser?.role === 'admin' ? 'Вы (Админ)' : 'Вы';
    } else {
      return message.is_admin ? 'Администратор' : (message.email || `Пользователь ${message.user_id}`);
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        <div className="chat-header">
          <h2>
            {currentUser?.role === 'admin' ? '💬 Чат поддержки (Администратор)' : '💬 Чат поддержки'}
          </h2>
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <div className="status-dot"></div>
            {isConnected ? 'Подключено' : 'Отключено'}
          </div>
        </div>

        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="no-messages">
              <p>
                {currentUser?.role === 'admin' 
                  ? 'Ожидайте сообщений от пользователей' 
                  : 'Начните общение! Задайте ваш вопрос'}
              </p>
              <p style={{ fontSize: '0.9rem', marginTop: '0.5rem', opacity: '0.6' }}>
                {currentUser?.role === 'admin' 
                  ? 'Сообщения пользователей появятся здесь' 
                  : 'Администратор ответит вам в ближайшее время'}
              </p>
            </div>
          ) : (
            Object.entries(messageGroups).map(([date, dateMessages]) => (
              <div key={date}>
                <div className="date-divider">
                  <span>{formatDate(dateMessages[0].created_at)}</span>
                </div>
                {dateMessages.map(message => {
                  const messageClass = isMyMessage(message) ? 'my-message' : 'admin-message';
                  const displayName = getDisplayName(message);
                  
                  return (
                    <div key={message.id} className={messageClass}>
                      <div className="message-content">
                        <div className="message-header">
                          <span className="message-sender">{displayName}</span>
                          <span className="message-time">
                            {formatTime(message.created_at)}
                          </span>
                        </div>
                        <div className="message-text">{message.message}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))
          )}
          
          {isTyping && (
            <div className="typing-indicator">
              <span className="typing-dots">печатает</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="message-input-container">
          <input
            type="text"
            value={newMessage}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={
              isConnected 
                ? currentUser?.role === 'admin' 
                  ? "Введите ответ пользователю..." 
                  : "Введите ваш вопрос..."
                : "Подключение..."
            }
            disabled={!isConnected}
            maxLength={500}
          />
          <button 
            onClick={sendMessage} 
            disabled={!isConnected || !newMessage.trim()}
            className="send-button"
          >
            Отправить
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;