from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class InterviewState(BaseModel):
    # Free-form state for MVP
    data: Dict[str, Any] = {}


class TurnRequest(BaseModel):
    state: InterviewState | None = None
    transcript: Optional[str] = None


class TurnResponse(BaseModel):
    next_prompt: str
    score_hint: float | None = None
    state: InterviewState | None = None


class GenerateQuestionsRequest(BaseModel):
    job_description: str
    count: int = 5


class GenerateQuestionsResponse(BaseModel):
    questions: List[str]
