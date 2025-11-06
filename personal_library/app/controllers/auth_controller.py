from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.utils.jwt import create_access_token
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли пользователь
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создаем пользователя
    hashed_password = User.get_password_hash(user_data.password)
    db_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Создаем токен
    access_token = create_access_token(
        data={"user_id": db_user.id, "email": db_user.email, "role": db_user.role}
    )
    
    return Token(
    access_token=access_token,
    token_type="bearer",
    user=UserResponse.model_validate(db_user)
    )

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not User.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role}
    )
    
    return Token(
    access_token=access_token,
    token_type="bearer",
    user=UserResponse.model_validate(user)
    )