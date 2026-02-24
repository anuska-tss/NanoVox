"""
Scoring Engine

Combines analyzer results with profile-specific weights to produce
a final 0-100 score.

Formula: Final_Score = 100 - Σ(weight_i × penalty_i / 100)

WHY weight normalization: If a profile only defines 3 of 4 parameters,
the weights still sum to 100% — preventing score inflation/deflation.
"""
import logging
from typing import Dict, List
from models import ParameterResult, ParameterBreakdown, CallScore

logger = logging.getLogger(__name__)


def _generate_interpretation(final_score: float, breakdown: Dict[str, ParameterBreakdown]) -> str:
    """
    Generate a human-readable 1-2 sentence interpretation of the score.
    Highlights the biggest strengths and concerns.
    """
    strengths = []
    concerns = []

    for key, param in breakdown.items():
        if param.penalty <= 15:
            strengths.append(param.display_name.lower())
        elif param.penalty >= 50:
            concerns.append(param.display_name.lower())

    parts = []

    if final_score >= 90:
        parts.append("Excellent call performance across the board.")
    elif final_score >= 75:
        parts.append("Good call with solid overall performance.")
    elif final_score >= 60:
        parts.append("Adequate call with room for improvement.")
    elif final_score >= 50:
        parts.append("Below-average call needing attention.")
    else:
        parts.append("Poor call performance requiring immediate coaching.")

    if strengths:
        parts.append(f"Strong {', '.join(strengths[:2])}.")
    if concerns:
        parts.append(f"Needs improvement in {', '.join(concerns[:2])}.")

    return " ".join(parts)


def calculate_score(
    analyzer_results: List[ParameterResult],
    weights: Dict[str, float],
    profile_name: str
) -> CallScore:
    """
    Compute the final weighted score from analyzer results.

    Args:
        analyzer_results: List of ParameterResult from each analyzer
        weights: Dict of parameter_name → weight (from profile config)
        profile_name: Name of the profile used

    Returns:
        CallScore with final_score, breakdown, and interpretation
    """
    # Build lookup by name
    results_by_name = {r.name: r for r in analyzer_results}

    # Normalize weights so they sum to 100
    relevant_weights = {k: v for k, v in weights.items() if k in results_by_name}

    if not relevant_weights:
        logger.warning("No matching weights for any analyzer result")
        return CallScore(
            final_score=50.0,
            breakdown={},
            profile_used=profile_name,
            interpretation="Unable to calculate score — no analyzer results matched profile weights.",
            metadata={"error": "no_matching_weights"}
        )

    weight_sum = sum(relevant_weights.values())
    if weight_sum <= 0:
        weight_sum = 1.0  # Prevent division by zero

    normalized_weights = {k: (v / weight_sum) * 100 for k, v in relevant_weights.items()}

    # Calculate weighted penalties and build breakdown
    total_weighted_penalty = 0.0
    breakdown: Dict[str, ParameterBreakdown] = {}
    combined_metadata = {}

    for param_name, weight in normalized_weights.items():
        result = results_by_name[param_name]
        contribution = -(weight * result.penalty / 100.0)
        total_weighted_penalty += abs(contribution)

        breakdown[param_name] = ParameterBreakdown(
            raw_value=result.raw_value,
            score=result.score,
            penalty=result.penalty,
            weight=round(weight, 2),
            contribution=round(contribution, 2),
            display_name=result.display_name,
            icon=result.icon,
            metadata=result.metadata
        )

        # Merge metadata
        if result.metadata:
            combined_metadata[param_name] = result.metadata

    # Final score: 100 minus total weighted penalties, clamped 0-100
    final_score = max(0.0, min(100.0, 100.0 - total_weighted_penalty))
    final_score = round(final_score, 2)

    interpretation = _generate_interpretation(final_score, breakdown)

    logger.info(f"Final score: {final_score}/100 | Profile: {profile_name}")

    return CallScore(
        final_score=final_score,
        breakdown=breakdown,
        profile_used=profile_name,
        interpretation=interpretation,
        metadata=combined_metadata
    )


