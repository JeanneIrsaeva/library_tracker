from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatMessageCreate(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_admin: int
    created_at: datetime
    email: Optional[str] = None
    
    class Config:
        from_attributes = True