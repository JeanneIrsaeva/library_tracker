from fastapi import Request, HTTPException, status
from app.utils.jwt import verify_token
from typing import Optional

async def get_current_user(request: Request) -> Optional[dict]:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(" ")[1] 
        user_data = verify_token(token)
        return user_data
    except:
        return None