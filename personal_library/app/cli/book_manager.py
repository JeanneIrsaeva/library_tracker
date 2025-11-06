import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from typing import Optional, List
from datetime import date
import questionary
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import SessionLocal
from app.models.book import Book, BookStatus
from app.models.user import User
from app.repositories.book_repository import BookRepository
from app.schemas.book import BookCreate, BookUpdate

app = typer.Typer(help="Управление личной библиотекой книг")
console = Console()

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_session(db):
    users = db.query(User).all()
    if not users:
        console.print("[red]В системе нет пользователей![/red]")
        console.print("Сначала создайте пользователя через API регистрации.")
        return None
    
    user_choices = [
        questionary.Choice(f"{user.email} (ID: {user.id})", value=user.id)
        for user in users
    ]
    
    user_id = questionary.select(
        "Выберите пользователя:",
        choices=user_choices
    ).ask()
    
    return user_id

def display_books_table(books: List[Book], title: str = "Список книг"):
    """Отображение книг в виде таблицы"""
    if not books:
        console.print("[yellow]Книги не найдены[/yellow]")
        return
        
    table = Table(title=title)
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Название", style="green", width=25)
    table.add_column("Автор", style="blue", width=20)
    table.add_column("Жанр", style="magenta", width=15)
    table.add_column("Статус", style="yellow", width=12)
    table.add_column("Рейтинг", style="red", width=8)
    table.add_column("Пользователь", style="white", width=20)
    
    for book in books:
        rating_str = str(book.rating) if book.rating else "Нет"
        user_email = book.user.email if book.user else "Неизвестно"
        
        status_style = {
            "PLANNED": "yellow",
            "READING": "blue", 
            "READ": "green"
        }.get(book.status.value, "white")
        
        table.add_row(
            str(book.id),
            book.title,
            book.author,
            book.genre,
            f"[{status_style}]{book.status.value}[/{status_style}]",
            rating_str,
            user_email
        )
    
    console.print(table)

def get_book_status_choice(current_status: str = "PLANNED") -> str:
    status_choices = [
        questionary.Choice("📋 Запланирована", value="PLANNED"),
        questionary.Choice("📖 Читаю", value="READING"),
        questionary.Choice("✅ Прочитана", value="READ")
    ]
    
    default_index = 0
    if current_status == "READING":
        default_index = 1
    elif current_status == "READ":
        default_index = 2
    
    return questionary.select(
        "Статус чтения:",
        choices=status_choices,
        default=status_choices[default_index]
    ).ask()

def get_rating_choice(current_rating: Optional[int] = None) -> Optional[int]:
    rating_choices = [
        questionary.Choice("Не оценена", value=None),
        questionary.Choice("⭐ 1", value=1),
        questionary.Choice("⭐⭐ 2", value=2),
        questionary.Choice("⭐⭐⭐ 3", value=3),
        questionary.Choice("⭐⭐⭐⭐ 4", value=4),
        questionary.Choice("⭐⭐⭐⭐⭐ 5", value=5)
    ]
    
    default_index = 0
    if current_rating:
        for i, choice in enumerate(rating_choices):
            if choice.value == current_rating:
                default_index = i
                break
    
    return questionary.select(
        "Рейтинг:",
        choices=rating_choices,
        default=rating_choices[default_index]
    ).ask()

def get_date_input(prompt: str, current_date: Optional[date] = None) -> Optional[date]:
    default_value = current_date.isoformat() if current_date else ""
    
    while True:
        date_str = Prompt.ask(
            prompt, 
            default=default_value,
            show_default=True
        )
        
        if not date_str:
            return None
            
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            console.print("[red]Неверный формат даты. Используйте ГГГГ-ММ-ДД[/red]")

@app.command()
def manage():
    db = next(get_session())
    
    user_id = get_user_session(db)
    if not user_id:
        return
        
    repository = BookRepository(db)
    
    while True:
        action = questionary.select(
            "Выберите действие:",
            choices=[
                "📚 Просмотреть все книги",
                "🔍 Найти книгу по ID", 
                "➕ Создать новую книгу",
                "✏️ Редактировать книгу",
                "🗑️ Удалить книгу",
                "👤 Показать книги пользователя",
                "❌ Выход"
            ]
        ).ask()

        if action == "📚 Просмотреть все книги":
            books = repository.get_all()
            display_books_table(books, "Все книги в библиотеке")

        elif action == "👤 Показать книги пользователя":
            user_books = repository.get_by_user_id(user_id)
            user = db.query(User).filter(User.id == user_id).first()
            display_books_table(user_books, f"Книги пользователя {user.email}")

        elif action == "🔍 Найти книгу по ID":
            try:
                book_id = IntPrompt.ask("Введите ID книги")
                book = repository.get_by_id(book_id)
                if book:
                    display_books_table([book], "Найденная книга")
                else:
                    console.print("[red]Книга не найдена[/red]")
            except ValueError:
                console.print("[red]ID должен быть числом[/red]")

        elif action == "➕ Создать новую книгу":
            console.print(Panel("Создание новой книги", style="bold blue"))
            
            title = Prompt.ask("Название книги")
            author = Prompt.ask("Автор")
            genre = Prompt.ask("Жанр")
            
            description = Prompt.ask("Описание", default="")
            favorite_quotes = Prompt.ask("Любимые цитаты", default="")
            
            status = get_book_status_choice()
            
            rating = get_rating_choice()
            
            start_date = get_date_input("Дата начала чтения (ГГГГ-ММ-ДД)")
            end_date = get_date_input("Дата окончания (ГГГГ-ММ-ДД)")
            
            if start_date and end_date and end_date < start_date:
                console.print("[red]Дата окончания не может быть раньше даты начала![/red]")
                if not Confirm.ask("Продолжить без изменений?"):
                    continue
            
            book_data = BookCreate(
                title=title,
                author=author,
                genre=genre,
                description=description or None,
                rating=rating,
                favorite_quotes=favorite_quotes or None,
                start_date=start_date,
                end_date=end_date,
                status=status
            )
            
            try:
                new_book = repository.create(book_data, user_id)
                console.print(f"[green]✅ Книга '{new_book.title}' успешно создана с ID {new_book.id}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Ошибка при создании книги: {e}[/red]")

        elif action == "✏️ Редактировать книгу":
            try:
                book_id = IntPrompt.ask("Введите ID книги для редактирования")
                book = repository.get_by_id(book_id)
                if not book:
                    console.print("[red]Книга не найдена[/red]")
                    continue
                    
                if book.user_id != user_id:
                    console.print("[red]Эта книга принадлежит другому пользователю![/red]")
                    continue
                    
                console.print(Panel(f"Редактирование книги: {book.title}", style="bold blue"))
                
                update_data = {}
                
                fields_to_edit = questionary.checkbox(
                    "Выберите поля для редактирования:",
                    choices=[
                        questionary.Choice("Название", value="title", checked=False),
                        questionary.Choice("Автор", value="author", checked=False),
                        questionary.Choice("Жанр", value="genre", checked=False),
                        questionary.Choice("Статус", value="status", checked=False),
                        questionary.Choice("Рейтинг", value="rating", checked=False),
                        questionary.Choice("Описание", value="description", checked=False),
                        questionary.Choice("Любимые цитаты", value="favorite_quotes", checked=False),
                        questionary.Choice("Дата начала", value="start_date", checked=False),
                        questionary.Choice("Дата окончания", value="end_date", checked=False)
                    ]
                ).ask()
                
                if not fields_to_edit:
                    console.print("[yellow]Редактирование отменено[/yellow]")
                    continue
                
                if "title" in fields_to_edit:
                    update_data["title"] = Prompt.ask("Новое название", default=book.title)
                    
                if "author" in fields_to_edit:
                    update_data["author"] = Prompt.ask("Новый автор", default=book.author)
                    
                if "genre" in fields_to_edit:
                    update_data["genre"] = Prompt.ask("Новый жанр", default=book.genre)
                    
                if "status" in fields_to_edit:
                    update_data["status"] = get_book_status_choice(book.status.value)
                    
                if "rating" in fields_to_edit:
                    update_data["rating"] = get_rating_choice(book.rating)
                    
                if "description" in fields_to_edit:
                    update_data["description"] = Prompt.ask("Новое описание", default=book.description or "")
                    
                if "favorite_quotes" in fields_to_edit:
                    update_data["favorite_quotes"] = Prompt.ask("Новые цитаты", default=book.favorite_quotes or "")
                    
                if "start_date" in fields_to_edit:
                    update_data["start_date"] = get_date_input("Новая дата начала", book.start_date)
                    
                if "end_date" in fields_to_edit:
                    update_data["end_date"] = get_date_input("Новая дата окончания", book.end_date)
                
                start_date = update_data.get("start_date", book.start_date)
                end_date = update_data.get("end_date", book.end_date)
                if start_date and end_date and end_date < start_date:
                    console.print("[red]Дата окончания не может быть раньше даты начала![/red]")
                    if not Confirm.ask("Продолжить без изменений дат?"):
                        continue
                
                book_update = BookUpdate(**update_data)
                updated_book = repository.update(book_id, book_update, user_id)
                
                if updated_book:
                    console.print(f"[green]✅ Книга '{updated_book.title}' успешно обновлена[/green]")
                else:
                    console.print("[red]❌ Ошибка при обновлении книги[/red]")
                    
            except ValueError:
                console.print("[red]ID должен быть числом[/red]")
            except Exception as e:
                console.print(f"[red]❌ Ошибка при редактировании: {e}[/red]")

        elif action == "🗑️ Удалить книгу":
            try:
                book_id = IntPrompt.ask("Введите ID книги для удаления")
                book = repository.get_by_id(book_id)
                if not book:
                    console.print("[red]Книга не найдена[/red]")
                    continue
                    
                if book.user_id != user_id:
                    console.print("[red]Эта книга принадлежит другому пользователю![/red]")
                    continue
                    
                confirm = Confirm.ask(
                    f"Вы уверены, что хотите удалить книгу '[red]{book.title}[/red]'?"
                )
                if confirm:
                    success = repository.delete(book_id, user_id)
                    if success:
                        console.print(f"[green]✅ Книга '{book.title}' успешно удалена[/green]")
                    else:
                        console.print("[red]❌ Ошибка при удалении книги[/red]")
                else:
                    console.print("[yellow]Удаление отменено[/yellow]")
                    
            except ValueError:
                console.print("[red]ID должен быть числом[/red]")

        elif action == "❌ Выход":
            console.print("[blue]👋 До свидания![/blue]")
            break

