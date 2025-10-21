from __future__ import annotations
from typing import Any, Dict

from ..models.llm import InterviewState, TurnResponse


PROMPTS = [
    "Briefly introduce yourself.",
    "Describe a challenging problem you solved recently.",
    "How do you prioritize tasks when everything is important?",
    "Tell me about a time you received constructive feedback and what you did with it.",
]


def next_turn(state: InterviewState | None, transcript: str | None) -> TurnResponse:
    # Extremely simple placeholder logic:
    # - If no state, start at index 0
    # - Else, move to next prompt until end
    data: Dict[str, Any] = {} if state is None else dict(state.data)
    idx = int(data.get("idx", 0))

    # Naive score hint: longer transcript => slightly higher
    score_hint = None
    if transcript:
        length = len(transcript.split())
        score_hint = min(10.0, 2.0 + length * 0.1)

    next_idx = min(idx + 1, len(PROMPTS) - 1)
    data["idx"] = next_idx

    return TurnResponse(next_prompt=PROMPTS[idx], score_hint=score_hint, state=InterviewState(data=data))
