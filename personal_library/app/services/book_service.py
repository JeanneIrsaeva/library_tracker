from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from sqlalchemy.orm import Session
from typing import List, Optional

class BookService:
    def __init__(self, db: Session):
        self.repository = BookRepository(db)

    def get_all_books(self) -> List[BookResponse]:
        books = self.repository.get_all()
        return [BookResponse.model_validate(book) for book in books]

    def get_books_by_user(self, user_id: int) -> List[BookResponse]:
        books = self.repository.get_by_user_id(user_id)
        return [BookResponse.model_validate(book) for book in books]

    def get_book_by_id(self, book_id: int) -> Optional[BookResponse]:
        book = self.repository.get_by_id(book_id)
        if book:
            return BookResponse.model_validate(book)
        return None

    def create_book(self, book_data: BookCreate, user_id: int) -> BookResponse:
        book = self.repository.create(book_data, user_id)
        return BookResponse.model_validate(book)

    def update_book(self, book_id: int, book_data: BookUpdate, user_id: int) -> Optional[BookResponse]:
        book = self.repository.update(book_id, book_data, user_id)
        if book:
            return BookResponse.model_validate(book)
        return None

    def delete_book(self, book_id: int, user_id: int) -> bool:
        return self.repository.delete(book_id, user_id)
