from pydantic import BaseModel
from typing import Optional


class TranscribeResponse(BaseModel):
    text: str
    duration_sec: Optional[float] = None
