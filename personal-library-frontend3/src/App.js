import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import BookList from './components/BookList';
import BookForm from './components/BookForm';
import BookView from './components/BookView';
import AuthForm from './components/AuthForm';
import Chat from './components/Chat';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

const MOCK_BOOKS = [
  {
    id: 1,
    title: 'Мастер и Маргарита',
    author: 'Михаил Булгаков',
    genre: 'Роман',
    description: 'Классика русской литературы о добре и зле',
    rating: 5,
    favorite_quotes: 'Рукописи не горят',
    start_date: '2024-01-15',
    end_date: '2024-02-01',
    status: 'READ'
  },
  {
    id: 2,
    title: '1984',
    author: 'Джордж Оруэлл',
    genre: 'Антиутопия',
    description: 'Роман о тоталитарном обществе',
    rating: 4,
    favorite_quotes: 'Большой брат следит за тобой',
    start_date: '2024-02-10',
    end_date: null,
    status: 'READING'
  },
  {
    id: 3,
    title: 'Преступление и наказание',
    author: 'Фёдор Достоевский',
    genre: 'Психологический роман',
    description: 'История студента Раскольникова',
    rating: null,
    favorite_quotes: null,
    start_date: null,
    end_date: null,
    status: 'PLANNED'
  }
];

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

