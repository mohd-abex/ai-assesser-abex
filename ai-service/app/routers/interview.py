from fastapi import APIRouter
from ..models.llm import (
    TurnRequest,
    TurnResponse,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
)
from ..services.interview_service import next_turn
from ..services.question_generator import generate_questions

router = APIRouter()


@router.post("/turn", response_model=TurnResponse)
async def interview_turn(req: TurnRequest):
    return next_turn(req.state, req.transcript)


@router.post("/questions/generate", response_model=GenerateQuestionsResponse)
async def questions_generate(req: GenerateQuestionsRequest):
    questions = generate_questions(req.job_description, req.count)
    return GenerateQuestionsResponse(questions=questions)
