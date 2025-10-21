from fastapi import APIRouter, File, UploadFile
from ..models.stt import TranscribeResponse

router = APIRouter()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)):
    # Read but ignore content in stub
    await audio.read()
    return TranscribeResponse(text="[stub] Transcription would go here.")
