"""
Talk-to-Listen Ratio Analyzer

Measures how much the agent spoke vs total call duration,
then penalizes deviations from the profile's ideal range.

WHY this matters: Sales agents should talk more (pitching/closing),
while complaint handlers should listen more (de-escalation).
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)


def analyze(transcript: list, profile_config: dict) -> ParameterResult:
    """
    Calculate agent talk ratio and score against profile-specific ideal range.

    Args:
        transcript: List of segments with 'speaker', 'start', 'end' keys
        profile_config: Profile dict with 'ideal_talk_ratio' [min, max]

    Returns:
        ParameterResult with ratio as raw_value and penalty based on deviation
    """
    if not transcript:
        logger.warning("No transcript segments for talk ratio analysis")
        return ParameterResult(
            name="talk_ratio",
            display_name="Talk-to-Listen Ratio",
            icon="🎙️",
            raw_value=0.0,
            score=50.0,
            penalty=50.0,
            metadata={"error": "no_segments"}
        )

    # Calculate agent talk time from segment timestamps
    agent_talk_time = 0.0
    total_call_time = 0.0

    for seg in transcript:
        duration = seg["end"] - seg["start"]
        total_call_time += duration
        if seg["speaker"] == "Agent":
            agent_talk_time += duration

    # Avoid division by zero
    if total_call_time <= 0:
        logger.warning("Total call time is zero")
        return ParameterResult(
            name="talk_ratio",
            display_name="Talk-to-Listen Ratio",
            icon="🎙️",
            raw_value=0.0,
            score=50.0,
            penalty=50.0,
            metadata={"error": "zero_duration"}
        )

    ratio = agent_talk_time / total_call_time

    # Load ideal range from profile (e.g., [0.40, 0.60] for support)
    ideal_range = profile_config.get("ideal_talk_ratio", [0.40, 0.60])
    ideal_min, ideal_max = ideal_range[0], ideal_range[1]

    # Penalty based on deviation from ideal range
    if ideal_min <= ratio <= ideal_max:
        penalty = 0.0
    elif ratio < ideal_min:
        deviation = ideal_min - ratio
        penalty = min(100.0, deviation * 200.0)
    else:
        deviation = ratio - ideal_max
        penalty = min(100.0, deviation * 200.0)

    score = 100.0 - penalty

    logger.info(
        f"Talk ratio: {ratio:.2%} | Ideal: {ideal_min:.0%}-{ideal_max:.0%} | "
        f"Score: {score:.1f} | Penalty: {penalty:.1f}"
    )

    return ParameterResult(
        name="talk_ratio",
        display_name="Talk-to-Listen Ratio",
        icon="🎙️",
        raw_value=round(ratio, 4),
        score=round(score, 2),
        penalty=round(penalty, 2),
        metadata={
            "agent_talk_time": round(agent_talk_time, 2),
            "total_call_time": round(total_call_time, 2),
            "ideal_range": ideal_range,
            "context_text": f"Agent spoke {ratio:.0%} of the time"
        }
    )
