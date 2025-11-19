from enum import Enum
from pydantic import BaseModel, Field, validator
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date

class BookStatus(str, Enum):
    READING = "READING"
    PLANNED = "PLANNED"
    READ = "READ"

class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    rating: Optional[int] = None
    favorite_quotes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: BookStatus = BookStatus.PLANNED

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Рейтинг должен быть от 1 до 5')
        return v

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    genre: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    favorite_quotes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: BookStatus = BookStatus.PLANNED

    @validator('end_date')
    def validate_dates(cls, end_date, values):
        start_date = values.get('start_date')
        if start_date and end_date and end_date < start_date:
            raise ValueError('Дата окончания не может быть раньше даты начала')
        return end_date

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    genre: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    favorite_quotes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[BookStatus] = None

class BookResponse(BookBase):
    id: int
    user_id: int  
    
    class Config:
        from_attributes = True