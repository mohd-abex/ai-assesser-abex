"""
Interview Service Module.

This module handles the interview conversation flow, generating appropriate prompts
based on the current state and providing score hints based on candidate responses.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import logging

from ..models.llm import InterviewState, TurnResponse

logger = logging.getLogger(__name__)

# Constants for interview configuration
MAX_PROMPTS = 4
MIN_WORD_COUNT_FOR_SCORE = 5
SCORE_BASE = 2.0
SCORE_MULTIPLIER = 0.1
MAX_SCORE = 10.0

# Interview prompts in order of progression
PROMPTS = [
    "Briefly introduce yourself.",
    "Describe a challenging problem you solved recently.",
    "How do you prioritize tasks when everything is important?",
    "Tell me about a time you received constructive feedback and what you did with it.",
]


def _calculate_score_hint(transcript: Optional[str]) -> Optional[float]:
    """
    Calculate a score hint based on the candidate's response transcript.
    
    This is a simple heuristic that gives higher scores for longer, more detailed
    responses. In production, this should be replaced with actual AI-based scoring.
    
    Args:
        transcript: The candidate's response text
        
    Returns:
        A score between SCORE_BASE and MAX_SCORE, or None if no transcript
        
    Examples:
        >>> _calculate_score_hint(None)
        None
        >>> _calculate_score_hint("Yes")  # 1 word
        2.1
        >>> _calculate_score_hint("This is a much longer and detailed response")  # 8 words
        2.8
    """
    if not transcript:
        return None
    
    words = transcript.split()
    word_count = len(words)
    
    if word_count < MIN_WORD_COUNT_FOR_SCORE:
        logger.warning(
            f"Response is very short ({word_count} words). "
            f"Candidate may need prompting for more detail."
        )
    
    # Calculate score: base + (word_count * multiplier), capped at MAX_SCORE
    score = min(MAX_SCORE, SCORE_BASE + word_count * SCORE_MULTIPLIER)
    logger.debug(f"Calculated score hint: {score} for {word_count} words")
    
    return score


def _get_current_index(state: Optional[InterviewState]) -> int:
    """
    Extract the current question index from interview state.
    
    Args:
        state: Current interview state or None for new interview
        
    Returns:
        Current index as integer, defaulting to 0 for new interviews
    """
    if state is None:
        return 0
    
    data = dict(state.data)
    idx = int(data.get("idx", 0))
    logger.debug(f"Current interview index: {idx}")
    return idx


def next_turn(
    state: InterviewState | None, 
    transcript: str | None
) -> TurnResponse:
    """
    Process the next turn of the interview conversation.
    
    This function manages the interview flow by:
    1. Determining the current position in the interview
    2. Calculating a score hint based on the candidate's previous response
    3. Returning the next prompt and updated state
    
    Args:
        state: Current interview state (None for first turn)
        transcript: Candidate's response to the previous prompt (None for first turn)
        
    Returns:
        TurnResponse containing:
            - next_prompt: The next question to ask
            - score_hint: Estimated quality score for the response
            - state: Updated interview state
            
    Note:
        BUG #2: There is an off-by-one error in the prompt indexing logic.
        When idx reaches len(PROMPTS), the code tries to access PROMPTS[idx]
        which will raise an IndexError. The bounds check uses `min()` incorrectly
        for the next_idx but then uses the old idx to access the array.
        
    Examples:
        >>> # First turn
        >>> response = next_turn(None, None)
        >>> response.next_prompt
        'Briefly introduce yourself.'
        
        >>> # Subsequent turn
        >>> state = InterviewState(data={"idx": 1})
        >>> response = next_turn(state, "I'm a software engineer...")
        >>> response.score_hint  # Will be a float based on response length
    """
    logger.info("Processing next interview turn")
    
    # Get current state
    idx = _get_current_index(state)
    logger.info(f"Current prompt index: {idx}")
    
    # Calculate score for the previous response
    score_hint = _calculate_score_hint(transcript)
    if score_hint:
        logger.info(f"Score hint for response: {score_hint:.2f}")
    
    # BUG: This creates next_idx but then uses idx to access PROMPTS
    # When idx == len(PROMPTS), this will cause IndexError
    # Should be using: current_idx = min(idx, len(PROMPTS) - 1)
    # and then: next_idx = min(idx + 1, len(PROMPTS) - 1)
    next_idx = min(idx + 1, len(PROMPTS))
    
    # Prepare next state
    data: Dict[str, Any] = {} if state is None else dict(state.data)
    data["idx"] = next_idx
    
    logger.info(f"Moving to next index: {next_idx}")
    
    # BUG: Using idx here which can equal len(PROMPTS), causing IndexError
    # Should use: prompt = PROMPTS[min(idx, len(PROMPTS) - 1)]
    next_prompt = PROMPTS[idx]
    logger.debug(f"Next prompt: {next_prompt}")
    
    return TurnResponse(
        next_prompt=next_prompt,
        score_hint=score_hint,
        state=InterviewState(data=data)
    )
