import React from 'react';
import './BookList.css';

const BookList = ({ books, onViewBook, onEditBook, onDeleteBook }) => {
  const getStatusText = (status) => {
    const statusMap = {
      'PLANNED': 'Запланирована',
      'READING': 'Читаю',
      'READ': 'Прочитана'
    };
    return statusMap[status] || status;
  };

  const getStatusClass = (status) => {
    const classMap = {
      'PLANNED': 'status-planned',
      'READING': 'status-reading',
      'READ': 'status-read'
    };
    return classMap[status] || '';
  };

  if (books.length === 0) {
    return (
      <div className="book-list empty">
        <p>В библиотеке пока нет книг. Добавьте первую книгу!</p>
      </div>
    );
  }

  return (
    <div className="book-list">
      <h2>Список книг ({books.length})</h2>
      <div className="books-grid">
        {books.map(book => (
          <div key={book.id} className="book-card">
            <div className="book-header">
              <h3 className="book-title">{book.title}</h3>
              <span className={`status-badge ${getStatusClass(book.status)}`}>
                {getStatusText(book.status)}
              </span>
            </div>
            <div className="book-info">
              <p><strong>Автор:</strong> {book.author}</p>
              <p><strong>Жанр:</strong> {book.genre}</p>
              {book.rating && (
                <p><strong>Рейтинг:</strong> {'⭐'.repeat(book.rating)}</p>
              )}
            </div>
            <div className="book-actions">
              <button 
                className="btn btn-view"
                onClick={() => onViewBook(book)}
              >
                Просмотр
              </button>
              <button 
                className="btn btn-edit"
                onClick={() => onEditBook(book)}
              >
                Редактировать
              </button>
              <button 
                className="btn btn-delete"
                onClick={() => onDeleteBook(book.id)}
              >
                Удалить
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BookList;