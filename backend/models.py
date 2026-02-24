"""
Pydantic data models for the parameter-based scoring system.

These models define the contract between analyzers, the scoring engine,
and the API response — ensuring type safety throughout the pipeline.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional


class ParameterResult(BaseModel):
    """Output from a single analyzer module."""
    name: str
    display_name: str = ""
    icon: str = ""
    raw_value: float
    score: float  # Scoring engine clamps the CallScore output, not raw analyzer results
    penalty: float
    metadata: dict = {}


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
    final_score: float = Field(ge=0, le=100)
    breakdown: Dict[str, ParameterBreakdown]
    profile_used: str
    interpretation: str = ""
    metadata: dict = {}


class ProfileConfig(BaseModel):
    """Configuration for a client profile."""
    name: str
    description: str
    weights: Dict[str, float]
    ideal_talk_ratio: list[float] = [0.40, 0.60]
