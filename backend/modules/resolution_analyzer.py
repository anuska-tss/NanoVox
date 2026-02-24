"""
Resolution Analyzer

Checks the final segments of the call for resolution vs unresolved signals.

WHY last 3 segments: The closing of a call is where resolution language
appears — "is there anything else I can help with" or "I'll need to
transfer you" tells us the outcome.
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)

RESOLUTION_SIGNALS = [
    "resolved",
    "fixed",
    "solution",
    "all set",
    "you're good to go",
    "is there anything else",
    "is there anything else i can help you with",
]

UNRESOLVED_SIGNALS = [
    "escalate",
    "call you back",
    "transfer",
    "not sure",
    "can't help with that",
    "i'll need to check",
]


def analyze(transcript: list, profile_config: dict) -> ParameterResult:
    """
    Detect resolution vs unresolved keywords in the last segments.

    Args:
        transcript: List of segments with 'speaker' and 'text'
        profile_config: Profile dict (kept for interface consistency)

    Returns:
        ParameterResult with net_score as raw_value
    """
    if not transcript:
        logger.warning("No transcript segments for resolution analysis")
        return ParameterResult(
            name="resolution",
            display_name="Resolution Status",
            icon="✅",
            raw_value=0.0,
            score=50.0,
            penalty=50.0,
            metadata={"error": "no_segments", "context_text": "No data available"}
        )

    # Examine last 3 segments (or all if fewer)
    last_segments = transcript[-3:] if len(transcript) >= 3 else transcript
    combined_text = " ".join(s["text"].lower() for s in last_segments)

    resolution_count = 0
    unresolved_count = 0
    found_resolution = []
    found_unresolved = []

    for phrase in RESOLUTION_SIGNALS:
        if phrase in combined_text:
            resolution_count += 1
            found_resolution.append(phrase)

    for phrase in UNRESOLVED_SIGNALS:
        if phrase in combined_text:
            unresolved_count += 1
            found_unresolved.append(phrase)

    net_score = resolution_count - unresolved_count

    # Map net score to penalty
    if net_score >= 2:
        penalty = 10.0
        status = "Resolved"
    elif net_score == 1:
        penalty = 25.0
        status = "Likely resolved"
    elif net_score == 0:
        penalty = 50.0
        status = "Unclear outcome"
    else:
        penalty = 75.0
        status = "Likely unresolved"

    score = 100.0 - penalty

    logger.info(
        f"Resolution: +{resolution_count} -{unresolved_count} = net {net_score} | "
        f"Status: {status} | Penalty: {penalty}"
    )

    return ParameterResult(
        name="resolution",
        display_name="Resolution Status",
        icon="✅",
        raw_value=float(net_score),
        score=score,
        penalty=penalty,
        metadata={
            "resolution_signals": found_resolution,
            "unresolved_signals": found_unresolved,
            "segments_examined": len(last_segments),
            "status": status,
            "context_text": f"Call {status.lower()}" + (" ✓" if net_score >= 1 else "")
        }
    )
