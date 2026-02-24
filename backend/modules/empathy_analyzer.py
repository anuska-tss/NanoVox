"""
Agent Empathy Analyzer

Detects empathy phrases in agent speech using a tiered library,
with context-aware scoring (timing, uniqueness, diminishing returns).

WHY tiered phrases: "I completely understand how frustrating this must be"
shows more genuine empathy than a reflexive "sorry" — the scoring reflects
this by assigning 3 points vs 1 point.
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)

# ─── Phrase Library ───────────────────────────────────────────────────────────

HIGH_VALUE_PHRASES = [
    "i completely understand",
    "i totally understand",
    "i absolutely understand",
    "i can imagine how frustrating this must be",
    "i can see why that would be concerning",
    "that must be so frustrating",
    "i sincerely apologize",
    "i truly apologize",
    "let me personally help you with this",
]

MEDIUM_VALUE_PHRASES = [
    "i understand",
    "i'm sorry to hear that",
    "i'm sorry about that",
    "i apologize",
    "let me help you",
    "let me assist you",
    "i'll take care of this",
    "i'll make sure",
    "thank you for your patience",
    "thank you for waiting",
]

LOW_VALUE_PHRASES = [
    "sorry",
    "i see",
    "got it",
    "that makes sense",
]

NEGATIVE_PHRASES = [
    "unfortunately there's nothing i can do",
    "that's not my problem",
    "that's not our responsibility",
    "you should have",
    "you need to",
    "calm down",
    "i already told you",
]

# Customer acknowledgment phrases (signals empathy was effective)
CUSTOMER_ACK_PHRASES = [
    "okay", "ok", "thank you", "thanks", "that helps",
    "i appreciate", "appreciate it", "great", "alright",
]


def _get_timing_multiplier(seg_start: float, total_duration: float) -> float:
    """
    Early empathy is worth more — it sets the tone.
    First 25%: 1.2x, Middle 50%: 1.0x, Last 25%: 0.8x
    """
    if total_duration <= 0:
        return 1.0
    position = seg_start / total_duration
    if position < 0.25:
        return 1.2
    elif position > 0.75:
        return 0.8
    return 1.0


def _get_excellent_threshold(call_duration_seconds: float) -> float:
    """
    Longer calls need more empathy to score well.
    Short (<2 min): 3 points, Medium (2-5 min): 6 points, Long (>5 min): 12 points
    """
    if call_duration_seconds < 30:
        return 1.5  # Very short calls: reduced expectation
    elif call_duration_seconds < 120:
        return 3.0
    elif call_duration_seconds < 300:
        return 6.0
    return 12.0


def analyze(transcript: list, profile_config: dict) -> ParameterResult:
    """
    Detect empathy phrases in agent segments with context-aware scoring.

    Args:
        transcript: List of segments with 'speaker', 'text', 'start', 'end'
        profile_config: Profile dict (kept for interface consistency)

    Returns:
        ParameterResult with empathy_points as raw_value
    """
    agent_segments = [s for s in transcript if s["speaker"] == "Agent"]

    if not agent_segments:
        logger.warning("No agent segments for empathy analysis")
        return ParameterResult(
            name="empathy",
            display_name="Agent Empathy",
            icon="🤝",
            raw_value=0.0,
            score=0.0,
            penalty=100.0,
            metadata={"error": "no_agent_segments"}
        )

    # Total call duration for timing multiplier
    if transcript:
        total_duration = max(s["end"] for s in transcript) - min(s["start"] for s in transcript)
    else:
        total_duration = 0.0

    total_points = 0.0
    detected_phrases = set()  # Uniqueness: each phrase counted once
    high_count = 0
    medium_count = 0
    low_count = 0
    low_points_total = 0
    negative_count = 0
    customer_acknowledged = False

    for i, seg in enumerate(transcript):
        if seg["speaker"] != "Agent":
            continue

        text_lower = seg["text"].lower()
        timing_mult = _get_timing_multiplier(seg["start"], total_duration)

        # ── High-value phrases (3 points each) ──
        for phrase in HIGH_VALUE_PHRASES:
            if phrase in text_lower and phrase not in detected_phrases:
                detected_phrases.add(phrase)
                total_points += 3.0 * timing_mult
                high_count += 1

        # ── Medium-value phrases (2 points each) ──
        for phrase in MEDIUM_VALUE_PHRASES:
            if phrase in text_lower and phrase not in detected_phrases:
                detected_phrases.add(phrase)
                total_points += 2.0 * timing_mult
                medium_count += 1

        # ── Low-value phrases (1 point each, max 2 total) ──
        for phrase in LOW_VALUE_PHRASES:
            if phrase in text_lower and phrase not in detected_phrases:
                detected_phrases.add(phrase)
                if low_points_total < 2:
                    total_points += 1.0 * timing_mult
                    low_points_total += 1
                low_count += 1

        # ── Negative phrases (subtract 2 points each) ──
        for phrase in NEGATIVE_PHRASES:
            if phrase in text_lower and phrase not in detected_phrases:
                detected_phrases.add(phrase)
                total_points -= 2.0
                negative_count += 1

        # ── Customer acknowledgment bonus ──
        # If this agent segment shows empathy and the NEXT segment is customer
        # containing acknowledgment phrases, award +1.5 bonus
        has_empathy_here = any(p in text_lower for p in HIGH_VALUE_PHRASES + MEDIUM_VALUE_PHRASES)
        if has_empathy_here and i + 1 < len(transcript):
            next_seg = transcript[i + 1]
            if next_seg["speaker"] == "Customer":
                next_lower = next_seg["text"].lower()
                if any(ack in next_lower for ack in CUSTOMER_ACK_PHRASES):
                    total_points += 1.5
                    customer_acknowledged = True

    # ── Diminishing returns: penalize over-apologizing ──
    if medium_count >= 5:
        total_points *= 0.9
        logger.info(f"Diminishing returns applied: {medium_count} medium phrases detected")

    # Floor at 0
    total_points = max(0.0, total_points)

    # ── Score conversion based on call duration ──
    excellent = _get_excellent_threshold(total_duration)
    good = excellent * 0.5

    if total_points >= excellent:
        score = 90.0 + min(10.0, (total_points - excellent) / excellent * 10.0)
    elif total_points >= good:
        score = 75.0 + (total_points - good) / (excellent - good) * 14.0
    elif total_points > 0:
        score = 60.0 + (total_points / good) * 14.0
    else:
        score = 30.0

    score = min(100.0, max(0.0, score))
    penalty = 100.0 - score

    logger.info(
        f"Empathy: {total_points:.1f} pts | H:{high_count} M:{medium_count} "
        f"L:{low_count} Neg:{negative_count} | Score: {score:.1f}"
    )

    return ParameterResult(
        name="empathy",
        display_name="Agent Empathy",
        icon="🤝",
        raw_value=round(total_points, 2),
        score=round(score, 2),
        penalty=round(penalty, 2),
        metadata={
            "phrase_count_high": high_count,
            "phrase_count_medium": medium_count,
            "phrase_count_low": low_count,
            "negative_phrases_detected": negative_count,
            "customer_acknowledged": customer_acknowledged,
            "call_duration": round(total_duration, 2),
            "excellent_threshold": excellent,
            "detected_phrases": list(detected_phrases),
            "context_text": f"{len(detected_phrases)} empathy phrases detected"
        }
    )
