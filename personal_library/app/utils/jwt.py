from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

SECRET_KEY = "your-secret-key-here"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def refresh_tokens(refresh_token: str) -> Optional[Dict[str, str]]:
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    
    user_data = {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role")
    }
    
    new_access_token = create_access_token(user_data)
    new_refresh_token = create_refresh_token(user_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }