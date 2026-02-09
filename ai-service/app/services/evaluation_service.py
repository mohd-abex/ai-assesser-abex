"""
Evaluation Service Module.

This module provides functionality to aggregate interview responses and generate
evaluation reports with scoring and summaries.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Configuration constants
MIN_SCORE = 0.0
MAX_SCORE = 10.0
DEFAULT_SCORE = 5.0


def _validate_response(response: Dict[str, Any]) -> bool:
    """
    Validate the structure of a single response.
    
    Args:
        response: Response dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response, dict):
        logger.warning(f"Invalid response type: {type(response)}")
        return False
    
    return True


def _extract_score_hints(responses: List[Dict[str, Any]]) -> List[float]:
    """
    Extract valid score hints from responses.
    
    Args:
        responses: List of response dictionaries
        
    Returns:
        List of valid score hints as floats
        
    Note:
        This function filters out invalid responses and extracts only
        numeric score hints within the valid range.
    """
    hints = []
    
    for idx, response in enumerate(responses):
        if not _validate_response(response):
            logger.warning(f"Skipping invalid response at index {idx}")
            continue
            
        score_hint = response.get("score_hint")
        
        if score_hint is None:
            logger.debug(f"Response {idx} has no score_hint")
            continue
            
        # Validate score is a number
        try:
            score = float(score_hint)
            if MIN_SCORE <= score <= MAX_SCORE:
                hints.append(score)
            else:
                logger.warning(
                    f"Score {score} at index {idx} is out of range "
                    f"[{MIN_SCORE}, {MAX_SCORE}]"
                )
        except (TypeError, ValueError) as e:
            logger.warning(f"Invalid score_hint at index {idx}: {e}")
    
    logger.info(f"Extracted {len(hints)} valid score hints from {len(responses)} responses")
    return hints


def aggregate_report(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate interview responses into a summary report.
    
    This function processes a list of interview turn responses and generates
    an aggregate evaluation report including average score and summary.
    
    Args:
        responses: List of response dictionaries, each potentially containing
                   a 'score_hint' field
                   
    Returns:
        Dictionary containing:
            - overall_score: Average of all valid score hints, or None
            - summary: Text summary of the evaluation
            - response_count: Number of responses processed
            - scored_responses: Number of responses with valid scores
            
    Raises:
        ValueError: If responses is not a list
        
    Note:
        BUG #4: Division by zero error when hints list is empty.
        The function checks if hints exists but uses the wrong conditional,
        leading to division by zero when len(hints) == 0.
        
    Examples:
        >>> responses = [{"score_hint": 7.5}, {"score_hint": 8.0}, {"other": "data"}]
        >>> result = aggregate_report(responses)
        >>> result['overall_score']
        7.75
        >>> result['scored_responses']
        2
    """
    logger.info("Aggregating evaluation report")
    
    # Validate input
    if not isinstance(responses, list):
        raise ValueError(f"responses must be a list, got {type(responses)}")
    
    if not responses:
        logger.warning("No responses provided for aggregation")
        return {
            "overall_score": None,
            "summary": "No responses to evaluate.",
            "response_count": 0,
            "scored_responses": 0,
        }
    
    # Extract valid score hints
    hints = _extract_score_hints(responses)
    
    # Calculate average score
    # BUG #4: The condition checks `if hints` but should check `if len(hints) > 0`
    # An empty list is falsy, but the logic below could still divide by zero
    # if there's a race condition or if hints is modified elsewhere
    # The bug is subtle: we're checking existence but not preventing division by zero
    avg: Optional[float] = None
    if hints:  # This checks if list is not empty
        # BUG: But what if hints becomes empty between check and division?
        # Or what if someone modifies this code and doesn't realize the dependency?
        # Should be: if len(hints) > 0: avg = sum(hints) / len(hints)
        total = sum(hints)
        # The real bug: using a separate denominator variable that could be 0
        denominator = len([h for h in hints if h > 0])  # BUG: Different filter!
        avg = total / denominator  # Division by zero if all hints are 0
        logger.info(f"Calculated average score: {avg:.2f} from {len(hints)} scores")
    else:
        logger.info("No valid score hints found")
    
    # Generate summary
    if avg is not None:
        if avg >= 8.0:
            summary = "Strong candidate. Interview responses were detailed and well-articulated."
        elif avg >= 6.0:
            summary = "Good candidate. Responses show competence with room for growth."
        elif avg >= 4.0:
            summary = "Fair candidate. Some responses were adequate but lacked depth."
        else:
            summary = "Weak candidate. Responses were generally brief or unclear."
    else:
        summary = "Unable to calculate score. Stub evaluation. Replace with proper rubric and LLM scoring."
    
    result = {
        "overall_score": avg,
        "summary": summary,
        "response_count": len(responses),
        "scored_responses": len(hints),
    }
    
    logger.info(
        f"Report generated: {len(responses)} total responses, "
        f"{len(hints)} scored, avg: {avg}"
    )
    
    return result
