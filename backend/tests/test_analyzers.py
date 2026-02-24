"""
Unit tests for all analyzers and the scoring engine.

Run with: python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from modules import talk_ratio_analyzer, sentiment_analyzer, empathy_analyzer, resolution_analyzer
from scoring_engine import calculate_score
from models import ParameterResult


# ─── Fixtures ─────────────────────────────────────────────────────────────────

SALES_PROFILE = {
    "name": "Sales",
    "weights": {"talk_ratio": 10, "sentiment": 20, "empathy": 10, "resolution": 60},
    "ideal_talk_ratio": [0.60, 0.70]
}

# Default profile alias
DEFAULT_PROFILE = SALES_PROFILE


def make_seg(speaker, text, start, end):
    return {"speaker": speaker, "text": text, "start": start, "end": end}


# ─── Talk Ratio Tests ─────────────────────────────────────────────────────────

class TestTalkRatioAnalyzer:

    def test_perfect_ratio_zero_penalty(self):
        # Sales profile: 60-70% ideal. 65% agent = perfect
        transcript = [
            make_seg("Agent",    "Hello, how can I help?", 0, 65),
            make_seg("Customer", "I have a problem.",       65, 100),
        ]
        result = talk_ratio_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty == 0.0
        assert result.score == 100.0

    def test_agent_talks_too_much(self):
        # Sales profile: 90% agent talk → 20% over the 70% ceiling → penalty = min(100, 0.20*200) = 40
        transcript = [
            make_seg("Agent",    "A" * 10, 0, 90),
            make_seg("Customer", "B" * 10, 90, 100),
        ]
        result = talk_ratio_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty >= 40

    def test_agent_talks_too_little(self):
        # Sales: 20% agent talk is below 60% floor → deviation 40% → penalty = min(100, 0.40*200) = 80
        transcript = [
            make_seg("Agent",    "A" * 10, 0, 20),
            make_seg("Customer", "B" * 10, 20, 100),
        ]
        result = talk_ratio_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty >= 40

    def test_ideal_range_affects_penalty(self):
        # 70% agent talk: ideal for sales (60-70%), penalized with narrower range
        transcript = [
            make_seg("Agent",    "A" * 10, 0, 70),
            make_seg("Customer", "B" * 10, 70, 100),
        ]
        sales_result = talk_ratio_analyzer.analyze(transcript, SALES_PROFILE)
        narrow_profile = {**SALES_PROFILE, "ideal_talk_ratio": [0.40, 0.50]}
        narrow_result = talk_ratio_analyzer.analyze(transcript, narrow_profile)

        # 70% is at the ceiling of sales ideal (60-70) → penalty=0
        assert sales_result.penalty == 0.0
        # 70% is 20% over narrow ideal (40-50) → penalty>0
        assert narrow_result.penalty > 0

    def test_no_segments_returns_neutral(self):
        result = talk_ratio_analyzer.analyze([], SALES_PROFILE)
        assert result.score == 50.0


# ─── Sentiment Analyzer Tests ─────────────────────────────────────────────────

class TestSentimentAnalyzer:

    @pytest.fixture(autouse=True)
    def setup_vader(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self.vader = SentimentIntensityAnalyzer()

    def test_happy_customer_low_penalty(self):
        transcript = [
            make_seg("Customer", "Thank you so much! Everything is perfect and wonderful.", 0, 5),
        ]
        result = sentiment_analyzer.analyze(transcript, SALES_PROFILE, self.vader)
        assert result.penalty < 20  # Happy customer → very low penalty

    def test_angry_customer_high_penalty(self):
        transcript = [
            make_seg("Customer", "This is terrible! I am absolutely furious. This is horrible and unacceptable.", 0, 5),
        ]
        result = sentiment_analyzer.analyze(transcript, SALES_PROFILE, self.vader)
        assert result.penalty > 30

    def test_sentiment_improvement_bonus(self):
        # Start very negative, end very positive — bonus should reduce penalty
        transcript = [
            make_seg("Customer", "I am furious! This is terrible and awful.", 0, 5),
            make_seg("Customer", "This is a disaster! I hate this so much!", 5, 10),
            make_seg("Customer", "This is a disaster! Terrible!", 10, 15),
            make_seg("Agent",    "Let me help you resolve this right away.", 15, 20),
            make_seg("Customer", "Oh thank you! That's wonderful! I appreciate that.", 20, 25),
            make_seg("Customer", "Great! Thank you so much! You're amazing!", 25, 30),
        ]
        result = sentiment_analyzer.analyze(transcript, SALES_PROFILE, self.vader)
        assert result.metadata.get("sentiment_improved") is True

    def test_no_customer_segments_neutral(self):
        transcript = [make_seg("Agent", "Hello there!", 0, 5)]
        result = sentiment_analyzer.analyze(transcript, SALES_PROFILE, self.vader)
        assert result.score == 50.0


# ─── Empathy Analyzer Tests ───────────────────────────────────────────────────

class TestEmpathyAnalyzer:

    def test_high_value_phrases_good_score(self):
        # 3 high-value phrases in a short call → excellent
        transcript = [
            make_seg("Agent", "I completely understand how frustrating this must be.", 0, 10),
            make_seg("Agent", "I sincerely apologize for the inconvenience.", 10, 20),
            make_seg("Agent", "Let me personally help you with this right now.", 20, 30),
        ]
        result = empathy_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.score >= 75

    def test_negative_phrase_subtracts_points(self):
        # Negative phrase mixed with good empathy
        t1 = [make_seg("Agent", "I completely understand. I sincerely apologize.", 0, 30)]
        t2 = [
            make_seg("Agent", "I completely understand. I sincerely apologize.", 0, 30),
            make_seg("Agent", "Unfortunately there's nothing I can do.", 30, 60),
        ]
        r1 = empathy_analyzer.analyze(t1, SALES_PROFILE)
        r2 = empathy_analyzer.analyze(t2, SALES_PROFILE)
        assert r1.score > r2.score

    def test_over_apologizing_diminishing_returns(self):
        # 6 different medium phrases → diminishing returns applied
        transcript = [
            make_seg("Agent", "I understand. I'm sorry to hear that. I apologize. Let me help you. I'll take care of this. Thank you for your patience.", 0, 60),
        ]
        result = empathy_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.metadata.get("phrase_count_medium") >= 5

    def test_short_call_one_phrase_good_score(self):
        # Very short call (1 min), 1 phrase → should be decent score
        transcript = [
            make_seg("Agent",    "I completely understand. Let me help right away.", 0, 30),
            make_seg("Customer", "Thanks!", 30, 60),
        ]
        result = empathy_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.score >= 75

    def test_long_call_one_phrase_poor_score(self):
        # 10-minute call with only 1 phrase → poor
        transcript = [
            make_seg("Agent",    "I understand.", 0, 10),
            make_seg("Customer", "Tell me more.", 10, 600),  # 10 min call
        ]
        result = empathy_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.score < 75

    def test_no_agent_segments_returns_zero(self):
        result = empathy_analyzer.analyze([], SALES_PROFILE)
        assert result.score == 0.0
        assert result.penalty == 100.0


# ─── Resolution Analyzer Tests ───────────────────────────────────────────────

class TestResolutionAnalyzer:

    def test_two_resolution_keywords_penalty_10(self):
        transcript = [
            make_seg("Agent",    "Is there anything else I can help you with?", 0, 5),
            make_seg("Agent",    "Great, that issue is now resolved. You're all set.", 5, 10),
            make_seg("Customer", "Thank you!", 10, 12),
        ]
        result = resolution_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty == 10.0

    def test_two_unresolved_keywords_penalty_75(self):
        transcript = [
            make_seg("Agent",    "I'll need to escalate this to another team.", 0, 5),
            make_seg("Agent",    "We'll call you back about this transfer.", 5, 10),
            make_seg("Customer", "OK.", 10, 12),
        ]
        result = resolution_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty == 75.0

    def test_mixed_signals_penalty_50(self):
        transcript = [
            make_seg("Agent",    "The issue is resolved now.", 0, 5),
            make_seg("Agent",    "I'll need to transfer this case.", 5, 10),
            make_seg("Customer", "OK.", 10, 12),
        ]
        result = resolution_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty == 50.0

    def test_no_keywords_penalty_50(self):
        transcript = [
            make_seg("Agent",    "Goodbye.", 0, 2),
            make_seg("Customer", "Bye.", 2, 4),
        ]
        result = resolution_analyzer.analyze(transcript, SALES_PROFILE)
        assert result.penalty == 50.0

    def test_empty_transcript(self):
        result = resolution_analyzer.analyze([], SALES_PROFILE)
        assert result.score == 50.0


# ─── Scoring Engine Tests ─────────────────────────────────────────────────────

class TestScoringEngine:

    def _make_result(self, name, penalty):
        return ParameterResult(
            name=name, display_name=name.title(), icon="•",
            raw_value=1.0,
            score=100.0 - penalty,
            penalty=penalty
        )

    def test_perfect_scores_give_100(self):
        results = [
            self._make_result("talk_ratio", 0),
            self._make_result("sentiment",  0),
            self._make_result("empathy",    0),
            self._make_result("resolution", 0),
        ]
        score = calculate_score(results, SALES_PROFILE["weights"], "sales")
        assert score.final_score == 100.0

    def test_worst_scores_give_0(self):
        results = [
            self._make_result("talk_ratio", 100),
            self._make_result("sentiment",  100),
            self._make_result("empathy",    100),
            self._make_result("resolution", 100),
        ]
        score = calculate_score(results, SALES_PROFILE["weights"], "sales")
        assert score.final_score == 0.0

    def test_final_score_clamped(self):
        results = [self._make_result("talk_ratio", 150)]
        score = calculate_score(results, SALES_PROFILE["weights"], "sales")
        assert 0 <= score.final_score <= 100

    def test_weight_normalization(self):
        # Weights that don't sum to 100 should still produce valid result
        unnormalized_weights = {"talk_ratio": 5, "sentiment": 5, "empathy": 5, "resolution": 5}
        results = [
            self._make_result("talk_ratio", 0),
            self._make_result("sentiment",  50),
            self._make_result("empathy",    0),
            self._make_result("resolution", 0),
        ]
        score = calculate_score(results, unnormalized_weights, "test")
        assert 0 <= score.final_score <= 100

    def test_breakdown_keys_match_weights(self):
        results = [
            self._make_result("talk_ratio", 20),
            self._make_result("sentiment",  30),
            self._make_result("empathy",    10),
            self._make_result("resolution", 40),
        ]
        score = calculate_score(results, SALES_PROFILE["weights"], "sales")
        assert set(score.breakdown.keys()) == {"talk_ratio", "sentiment", "empathy", "resolution"}

    def test_custom_weights_change_score(self):
        # Bad resolution (penalty=80): high-resolution-weight vs low → different scores
        results = [
            self._make_result("talk_ratio", 0),
            self._make_result("sentiment",  0),
            self._make_result("empathy",    0),
            self._make_result("resolution", 80),  # Bad resolution
        ]
        # Default sales weights (resolution=60)
        high_res_score = calculate_score(results, SALES_PROFILE["weights"], "sales")
        # Custom weights with low resolution importance
        low_res_weights = {"talk_ratio": 30, "sentiment": 30, "empathy": 30, "resolution": 10}
        low_res_score = calculate_score(results, low_res_weights, "sales")
        # High resolution weight → lower score (more penalty from bad resolution)
        assert high_res_score.final_score < low_res_score.final_score
