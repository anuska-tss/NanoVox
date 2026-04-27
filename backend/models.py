"""
Pydantic data models for the parameter-based scoring system.

These models define the contract between analyzers, the scoring engine,
and the API response — ensuring type safety throughout the pipeline.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional


class TranscriptSegment(BaseModel):
    """A single segment of a call transcript."""
    speaker: str = Field(..., description="Label for the speaker", example="Agent")
    start: float = Field(..., description="Start time in seconds", example=0.0)
    end: float = Field(..., description="End time in seconds", example=5.0)
    text: str = Field(..., description="The spoken text", example="Hello, how can I help you?")


class ParameterResult(BaseModel):
    """Output from a single analyzer module."""
    name: str = Field(..., description="Unique identifier for the parameter", example="talk_ratio")
    display_name: str = Field("", description="Human-readable name", example="Talk Ratio")
    icon: str = Field("", description="Emoji or icon shorthand", example="🗣️")
    raw_value: float = Field(..., description="The non-normalized value from the analyzer", example=0.65)
    score: float = Field(..., description="The normalized score (0-100)", example=85.0)
    penalty: float = Field(..., description="Points lost from 100", example=15.0)
    metadata: dict = Field({}, description="Additional debug/context info")


class ParameterBreakdown(BaseModel):
    """A scored parameter with its weight and contribution to final score."""
    raw_value: float
    score: float
    penalty: float
    weight: float
    contribution: float  # Negative number (points lost from 100)
    display_name: str = ""
    icon: str = ""
    metadata: dict = {}


class CallScore(BaseModel):
    """Complete scoring result returned by the scoring engine."""
    final_score: float = Field(..., ge=0, le=100, description="The overall weighted score", example=78.5)
    breakdown: Dict[str, ParameterBreakdown] = Field(..., description="Details for each scoring parameter")
    profile_used: str = Field(..., description="The name of the configuration profile used", example="Sales")
    interpretation: str = Field("", description="A human-readable summary of the score outcome", example="Strong performance with high empathy.")
    metadata: dict = Field({}, description="Additional debug/context info")


class CallSummary(BaseModel):
    """A brief summary of a call from the history table."""
    id: int = Field(..., example=1)
    filename: str = Field(..., example="call_recording.wav")
    file_size_bytes: int = Field(0, example=1024500)
    analyzed_at: str = Field(..., example="2023-10-27T10:00:00Z")
    final_score: float = Field(..., example=82.4)
    profile_used: str = Field("Sales", example="Sales")
    interpretation: str = Field("", example="Good closure.")
    commitment_status: str = Field("Unknown", example="Resolved")
    call_duration: float = Field(0.0, example=145.2)
    segment_count: int = Field(0, example=14)
    agent_name: Optional[str] = Field(None, example="David")


class Stats(BaseModel):
    """Aggregate statistics for the entire call history."""
    total_calls: int = Field(0, example=150)
    avg_score: float = Field(0.0, example=75.2)
    min_score: float = Field(0.0, example=45.0)
    max_score: float = Field(0.0, example=98.0)
    avg_talk_ratio: float = Field(0.0, example=65.0)
    avg_sentiment: float = Field(0.0, example=70.5)
    avg_empathy: float = Field(0.0, example=80.0)
    avg_commitment: float = Field(0.0, example=60.5)
    committed_count: int = Field(0, example=120)
    ghosted_count: int = Field(0, example=30)

