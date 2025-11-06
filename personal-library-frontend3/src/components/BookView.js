import React from 'react';
import './BookView.css';

const BookView = ({ book, onEdit, onClose }) => {
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

  const formatDate = (dateString) => {
    if (!dateString) return 'Не указана';
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  return (
    <div className="book-view">
      <div className="book-view-header">
        <h2>{book.title}</h2>
        <button className="btn btn-close" onClick={onClose}>×</button>
      </div>

      <div className="book-view-content">
        <div className="book-basic-info">
          <div className="info-row">
            <strong>Автор:</strong>
            <span>{book.author}</span>
          </div>
          <div className="info-row">
            <strong>Жанр:</strong>
            <span>{book.genre}</span>
          </div>
          <div className="info-row">
            <strong>Статус:</strong>
            <span className={`status-badge ${getStatusClass(book.status)}`}>
              {getStatusText(book.status)}
            </span>
          </div>
          {book.rating && (
            <div className="info-row">
              <strong>Рейтинг:</strong>
              <span className="rating">{'⭐'.repeat(book.rating)}</span>
            </div>
          )}
        </div>

        <div className="book-dates">
          <div className="info-row">
            <strong>Дата начала:</strong>
            <span>{formatDate(book.start_date)}</span>
          </div>
          <div className="info-row">
            <strong>Дата окончания:</strong>
            <span>{formatDate(book.end_date)}</span>
          </div>
        </div>

        {book.description && (
          <div className="book-section">
            <h3>Описание</h3>
            <p>{book.description}</p>
          </div>
        )}

        {book.favorite_quotes && (
          <div className="book-section">
            <h3>Любимые цитаты</h3>
            <p className="quotes">{book.favorite_quotes}</p>
          </div>
        )}
      </div>

      <div className="book-view-actions">
        <button className="btn btn-primary" onClick={onEdit}>
          Редактировать
        </button>
        <button className="btn btn-secondary" onClick={onClose}>
          Закрыть
        </button>
      </div>
    </div>
  );
};

export default BookView;