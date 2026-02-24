"""
Customer Sentiment Analyzer

Uses VADER to measure customer frustration, with tiered penalties
and a sentiment-journey bonus that rewards de-escalation.

WHY tiered penalties: A frustration of 8 is far worse than 4, so the
penalty curve accelerates — low frustration barely hurts, but high
frustration hammers the score.
"""
import logging
from models import ParameterResult

logger = logging.getLogger(__name__)


def analyze(transcript: list, profile_config: dict, vader_analyzer=None) -> ParameterResult:
    """
    Analyze customer sentiment using VADER and compute frustration-based penalty.

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
        base_penalty = avg_frustration * 5.0  # max 15
    elif avg_frustration <= 6.0:
        base_penalty = 15.0 + (avg_frustration - 3.0) * 10.0  # 15-45 range
    else:
        base_penalty = 45.0 + (avg_frustration - 6.0) * 13.75  # 45-100 range

    base_penalty = min(100.0, max(0.0, base_penalty))

    # Sentiment journey bonus: compare first vs last segments
    sentiment_improved = False
    n = len(segment_compounds)
    take = min(3, n)

    start_compounds = segment_compounds[:take]
    end_compounds = segment_compounds[-take:] if n > take else segment_compounds

    start_avg = sum(start_compounds) / len(start_compounds)
    end_avg = sum(end_compounds) / len(end_compounds)

    # If end sentiment improved by 0.3+ → 30% penalty reduction
    if end_avg > start_avg + 0.3:
        sentiment_improved = True
        final_penalty = base_penalty * 0.7
        logger.info(f"Sentiment journey bonus applied: {base_penalty:.1f} → {final_penalty:.1f}")
    else:
        final_penalty = base_penalty

    final_penalty = round(min(100.0, max(0.0, final_penalty)), 2)
    score = round(100.0 - final_penalty, 2)

    logger.info(
        f"Sentiment: frustration={avg_frustration:.2f}/10 | "
        f"Penalty: {final_penalty} | Improved: {sentiment_improved}"
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
            "start_sentiment": round(start_avg, 3),
            "end_sentiment": round(end_avg, 3),
            "segment_count": n,
            "context_text": f"Customer frustration: {avg_frustration:.1f}/10"
        }
    )
