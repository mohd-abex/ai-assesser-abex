from typing import Optional
from pydantic import BaseModel


class Health(BaseModel):
    status: str = "ok"
    env: Optional[str] = None


class Message(BaseModel):
    message: str
