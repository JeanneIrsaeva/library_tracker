import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './AuthForm.css';

const AuthForm = ({ onLogin, onRegister, isLogin = true }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    password_confirm: ''
  });
  
  const navigate = useNavigate();
  const location = useLocation();

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLogin) {
      onLogin(formData);
    } else {
      onRegister(formData);
    }
  };

  const switchAuthMode = () => {
    if (isLogin) {
      navigate('/register');
    } else {
      navigate('/login');
    }
  };

  const getAuthIcon = () => {
    return isLogin ? '🔐' : '👤';
  };

  const getAuthTitle = () => {
    return isLogin ? 'Вход в библиотеку' : 'Регистрация';
  };

  const getAuthDescription = () => {
    return isLogin 
      ? 'Войдите в свою учетную запись для доступа к библиотеке'
      : 'Создайте новую учетную запись для начала работы';
  };

  const getSwitchText = () => {
    return isLogin 
      ? 'Еще нет аккаунта?' 
      : 'Уже есть аккаунт?';
  };

  const getSwitchButtonText = () => {
    return isLogin ? 'Зарегистрироваться' : 'Войти';
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <div className="auth-header">
          <span className="auth-icon">{getAuthIcon()}</span>
          <h2>{getAuthTitle()}</h2>
          <p>{getAuthDescription()}</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="your@email.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Пароль</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Введите ваш пароль"
              required
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="password_confirm">Подтверждение пароля</label>
              <input
                type="password"
                id="password_confirm"
                name="password_confirm"
                value={formData.password_confirm}
                onChange={handleChange}
                placeholder="Повторите ваш пароль"
                required
              />
            </div>
          )}

          <button type="submit" className="auth-submit-btn">
            {isLogin ? 'Войти в библиотеку' : 'Создать аккаунт'}
          </button>
        </form>

        <div className="auth-switch">
          <p>{getSwitchText()}</p>
          <button 
            type="button" 
            className="auth-switch-btn"
            onClick={switchAuthMode}
          >
            {getSwitchButtonText()}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthForm;