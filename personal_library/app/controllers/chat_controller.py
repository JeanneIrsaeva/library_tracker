from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.chat import ChatMessage
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse
from app.dependencies import get_current_user  # Используем новую зависимость
from typing import List

router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("/messages", response_model=List[ChatMessageResponse])
def get_chat_messages(
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user),  # Используем зависимость вместо token параметра
    skip: int = 0,
    limit: int = 50
):
    # Админы видят все сообщения, пользователи - только свои
    if user_data.get('role') == 'admin':
        messages = db.query(ChatMessage).offset(skip).limit(limit).all()
    else:
        messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_data.get('user_id')
        ).offset(skip).limit(limit).all()
    
    return messages

@router.post("/messages", response_model=ChatMessageResponse)
def create_chat_message(
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)  # Используем зависимость вместо token параметра
):
    db_message = ChatMessage(
        user_id=user_data.get('user_id'),
        message=message_data.message,
        is_admin=1 if user_data.get('role') == 'admin' else 0
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message