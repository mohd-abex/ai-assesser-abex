from typing import Dict, Any


def aggregate_report(responses: list[Dict[str, Any]]) -> Dict[str, Any]:
    # Placeholder aggregator: average a fake per-turn score_hint
    hints = [r.get("score_hint") for r in responses if r.get("score_hint") is not None]
    avg = sum(hints) / len(hints) if hints else None
    return {
        "overall_score": avg,
        "summary": "Stub evaluation. Replace with proper rubric and LLM scoring.",
    }
