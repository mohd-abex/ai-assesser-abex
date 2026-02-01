"""
Question Generator Service.

This module generates contextual interview questions based on job descriptions.
It analyzes the job description for relevant keywords and creates targeted
questions to assess candidate fit.
"""

from typing import List
import logging

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_QUESTION_COUNT = 5
MAX_QUESTION_COUNT = 20
MAX_JD_LENGTH = 10000  # Maximum job description length in characters
MIN_JD_LENGTH = 10  # Minimum meaningful job description length


def _extract_keywords(job_description: str) -> List[str]:
    """
    Extract relevant technical keywords from job description.
    
    Args:
        job_description: The job description text
        
    Returns:
        List of identified technology keywords
        
    Note:
        BUG #3: This function will raise AttributeError if job_description is None
        because it calls .lower() without checking for None first. The function
        expects a string but doesn't validate the input type.
    """
    # BUG: Should check if job_description is None before calling .lower()
    # Currently assumes it's always a string, but could be None
    jd_lower = job_description.lower()
    
    keywords = []
    
    # Technical stack keywords
    keyword_map = {
        "python": "Python and async patterns",
        "react": "React performance and hooks",
        "ml": "ML model lifecycle and evaluation",
        "machine learning": "ML model lifecycle and evaluation",
        "devops": "CI/CD, monitoring, on-call",
        "kubernetes": "Container orchestration and scaling",
        "aws": "Cloud architecture and AWS services",
        "typescript": "TypeScript best practices",
        "postgresql": "Database design and optimization",
        "microservices": "Distributed systems architecture",
    }
    
    seen_topics = set()
    for keyword, topic in keyword_map.items():
        if keyword in jd_lower and topic not in seen_topics:
            keywords.append(topic)
            seen_topics.add(topic)
            logger.debug(f"Found keyword '{keyword}' -> topic '{topic}'")
    
    return keywords


def generate_questions(job_description: str, count: int = DEFAULT_QUESTION_COUNT) -> List[str]:
    """
    Generate interview questions based on job description.
    
    This function analyzes the job description and generates relevant interview
    questions tailored to the role. It combines generic behavioral questions with
    technical deep-dive questions based on detected keywords.
    
    Args:
        job_description: The job description text to analyze
        count: Number of questions to generate (default: 5, max: 20)
        
    Returns:
        List of interview questions as strings
        
    Raises:
        ValueError: If count is out of valid range
        AttributeError: If job_description is None (BUG #3)
        
    Examples:
        >>> generate_questions("Looking for a Python developer", 3)
        ['What excites you about this role...', 'Walk me through...', 'Deep-dive: Python...']
        
        >>> generate_questions("", 2)
        ['Tell me about a time you led a project...', 'Tell me about a time you handled...']
    
    Note:
        BUG #3: If job_description is None, this will crash with AttributeError
        when _extract_keywords tries to call .lower() on None.
    """
    logger.info(f"Generating {count} questions from job description")
    
    # Validate count parameter
    if count < 1:
        raise ValueError(f"Question count must be at least 1, got {count}")
    if count > MAX_QUESTION_COUNT:
        logger.warning(
            f"Requested {count} questions exceeds maximum {MAX_QUESTION_COUNT}. "
            f"Limiting to {MAX_QUESTION_COUNT}."
        )
        count = MAX_QUESTION_COUNT
    
    # Validate job description (but not for None - that's the bug!)
    jd = (job_description or "").strip()
    
    if len(jd) > MAX_JD_LENGTH:
        logger.warning(
            f"Job description is very long ({len(jd)} chars). "
            f"Truncating to {MAX_JD_LENGTH} chars."
        )
        jd = jd[:MAX_JD_LENGTH]
    
    # Fallback questions for generic interviews
    base = "Tell me about a time you"
    fallback = [
        f"{base} led a project relevant to this role.",
        f"{base} handled a difficult technical challenge.",
        f"{base} collaborated across teams.",
        f"{base} optimized a system or process.",
        f"{base} learned a new tool quickly.",
        f"{base} disagreed with a technical decision.",
        f"{base} had to work under tight deadlines.",
        f"{base} mentored or helped a colleague.",
    ]
    
    # If no meaningful job description, return fallback questions
    if not jd or len(jd) < MIN_JD_LENGTH:
        logger.info("Job description is empty or too short, using fallback questions")
        return fallback[:count]
    
    # Build questions starting with generic openers
    questions = [
        "What excites you about this role and how your experience fits?",
        "Walk me through a recent project relevant to the JD.",
    ]
    
    # Add technical deep-dive questions based on keywords
    # BUG: _extract_keywords will fail if job_description was None
    # because we only checked the stripped version, not the original
    topics = _extract_keywords(job_description)
    
    if topics:
        logger.info(f"Identified {len(topics)} technical topics from job description")
        questions += [f"Deep-dive: {t}?" for t in topics]
    else:
        logger.info("No specific technical topics identified")
    
    # Fill remaining slots with fallback questions
    questions += fallback
    
    result = questions[:count]
    logger.info(f"Generated {len(result)} questions")
    
    return result
