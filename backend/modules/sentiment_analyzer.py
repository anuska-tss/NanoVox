"""
Customer Sentiment Analyzer

Uses VADER to measure customer frustration, with tiered penalties
and a sentiment-journey bonus that rewards de-escalation.

WHY the journey bonus is primary backup: In a complaints context the most
important outcome is whether the agent turned a frustrated customer around.
When the resolution_analyzer returns a neutral score (net_score == 0),
a strong de-escalation (Negative → Positive sentiment journey) must still
produce a positive overall result. This bonus therefore applies an AGGRESSIVE
penalty reduction (up to 60%) instead of the original 30%.
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)


def analyze(transcript: list, profile_config: dict, vader_analyzer=None) -> ParameterResult:
    """
    Analyze customer sentiment using VADER and compute frustration-based penalty.

    Sentiment Journey Bonus (primary backup when resolution is neutral):
      - Improvement threshold: end_avg > start_avg + 0.3  (original 30% reduction)
      - Strong improvement:    end_avg > start_avg + 0.6  → 60% penalty reduction
        This ensures that a clear de-escalation heavily influences the final
        parameter result even when the resolution_analyzer score is neutral.

    Args:
        transcript: List of segments with 'speaker' and 'text'
        profile_config: Profile dict (unused here, kept for interface consistency)
        vader_analyzer: Pre-loaded VADER SentimentIntensityAnalyzer instance

    Returns:
        ParameterResult with frustration (0-10) as raw_value
    """
    if vader_analyzer is None:
        logger.error("VADER analyzer not provided")
        return ParameterResult(
            name="sentiment",
            display_name="Customer Sentiment",
            icon="😊",
            raw_value=5.0,
            score=50.0,
            penalty=50.0,
            metadata={"error": "vader_not_loaded"}
        )

    # Filter customer segments only
    customer_segments = [s for s in transcript if s["speaker"] == "Customer"]

    if not customer_segments:
        logger.info("No customer segments — returning neutral score")
        return ParameterResult(
            name="sentiment",
            display_name="Customer Sentiment",
            icon="😊",
            raw_value=5.0,
            score=50.0,
            penalty=50.0,
            metadata={"no_customer_segments": True, "context_text": "No customer speech detected"}
        )

    # Calculate frustration per segment: frustration = (1 - compound) × 5
    # compound ranges -1 to +1, so frustration ranges 0 to 10
    segment_frustrations = []
    segment_compounds = []

    for seg in customer_segments:
        scores = vader_analyzer.polarity_scores(seg["text"])
        compound = scores["compound"]
        frustration = (1.0 - compound) * 5.0
        segment_frustrations.append(frustration)
        segment_compounds.append(compound)

    avg_frustration = sum(segment_frustrations) / len(segment_frustrations)

    # Tiered penalty calculation
    if avg_frustration <= 3.0:
        base_penalty = avg_frustration * 5.0          # max 15
    elif avg_frustration <= 6.0:
        base_penalty = 15.0 + (avg_frustration - 3.0) * 10.0  # 15–45 range
    else:
        base_penalty = 45.0 + (avg_frustration - 6.0) * 13.75  # 45–100 range

    base_penalty = min(100.0, max(0.0, base_penalty))

    # ── Sentiment Journey Bonus — PRIMARY BACKUP for neutral resolution ──
    # Compare first 3 vs last 3 customer segments to detect de-escalation.
    # A strong improvement (Negative → Positive) applies an aggressive
    # 60% penalty reduction, ensuring it can override a neutral resolution score.
    sentiment_improved = False
    journey_bonus_level = "none"
    n = len(segment_compounds)
    take = min(3, n)

    start_compounds = segment_compounds[:take]
    end_compounds = segment_compounds[-take:] if n > take else segment_compounds

    start_avg = sum(start_compounds) / len(start_compounds)
    end_avg = sum(end_compounds) / len(end_compounds)

    delta = end_avg - start_avg

    if delta > 0.6:
        # Strong de-escalation: 60% penalty reduction (primary backup)
        sentiment_improved = True
        journey_bonus_level = "strong"
        final_penalty = base_penalty * 0.4
        logger.info(
            f"Sentiment journey STRONG bonus applied (Δ={delta:.2f}): "
            f"{base_penalty:.1f} → {final_penalty:.1f}"
        )
    elif delta > 0.3:
        # Moderate improvement: 30% penalty reduction (original behaviour)
        sentiment_improved = True
        journey_bonus_level = "moderate"
        final_penalty = base_penalty * 0.7
        logger.info(
            f"Sentiment journey moderate bonus applied (Δ={delta:.2f}): "
            f"{base_penalty:.1f} → {final_penalty:.1f}"
        )
    else:
        final_penalty = base_penalty

    final_penalty = round(min(100.0, max(0.0, final_penalty)), 2)
    score = round(100.0 - final_penalty, 2)

    logger.info(
        f"Sentiment: frustration={avg_frustration:.2f}/10 | "
        f"Penalty: {final_penalty} | Journey bonus: {journey_bonus_level}"
    )

    return ParameterResult(
        name="sentiment",
        display_name="Customer Sentiment",
        icon="😊",
        raw_value=round(avg_frustration, 2),
        score=score,
        penalty=final_penalty,
        metadata={
            "sentiment_improved": sentiment_improved,
            "journey_bonus_level": journey_bonus_level,
            "start_sentiment": round(start_avg, 3),
            "end_sentiment": round(end_avg, 3),
            "sentiment_delta": round(delta, 3),
            "segment_count": n,
            "context_text": f"Customer frustration: {avg_frustration:.1f}/10"
        }
    )
