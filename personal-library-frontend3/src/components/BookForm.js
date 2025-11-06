import React, { useState, useEffect } from 'react';
import './BookForm.css';

const BookForm = ({ book, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    genre: '',
    description: '',
    rating: '',
    favorite_quotes: '',
    start_date: '',
    end_date: '',
    status: 'PLANNED'
  });

  useEffect(() => {
    if (book) {
      setFormData({
        title: book.title || '',
        author: book.author || '',
        genre: book.genre || '',
        description: book.description || '',
        rating: book.rating || '',
        favorite_quotes: book.favorite_quotes || '',
        start_date: book.start_date || '',
        end_date: book.end_date || '',
        status: book.status || 'PLANNED'
      });
    }
  }, [book]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const submitData = {
      ...formData,
      rating: formData.rating ? parseInt(formData.rating) : null,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
      book_status: formData.status  // Используем переименованное поле для бэкенда
    };

    onSubmit(submitData);
  };

  return (
    <div className="book-form">
      <h2>{book ? 'Редактировать книгу' : 'Добавить новую книгу'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="title">Название *</label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="author">Автор *</label>
          <input
            type="text"
            id="author"
            name="author"
            value={formData.author}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="genre">Жанр *</label>
          <input
            type="text"
            id="genre"
            name="genre"
            value={formData.genre}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="status">Статус</label>
          <select
            id="status"
            name="status"
            value={formData.status}
            onChange={handleChange}
          >
            <option value="PLANNED">Запланирована</option>
            <option value="READING">Читаю</option>
            <option value="READ">Прочитана</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="rating">Рейтинг (1-5)</label>
          <select
            id="rating"
            name="rating"
            value={formData.rating}
            onChange={handleChange}
          >
            <option value="">Не оценена</option>
            <option value="1">1 ⭐</option>
            <option value="2">2 ⭐⭐</option>
            <option value="3">3 ⭐⭐⭐</option>
            <option value="4">4 ⭐⭐⭐⭐</option>
            <option value="5">5 ⭐⭐⭐⭐⭐</option>
          </select>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="start_date">Дата начала чтения</label>
            <input
              type="date"
              id="start_date"
              name="start_date"
              value={formData.start_date}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="end_date">Дата окончания чтения</label>
            <input
              type="date"
              id="end_date"
              name="end_date"
              value={formData.end_date}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="description">Описание</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="3"
          />
        </div>

        <div className="form-group">
          <label htmlFor="favorite_quotes">Любимые цитаты</label>
          <textarea
            id="favorite_quotes"
            name="favorite_quotes"
            value={formData.favorite_quotes}
            onChange={handleChange}
            rows="3"
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary">
            {book ? 'Обновить' : 'Добавить'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
};

export default BookForm;