from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from passlib.context import CryptContext
from app.database import Base

# Используем более современный алгоритм хеширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password):
        # Ограничиваем длину пароля для bcrypt
        if len(password) > 72:
            password = password[:72]
        return pwd_context.hash(password)
