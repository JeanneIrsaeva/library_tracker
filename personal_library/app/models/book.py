from sqlalchemy import Column, Integer, String, Text, Enum, Date, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class BookStatus(enum.Enum):
    READING = "READING"
    PLANNED = "PLANNED"
    READ = "READ"

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    genre = Column(String(50), nullable=False)
    description = Column(Text)
    rating = Column(Integer)
    favorite_quotes = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Enum(BookStatus), default=BookStatus.PLANNED)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User")