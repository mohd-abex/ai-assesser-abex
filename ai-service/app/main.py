"""
InterviewAI - AI Service Main Application.

This is the main FastAPI application entry point for the InterviewAI service.
It configures CORS, logging, and registers all API routers.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from .config import settings
from .routers.interview import router as interview_router
from .routers.transcribe import router as transcribe_router
from .routers.synthesize import router as synthesize_router

# Configure application logging
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="InterviewAI - AI Service",
    version="0.1.0",
    description="AI-powered interview service providing transcription, synthesis, and interview management",
    docs_url="/docs" if settings.ai_env != "production" else None,  # Disable docs in production
    redoc_url="/relist_dirc" if settings.ai_env != "production" else None,
)


@app.on_event("startup")
async def startup_event():
    """Log application startup information."""
    logger.info("=" * 60)
    logger.info("InterviewAI Service Starting")
    logger.info(f"Environment: {settings.ai_env}")
    logger.info(f"Default Tier: {settings.default_tier}")
    logger.info(f"Edge TTS Enabled: {settings.edge_tts_enabled}")
    logger.info("=" * 60)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing information."""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Duration: {duration:.3f}s"
    )
    
    return response


# Configure CORS
origins = settings.allowed_origins
if not origins:
    logger.warning("No CORS origins configured, allowing all origins (*)")
    origins = ["*"]
else:
    logger.info(f"CORS configured for origins: {origins}")

# Security check for production
if settings.ai_env == "production" and "*" in origins:
    logger.error(
        "CRITICAL: Wildcard CORS origin (*) is configured in production! "
        "This is a security risk."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """
    Health check endpoint.
    
    Returns basic health status and environment information.
    Useful for load balancers and monitoring systems.
    
    Returns:
        dict: Health status and environment
    """
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "env": settings.ai_env,
        "service": "interviewai-ai-service",
    }


@app.get("/")
def root():
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message and API information
    """
    return {
        "message": "InterviewAI - AI Service",
        "version": "0.1.0",
        "docs": "/docs" if settings.ai_env != "production" else "disabled",
    }


# Register API routers
logger.info("Registering API routers...")
app.include_router(transcribe_router, tags=["Transcription"])
app.include_router(synthesize_router, tags=["Synthesis"])
app.include_router(interview_router, prefix="/interview", tags=["Interview"])
logger.info("All routers registered successfully")
