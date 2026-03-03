"""
Talk-to-Listen Ratio Analyzer (Phase-Aware)

Splits the call into 3 time-based phases (Discovery, Middle, Closing)
and evaluates agent talk ratio against phase-specific ideal ranges.

WHY phase-aware: In sales, the agent should listen during Discovery
(understand the customer's needs), balance during Middle, and lead
during Closing (drive the deal). A flat ratio misses this nuance.
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)

# ── Phase Definitions ──
# Each phase has a name, an ideal agent talk ratio range, and a weight
# toward the final penalty.

PHASES = [
    {
        "name": "Discovery",
        "start_pct": 0.0,
        "end_pct": 0.33,
        "ideal_range": [0.20, 0.40],
        "weight": 0.40,
        "too_high_msg": "Talked too much in Discovery — should listen more",
        "too_low_msg": "Too quiet in Discovery — missed opportunity to ask questions",
    },
    {
        "name": "Middle",
        "start_pct": 0.33,
        "end_pct": 0.66,
        "ideal_range": [0.40, 0.60],
        "weight": 0.20,
        "too_high_msg": "Dominated the Middle phase — should balance dialogue",
        "too_low_msg": "Under-engaged in Middle phase",
    },
    {
        "name": "Closing",
        "start_pct": 0.66,
        "end_pct": 1.0,
        "ideal_range": [0.60, 0.80],
        "weight": 0.40,
        "too_high_msg": "Over-talked in Closing — may feel pushy",
        "too_low_msg": "Too passive in Closing — should lead the close",
    },
]


def _compute_phase_ratio(segments: list, phase_start: float, phase_end: float) -> dict:
    """
    Calculate agent talk ratio for segments falling within a time window.
    Returns dict with ratio, agent_time, total_time, and segment count.
    """
    agent_time = 0.0
    total_time = 0.0
    seg_count = 0

    for seg in segments:
        # Include segment if it overlaps with the phase window
        seg_start = max(seg["start"], phase_start)
        seg_end = min(seg["end"], phase_end)

        if seg_start >= seg_end:
            continue  # No overlap

        duration = seg_end - seg_start
        total_time += duration
        seg_count += 1

        if seg["speaker"] == "Agent":
            agent_time += duration

    if total_time <= 0:
        return {"ratio": 0.5, "agent_time": 0.0, "total_time": 0.0, "seg_count": 0}

    return {
        "ratio": agent_time / total_time,
        "agent_time": round(agent_time, 2),
        "total_time": round(total_time, 2),
        "seg_count": seg_count,
    }


def _phase_penalty(ratio: float, ideal_min: float, ideal_max: float) -> float:
    """Calculate penalty for deviation from ideal range, capped at 100."""
    if ideal_min <= ratio <= ideal_max:
        return 0.0
    elif ratio < ideal_min:
        deviation = ideal_min - ratio
    else:
        deviation = ratio - ideal_max

    return min(100.0, deviation * 200.0)


def analyze(transcript: list, profile_config: dict) -> ParameterResult:
    """
    Phase-aware talk ratio analysis for sales calls.

    Splits transcript into Discovery (0-33%), Middle (33-66%), Closing (66-100%)
    and evaluates each against phase-specific ideal ranges.

    Args:
        transcript: List of segments with 'speaker', 'start', 'end' keys
        profile_config: Profile dict (phase config is built-in for sales)

    Returns:
        ParameterResult with overall ratio as raw_value and phase-weighted penalty
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

    # Determine call time boundaries
    call_start = min(s["start"] for s in transcript)
    call_end = max(s["end"] for s in transcript)
    call_duration = call_end - call_start

    if call_duration <= 0:
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

    # ── Analyze each phase ──
    phase_results = []
    total_weighted_penalty = 0.0
    struggles = []

    # Overall ratio (for raw_value)
    overall_agent_time = 0.0
    overall_total_time = 0.0

    for phase in PHASES:
        phase_start = call_start + (call_duration * phase["start_pct"])
        phase_end = call_start + (call_duration * phase["end_pct"])

        result = _compute_phase_ratio(transcript, phase_start, phase_end)
        penalty = _phase_penalty(result["ratio"], phase["ideal_range"][0], phase["ideal_range"][1])
        weighted_penalty = penalty * phase["weight"]
        total_weighted_penalty += weighted_penalty

        overall_agent_time += result["agent_time"]
        overall_total_time += result["total_time"]

        # Identify struggles
        struggle_msg = None
        if result["ratio"] > phase["ideal_range"][1]:
            struggle_msg = phase["too_high_msg"]
        elif result["ratio"] < phase["ideal_range"][0]:
            struggle_msg = phase["too_low_msg"]

        if struggle_msg:
            struggles.append(struggle_msg)

        phase_results.append({
            "phase": phase["name"],
            "ratio": round(result["ratio"], 4),
            "ratio_pct": f"{result['ratio']:.0%}",
            "ideal_range": phase["ideal_range"],
            "ideal_range_pct": f"{phase['ideal_range'][0]:.0%}-{phase['ideal_range'][1]:.0%}",
            "penalty": round(penalty, 2),
            "weighted_penalty": round(weighted_penalty, 2),
            "weight": phase["weight"],
            "agent_time": result["agent_time"],
            "total_time": result["total_time"],
            "segments": result["seg_count"],
            "struggle": struggle_msg,
        })

    # Clamp total penalty
    total_weighted_penalty = min(100.0, max(0.0, total_weighted_penalty))
    score = 100.0 - total_weighted_penalty

    # Overall ratio for raw_value
    overall_ratio = overall_agent_time / overall_total_time if overall_total_time > 0 else 0.5

    # Build context text
    if not struggles:
        context_text = f"Agent spoke {overall_ratio:.0%} — balanced across all phases"
    else:
        context_text = struggles[0]  # Show the most notable struggle

    logger.info(
        f"Talk ratio (phase-aware): overall={overall_ratio:.2%} | "
        f"D={phase_results[0]['ratio_pct']} M={phase_results[1]['ratio_pct']} "
        f"C={phase_results[2]['ratio_pct']} | Score: {score:.1f}"
    )

    return ParameterResult(
        name="talk_ratio",
        display_name="Talk-to-Listen Ratio",
        icon="🎙️",
        raw_value=round(overall_ratio, 4),
        score=round(score, 2),
        penalty=round(total_weighted_penalty, 2),
        metadata={
            "overall_ratio": round(overall_ratio, 4),
            "overall_ratio_pct": f"{overall_ratio:.0%}",
            "call_duration": round(call_duration, 2),
            "phases": phase_results,
            "struggles": struggles,
            "context_text": context_text,
        }
    )
