from sqlalchemy.orm import Session
from app.models.book import Book
from app.schemas.book import BookCreate, BookUpdate
from typing import List, Optional

class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Book]:
        return self.db.query(Book).all()

    def get_by_user_id(self, user_id: int) -> List[Book]:
        return self.db.query(Book).filter(Book.user_id == user_id).all()

    def get_by_id(self, book_id: int) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def create(self, book: BookCreate, user_id: int) -> Book:
        db_book = Book(**book.dict(), user_id=user_id)
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    def update(self, book_id: int, book_update: BookUpdate, user_id: int) -> Optional[Book]:
        db_book = self.db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
        if db_book:
            update_data = book_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_book, field, value)
            self.db.commit()
            self.db.refresh(db_book)
        return db_book

    def delete(self, book_id: int, user_id: int) -> bool:
        db_book = self.db.query(Book).filter(Book.id == book_id, Book.user_id == user_id).first()
        if db_book:
            self.db.delete(db_book)
            self.db.commit()
            return True
        return False