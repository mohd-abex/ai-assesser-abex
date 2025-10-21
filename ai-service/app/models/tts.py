from pydantic import BaseModel
from typing import Optional


class SynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class SynthesizeResponse(BaseModel):
    # For stub, we return a message instead of audio bytes
    message: str
    audio_url: Optional[str] = None
