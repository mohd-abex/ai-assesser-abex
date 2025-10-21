from fastapi import APIRouter
from ..models.tts import SynthesizeRequest, SynthesizeResponse

router = APIRouter()


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(req: SynthesizeRequest):
    return SynthesizeResponse(message="[stub] TTS synthesis would return audio.", audio_url=None)
