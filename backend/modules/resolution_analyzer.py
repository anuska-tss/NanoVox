"""
Resolution Analyzer

Analyzes the final 25% of the call for resolution signals that indicate
the customer's issue was actually fixed (resolved, sorted, rectified, etc.)
vs failure/escalation signals where the call breaks down.

WHY final 25%: Resolutions and escalations happen in the closing phase
of a support call. Analyzing the full call would dilute the signal.
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)

# ── Resolution Signals (+2 points each) ──
# Language indicating the customer's issue was genuinely fixed
RESOLUTION_SIGNALS = [
    "fixed", "resolved", "rectified", "sorted", "done",
    "solved", "processed", "completed", "corrected", "taken care",
    "all set", "good to go", "working now", "works now",
]

# ── Failure / Escalation Signals (-1 point each) ──
# Language indicating the call broke down or customer was unsatisfied
FAILURE_SIGNALS = [
    "manager", "supervisor", "unhappy", "not helping",
    "escalate", "useless", "not working", "waste of time",
    "ridiculous", "unacceptable",
]


def analyze(transcript: list, profile_config: dict) -> ParameterResult:
    """
    Detect resolution vs failure/escalation signals in the closing window (last 25%).

    Scoring:
      • Each resolution signal found in the closing window: +2 points
      • Each failure/escalation signal found:               -1 point
      • net_score drives the final penalty bucket

    Args:
        transcript: List of segments with 'speaker', 'text', 'start', 'end'
        profile_config: Profile dict (kept for interface consistency)

    Returns:
        ParameterResult with net resolution score as raw_value
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

    # ── Determine closing window (last 25% of call) ──
    call_start = min(s["start"] for s in transcript)
    call_end = max(s["end"] for s in transcript)
    call_duration = call_end - call_start

    if call_duration <= 0:
        logger.warning("Call duration is zero")
        return ParameterResult(
            name="resolution",
            display_name="Resolution Status",
            icon="✅",
            raw_value=0.0,
            score=50.0,
            penalty=50.0,
            metadata={"error": "zero_duration", "context_text": "No data available"}
        )

    closing_start = call_start + (call_duration * 0.75)

    # Filter to only closing window segments
    closing_segments = [seg for seg in transcript if seg["end"] > closing_start]

    if not closing_segments:
        logger.info("No segments in closing window — scoring as unclear")
        return ParameterResult(
            name="resolution",
            display_name="Resolution Status",
            icon="✅",
            raw_value=0.0,
            score=50.0,
            penalty=50.0,
            metadata={
                "closing_window_start": round(closing_start, 2),
                "segments_in_window": 0,
                "status": "Unclear outcome",
                "context_text": "No speech in closing window"
            }
        )

    # ── Score resolution vs failure signals ──
    combined_text = " ".join(s["text"].lower() for s in closing_segments)

    resolution_points = 0
    failure_points = 0
    found_resolution = []
    found_failure = []

    for phrase in RESOLUTION_SIGNALS:
        if phrase in combined_text:
            resolution_points += 2
            found_resolution.append(phrase)

    for phrase in FAILURE_SIGNALS:
        if phrase in combined_text:
            failure_points += 1
            found_failure.append(phrase)

    net_score = resolution_points - failure_points

    # ── Map net score to penalty and status ──
    if net_score >= 2:
        penalty = 0.0
        status = "Resolved"
        interpretation = "Issue successfully resolved — customer confirmed fix"
    elif net_score == 1:
        penalty = 25.0
        status = "Likely resolved"
        interpretation = "Partial resolution signals — follow-up recommended"
    elif net_score == 0:
        penalty = 50.0
        status = "Unclear outcome"
        interpretation = "No resolution detected — could not confirm issue was fixed"
    else:
        penalty = 100.0
        status = "Escalated / Unresolved"
        interpretation = "Failure or escalation signals detected — high dissatisfaction risk"

    score = 100.0 - penalty

    logger.info(
        f"Resolution: +{resolution_points} resolution, -{failure_points} failure = "
        f"net {net_score} | Status: {status} | Penalty: {penalty}"
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
            "failure_signals": found_failure,
            "resolution_points": resolution_points,
            "failure_points": failure_points,
            "net_score": net_score,
            "segments_in_window": len(closing_segments),
            "closing_window_start": round(closing_start, 2),
            "call_duration": round(call_duration, 2),
            "status": status,
            "interpretation": interpretation,
            "detected_phrases": found_resolution + found_failure,
            "context_text": f"Call {status.lower()}" + (" ✓" if net_score >= 1 else ""),
        }
    )
