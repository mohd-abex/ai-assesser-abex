from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.interview import router as interview_router
from .routers.transcribe import router as transcribe_router
from .routers.synthesize import router as synthesize_router

app = FastAPI(title="InterviewAI - AI Service", version="0.1.0")

# CORS
origins = settings.allowed_origins
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ai_env}


# Routers
app.include_router(transcribe_router)
app.include_router(synthesize_router)
app.include_router(interview_router, prefix="/interview")