@app.command()
def list_all():
    db = next(get_session())
    repository = BookRepository(db)
    books = repository.get_all()
    display_books_table(books, "Все книги в библиотеке")

@app.command()
def list_user_books(user_id: int):
    db = next(get_session())
    repository = BookRepository(db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        console.print(f"[red]Пользователь с ID {user_id} не найден[/red]")
        return
        
    books = repository.get_by_user_id(user_id)
    display_books_table(books, f"Книги пользователя {user.email}")

@app.command()
def create(
    title: str = typer.Option(..., prompt=True),
    author: str = typer.Option(..., prompt=True),
    genre: str = typer.Option(..., prompt=True),
    user_id: int = typer.Option(..., prompt="User ID"),
    description: str = typer.Option(""),
    status: BookStatus = typer.Option(BookStatus.PLANNED, prompt=True),
    rating: Optional[int] = typer.Option(None, min=1, max=5)
):
    db = next(get_session())
    repository = BookRepository(db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        console.print(f"[red]Пользователь с ID {user_id} не найден[/red]")
        return
    
    book_data = BookCreate(
        title=title,
        author=author,
        genre=genre,
        description=description or None,
        rating=rating,
        status=status
    )
    
    try:
        new_book = repository.create(book_data, user_id)
        console.print(f"[green]✅ Книга '{new_book.title}' успешно создана с ID {new_book.id}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Ошибка при создании книги: {e}[/red]")

@app.command()
def delete(book_id: int, user_id: int = typer.Option(..., prompt="User ID")):
    db = next(get_session())
    repository = BookRepository(db)
    
    book = repository.get_by_id(book_id)
    if not book:
        console.print(f"[red]Книга с ID {book_id} не найдена[/red]")
        return
        
    if book.user_id != user_id:
        console.print("[red]Эта книга принадлежит другому пользователю![/red]")
        return
    
    success = repository.delete(book_id, user_id)
    if success:
        console.print(f"[green]✅ Книга с ID {book_id} успешно удалена[/green]")
    else:
        console.print(f"[red]❌ Ошибка при удалении книги с ID {book_id}[/red]")

if __name__ == "__main__":
    app()