function App() {
  const [books, setBooks] = useState([]);
  const [selectedBook, setSelectedBook] = useState(null);
  const [isFormVisible, setIsFormVisible] = useState(false);
  const [editingBook, setEditingBook] = useState(null);
  const [useMockData, setUseMockData] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
    setBooks([]);
  }, []);

  const fetchBooks = useCallback(async (token = null) => {
    const authToken = token || localStorage.getItem('token');
    
    if (!authToken && !useMockData) {
      console.warn('Токен не найден, используем моковые данные');
      setBooks(MOCK_BOOKS);
      setUseMockData(true);
      return;
    }

    try {
      const response = await authFetch(`${API_BASE_URL}/books/`);
      
      if (response.ok) {
        const data = await response.json();
        setBooks(data);
        setUseMockData(false);
      } else {
        console.warn('Бэкенд недоступен, используем моковые данные');
        setBooks(MOCK_BOOKS);
        setUseMockData(true);
      }
    } catch (error) {
      console.warn('Ошибка при загрузке книг, используем моковые данные:', error);
      setBooks(MOCK_BOOKS);
      setUseMockData(true);
    }
  }, [useMockData]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userData));
      fetchBooks(token);
    }
  }, [fetchBooks]);

  const handleCreateBook = async (bookData) => {
    if (useMockData) {
      const newBook = {
        id: Date.now(), 
        ...bookData,
        rating: bookData.rating ? parseInt(bookData.rating) : null
      };
      setBooks(prevBooks => [...prevBooks, newBook]);
      setIsFormVisible(false);
      return;
    }

    try {
      const formData = new FormData();
      Object.keys(bookData).forEach(key => {
        if (bookData[key] !== null && bookData[key] !== undefined) {
          formData.append(key, bookData[key]);
        }
      });

      const response = await authFetch(`${API_BASE_URL}/books/`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const newBook = await response.json();
        setBooks(prevBooks => [...prevBooks, newBook]);
        setIsFormVisible(false);
      } else {
        console.error('Ошибка при создании книги:', response.status);
      }
    } catch (error) {
      console.error('Ошибка при создании книги:', error);
    }
  };

  const handleUpdateBook = async (bookId, bookData) => {
    if (useMockData) {
      setBooks(prevBooks =>
        prevBooks.map(book => 
          book.id === bookId 
            ? { ...book, ...bookData, rating: bookData.rating ? parseInt(bookData.rating) : book.rating }
            : book
        )
      );
      setEditingBook(null);
      if (selectedBook && selectedBook.id === bookId) {
        setSelectedBook({ ...selectedBook, ...bookData });
      }
      return;
    }

    try {
      const response = await authFetch(`${API_BASE_URL}/books/${bookId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookData),
      });

      if (response.ok) {
        const updatedBook = await response.json();
        setBooks(prevBooks =>
          prevBooks.map(book => (book.id === bookId ? updatedBook : book))
        );
        setEditingBook(null);
        setSelectedBook(updatedBook);
      } else {
        console.error('Ошибка при обновлении книги:', response.status);
      }
    } catch (error) {
      console.error('Ошибка при обновлении книги:', error);
    }
  };

  const handleDeleteBook = async (bookId) => {
    if (useMockData) {
      setBooks(prevBooks => prevBooks.filter(book => book.id !== bookId));
      if (selectedBook && selectedBook.id === bookId) {
        setSelectedBook(null);
      }
      return;
    }

    try {
      const response = await authFetch(`${API_BASE_URL}/books/${bookId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setBooks(prevBooks => prevBooks.filter(book => book.id !== bookId));
        if (selectedBook && selectedBook.id === bookId) {
          setSelectedBook(null);
        }
      } else {
        console.error('Ошибка при удалении книги:', response.status);
      }
    } catch (error) {
      console.error('Ошибка при удалении книги:', error);
    }
  };

  const handleEditBook = (book) => {
    setEditingBook(book);
    setIsFormVisible(true);
    setSelectedBook(null);
  };

  const handleViewBook = (book) => {
    setSelectedBook(book);
    setIsFormVisible(false);
    setEditingBook(null);
  };

  const handleCancelEdit = () => {
    setEditingBook(null);
    setIsFormVisible(false);
  };

  const handleShowForm = () => {
    setIsFormVisible(true);
    setSelectedBook(null);
    setEditingBook(null);
  };

  const handleRetryConnection = () => {
    fetchBooks();
  };

  const handleLogin = async (loginData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setIsAuthenticated(true);
        setUser(data.user);
        fetchBooks(data.access_token);
      } else {
        alert('Ошибка авторизации: неверный email или пароль');
      }
    } catch (error) {
      console.error('Ошибка при авторизации:', error);
      alert('Ошибка подключения к серверу');
    }
  };

  const handleRegister = async (registerData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setIsAuthenticated(true);
        setUser(data.user);
        fetchBooks(data.access_token);
      } else {
        const errorData = await response.json();
        alert(`Ошибка регистрации: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Ошибка при регистрации:', error);
      alert('Ошибка подключения к серверу');
    }
  };

  if (!isAuthenticated) {
    return (
      <Router>
        <div className="app">
          <header className="app-header">
            <h1>Личная библиотека</h1>
          </header>
          <div className="app-content">
            <Routes>
              <Route path="/login" element={
                <AuthForm onLogin={handleLogin} isLogin={true} />
              } />
              <Route path="/register" element={
                <AuthForm onRegister={handleRegister} isLogin={false} />
              } />
              <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
          </div>
        </div>
      </Router>
    );
  }

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Личная библиотека</h1>
          <div className="header-actions">
            {useMockData && (
              <div className="mock-warning">
                <span>Используются демо-данные</span>
                <button 
                  className="btn btn-retry"
                  onClick={handleRetryConnection}
                >
                  Подключиться к серверу
                </button>
              </div>
            )}
            <nav className="nav-menu">
              <Link to="/books" className="nav-link">📚 Книги</Link>
              <Link to="/chat" className="nav-link">💬 Чат</Link>
            </nav>
            <div className="user-info">
              <span>👤 {user?.email}</span>
              <button className="btn btn-secondary" onClick={handleLogout}>
                Выйти
              </button>
            </div>
          </div>
        </header>

        <div className="app-content">
          <div className="main-section">
            <Routes>
              <Route path="/books" element={
                <>
                  {isFormVisible ? (
                    <BookForm
                      book={editingBook}
                      onSubmit={editingBook ? 
                        (data) => handleUpdateBook(editingBook.id, data) : 
                        handleCreateBook
                      }
                      onCancel={handleCancelEdit}
                    />
                  ) : selectedBook ? (
                    <BookView
                      book={selectedBook}
                      onEdit={() => handleEditBook(selectedBook)}
                      onClose={() => setSelectedBook(null)}
                    />
                  ) : (
                    <>
                      <div className="page-header">
                        <h2>Мои книги</h2>
                        <button 
                          className="btn btn-primary"
                          onClick={handleShowForm}
                        >
                          Добавить книгу
                        </button>
                      </div>
                      <BookList
                        books={books}
                        onViewBook={handleViewBook}
                        onEditBook={handleEditBook}
                        onDeleteBook={handleDeleteBook}
                      />
                    </>
                  )}
                </>
              } />
              <Route path="/chat" element={<Chat />} />
              <Route path="*" element={<Navigate to="/books" />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;