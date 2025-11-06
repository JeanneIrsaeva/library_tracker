from fastapi import APIRouter, Depends, HTTPException, status as http_status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging

from app.database import get_db
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.services.book_service import BookService
from app.dependencies import get_current_user  # Импортируем новую зависимость

router = APIRouter(prefix="/books", tags=["books"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[BookResponse])
def get_books(
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем новую зависимость
):
    try:
        service = BookService(db)
        user_id = user_data.get('user_id')
        books = service.get_books_by_user(user_id)
        return books
    except Exception as e:
        logger.error(f"Ошибка при получении списка книг: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int, 
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем новую зависимость
):
    service = BookService(db)
    book = service.get_book_by_id(book_id)
    
    if not book:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена"
        )
    
    # Проверяем, что книга принадлежит текущему пользователю
    if book.user_id != user_data.get('user_id'):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    return book

@router.post("/", response_model=BookResponse, status_code=http_status.HTTP_201_CREATED)
def create_book(
    title: str = Form(...),
    author: str = Form(...),
    genre: str = Form(...),
    description: Optional[str] = Form(None),
    rating: Optional[int] = Form(None),
    favorite_quotes: Optional[str] = Form(None),
    start_date: Optional[date] = Form(None),
    end_date: Optional[date] = Form(None),
    book_status: str = Form("PLANNED"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем новую зависимость
):
    try:
        valid_statuses = {"READING", "PLANNED", "READ"}
        if book_status not in valid_statuses:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Недопустимый статус: '{book_status}'. Допустимые значения: {', '.join(valid_statuses)}"
            )

        if rating == "" or rating is None:
            rating_value = None
        else:
            try:
                rating_value = int(rating)
                if rating_value == 0:
                    rating_value = None
            except (ValueError, TypeError):
                rating_value = None

        book_data = BookCreate(
            title=title,
            author=author,
            genre=genre,
            description=description,
            rating=rating_value,
            favorite_quotes=favorite_quotes,
            start_date=start_date,
            end_date=end_date,
            status=book_status
        )
        
        service = BookService(db)
        return service.create_book(book_data, user_data.get('user_id'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании книги: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при создании книги"
        )

@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int, 
    book_update: BookUpdate, 
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем новую зависимость
):
    service = BookService(db)
    book = service.update_book(book_id, book_update, user_data.get('user_id'))
    
    if not book:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена или у вас нет прав для ее редактирования"
        )
    
    return book

@router.put("/{book_id}", response_model=BookResponse)
def update_book_full(
    book_id: int, 
    book_update: BookUpdate, 
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем новую зависимость
):
    service = BookService(db)
    book = service.update_book(book_id, book_update, user_data.get('user_id'))
    
    if not book:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена или у вас нет прав для ее редактирования"
        )
    
    return book

@router.delete("/{book_id}")
def delete_book(
    book_id: int, 
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем новую зависимость
):
    service = BookService(db)
    if not service.delete_book(book_id, user_data.get('user_id')):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена или у вас нет прав для ее удаления"
        )
    
    return {"message": "Книга успешно удалена"}
