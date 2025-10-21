from typing import List


def generate_questions(job_description: str, count: int = 5) -> List[str]:
    jd = (job_description or "").strip()
    base = "Tell me about a time you"
    fallback = [
        f"{base} led a project relevant to this role.",
        f"{base} handled a difficult technical challenge.",
        f"{base} collaborated across teams.",
        f"{base} optimized a system or process.",
        f"{base} learned a new tool quickly.",
    ]

    if not jd:
        return fallback[:count]

    topics = []
    if "python" in jd.lower():
        topics.append("Python and async patterns")
    if "react" in jd.lower():
        topics.append("React performance and hooks")
    if "ml" in jd.lower() or "machine learning" in jd.lower():
        topics.append("ML model lifecycle and evaluation")
    if "devops" in jd.lower():
        topics.append("CI/CD, monitoring, on-call")

    questions = [
        f"What excites you about this role and how your experience fits?",
        f"Walk me through a recent project relevant to the JD.",
    ]
    questions += [f"Deep-dive: {t}?" for t in topics]
    questions += fallback

    return questions[:count]
