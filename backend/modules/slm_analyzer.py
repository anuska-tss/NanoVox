"""
SLM Analyzer — Empathy + Resolution via Ollama (phi3:mini)

WHY an SLM here:
  Keyword matching cannot capture context. A call that ends with "Goodbye.
  The ticket is NVX-INC-4421 for your reference." scores 50 (Unclear) under
  keyword matching even though clearly nothing was resolved. phi3:mini reads
  the full transcript and reasons about it the way a human QA auditor would.

Single call, two outputs:
  One Ollama request returns both empathy_score and is_resolved, so latency
  is a single LLM inference (~1–3 s on CPU) rather than two separate calls.

Fallback:
  If Ollama is unreachable, times out, or returns invalid JSON, both
  parameters fall back to a neutral penalty of 50 and log the error.
  This keeps the rest of the scoring pipeline intact.
"""

import json
import logging
import re
import requests
from models import ParameterResult

logger = logging.getLogger(__name__)

# ── Ollama configuration ────────────────────────────────────────────────────────
OLLAMA_URL    = "http://localhost:11434/api/generate"
OLLAMA_MODEL  = "phi3.5"
OLLAMA_TIMEOUT = 90          # seconds — generous for CPU inference on smaller models

# ── System prompt ───────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a Call Quality Auditor. Evaluate a customer support call transcript and return a JSON assessment.

TASK 1 — AGENT EMPATHY (empathy_score: 1 to 10)
Score how emotionally intelligent and empathetic the agent was.

CRITICAL: Being professional and efficient is NOT empathy. Apply these bands strictly:
- 9-10: Multiple genuine empathy phrases ("I completely understand how frustrating this is"),
        acknowledged feelings by name, personalised responses, warm and human tone throughout
- 7-8:  Some empathy phrases used, acknowledged customer's situation, reasonably warm
- 5-6:  Polite and professional but purely transactional — no emotional acknowledgment,
        no empathy phrases, just processes the request efficiently (this is the correct
        score for a standard billing update or account change call with no empathy shown)
- 3-4:  Cold, robotic, minimal acknowledgment of customer as a person
- 1-2:  Dismissive, rude, or actively unhelpful

EXAMPLES:
- Agent says "Confirmed. Please go ahead." → score 5 (professional, not empathetic)
- Agent says "I understand the time pressure you are under, I will do everything I can" → score 8
- Agent says "I'm so sorry for your frustration, that must be very stressful" → score 9


TASK 2 — RESOLUTION STATUS (resolution_score: 0 to 10)
Score how well the customer's issue was resolved by the end of the call.

Apply these bands strictly:
- 9-10: Issue fully fixed on this call, customer explicitly confirmed it works/is sorted
        Examples: "it worked", "I am fully connected", "you are all set", "I am fully sorted"
- 7-8:  Issue substantially resolved, customer satisfied, minor follow-up expected
- 5-6:  Workaround provided that satisfies the customer's immediate need, but root issue
        not fixed (e.g. server outage with CSV export workaround, escalated with timeline given)
        The customer leaves with something useful even though the core problem persists.
- 3-4:  Ticket logged or escalation initiated, no immediate help given, customer not satisfied
- 0-2:  Call failed completely — customer frustrated, nothing resolved, agent unhelpful

EXAMPLES:
- Server is down, agent gives workaround + sends notification email, customer accepts → score 6
- Credit card updated, email sent, customer says "that is all I needed" → score 9
- Agent only says ticket logged, customer still angry → score 3
- Customer hangs up furious, nothing was done → score 1

Be decisive and proportional.

TASK 3 — OVERALL CUSTOMER SENTIMENT (overall_sentiment: Positive, Neutral, or Negative)
Assess the TRUE underlying sentiment of the customer across the whole call.

CRITICAL: You must detect sarcasm and context, not just surface-level polite words.
- "Positive":  Customer was genuinely happy, satisfied, grateful throughout
- "Neutral":   Customer was calm and transactional — no strong emotion either way
- "Negative":  Customer was frustrated, angry, or disappointed — even if they were polite
               about it. Phrases like "Fine", "I guess that works", "Okay whatever",
               "I suppose I'll have to accept that" signal negative sentiment despite
               polite wording. Sarcastic positivity ("Oh great, another issue") = Negative.

EXAMPLES:
- Customer ends with "I am fully sorted. You have been absolutely great!" → Positive
- Customer calmly updates billing details, no emotion → Neutral
- Customer says "Fine, I'll wait for the email I guess" after server outage → Negative
- Customer says "Thank you for doing THAT at least" sarcastically → Negative
- Customer says "This has been one of the most confusing calls I've ever been on" → Negative

OUTPUT: Respond with ONLY this JSON and nothing else:
{
  "empathy_score": <integer 1 to 10>,
  "empathy_reason": "<one sentence, max 20 words>",
  "resolution_score": <integer 0 to 10>,
  "resolution_reason": "<one sentence, max 20 words>",
  "overall_sentiment": "<Positive, Neutral, or Negative>"
}
"""


def _build_transcript_text(transcript: list) -> str:
    """
    Format the transcript as a readable turn-by-turn conversation string
    to send to the model.
    """
    lines = []
    for seg in transcript:
        speaker = seg.get("speaker", "Unknown")
        text    = seg.get("text", "").strip()
        if text:
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def _strip_markdown(raw: str) -> str:
    """
    Local LLMs often wrap JSON in markdown code fences:
        ```json
        { ... }
        ```
    Strip the fences before attempting json.loads().
    """
    # Remove ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip()


def _neutral_empathy() -> ParameterResult:
    return ParameterResult(
        name="empathy",
        display_name="Agent Empathy",
        icon="🤝",
        raw_value=5.0,
        score=50.0,
        penalty=50.0,
        metadata={
            "context_text": "Empathy scoring unavailable — SLM fallback",
            "model_used": "fallback"
        }
    )


def _neutral_resolution() -> ParameterResult:
    return ParameterResult(
        name="resolution",
        display_name="Resolution Status",
        icon="✅",
        raw_value=0.0,
        score=50.0,
        penalty=50.0,
        metadata={
            "context_text": "Resolution scoring unavailable — SLM fallback",
            "model_used": "fallback"
        }
    )


def _neutral_slm_sentiment() -> ParameterResult:
    return ParameterResult(
        name="slm_sentiment",
        display_name="SLM True Sentiment",
        icon="🧠",
        raw_value=0.0,
        score=0.0,
        penalty=0.0,
        metadata={
            "true_sentiment": "Neutral",
            "model_used": "fallback",
            "context_text": "SLM sentiment unavailable — fallback to Neutral",
        }
    )


def analyze(transcript: list, profile_config: dict) -> list:
    """
    Run phi3:mini via Ollama to score Agent Empathy and Resolution Status.

    Args:
        transcript:     List of segments with 'speaker', 'text', 'start', 'end'.
        profile_config: Profile dict (kept for interface consistency — unused here).

    Returns:
        List of two ParameterResult objects: [empathy_result, resolution_result]
        Falls back to neutral (penalty=50) for both if Ollama fails.
    """
    if not transcript:
        logger.warning("SLM analyzer received empty transcript — returning neutral")
        return [_neutral_empathy(), _neutral_resolution()]

    transcript_text = _build_transcript_text(transcript)

    user_prompt = (
        f"Here is the full customer support call transcript:\n\n"
        f"{transcript_text}\n\n"
        "Now evaluate the call and return your JSON assessment."
    )

    payload = {
        "model":  OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "system": SYSTEM_PROMPT,
        "prompt": user_prompt,
    }

    try:
        logger.info(f"SLM: Sending {len(transcript)} segments to {OLLAMA_MODEL} via Ollama...")

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )
        response.raise_for_status()

        response_data = response.json()
        raw_text = response_data.get("response", "")

        logger.info(f"SLM raw response: {raw_text[:400]}")

        # ── Strip markdown fences if present ─────────────────────────────────
        cleaned_text = _strip_markdown(raw_text)

        # ── Parse JSON ────────────────────────────────────────────────────────
        parsed = json.loads(cleaned_text)

        logger.info(f"SLM parsed keys: {list(parsed.keys())}")

        # ── Extract and validate fields ───────────────────────────────────────
        empathy_score     = int(parsed.get("empathy_score", 5))
        empathy_reason    = str(parsed.get("empathy_reason", "No reason provided."))
        resolution_reason = str(parsed.get("resolution_reason", "No reason provided."))

        # Backward-compat: accept both resolution_score (new) and is_resolved (old)
        if "resolution_score" in parsed:
            resolution_score_raw = int(parsed["resolution_score"])
        elif "is_resolved" in parsed:
            # Old boolean schema — convert to score
            logger.warning("SLM: model returned old 'is_resolved' key — converting to resolution_score")
            resolution_score_raw = 9 if bool(parsed["is_resolved"]) else 2
        else:
            logger.warning("SLM: no resolution key found in response — defaulting to 5")
            resolution_score_raw = 5

        # Overall sentiment — SLM true sentiment (sarcasm-aware)
        overall_sentiment = str(parsed.get("overall_sentiment", "Neutral")).strip().capitalize()
        if overall_sentiment not in ("Positive", "Neutral", "Negative"):
            logger.warning(f"SLM: unexpected overall_sentiment value '{overall_sentiment}' — defaulting to Neutral")
            overall_sentiment = "Neutral"

        # Clamp both scores to valid range
        empathy_score        = max(1, min(10, empathy_score))
        resolution_score_raw = max(0, min(10, resolution_score_raw))

        # ── Calculate penalties ───────────────────────────────────────────────
        # Empathy: score 10 → penalty 0, score 1 → penalty 90
        empathy_penalty          = float((10 - empathy_score) * 10)
        empathy_score_normalised = 100.0 - empathy_penalty

        # Resolution: score 10 → penalty 0, score 0 → penalty 100
        resolution_penalty          = float((10 - resolution_score_raw) * 10)
        resolution_score_normalised = 100.0 - resolution_penalty

        # ── Map resolution score to status label ──────────────────────────────
        if resolution_score_raw >= 9:
            resolution_status = "Resolved"
        elif resolution_score_raw >= 7:
            resolution_status = "Likely Resolved"
        elif resolution_score_raw >= 5:
            resolution_status = "Partial Resolution"
        elif resolution_score_raw >= 3:
            resolution_status = "Unresolved — Escalated"
        else:
            resolution_status = "Escalated / Unresolved"

        logger.info(
            f"SLM result: empathy={empathy_score}/10 (penalty={empathy_penalty}) | "
            f"resolution={resolution_score_raw}/10 (penalty={resolution_penalty}) | "
            f"status={resolution_status} | sentiment={overall_sentiment}"
        )

        empathy_result = ParameterResult(
            name="empathy",
            display_name="Agent Empathy",
            icon="🤝",
            raw_value=float(empathy_score),
            score=empathy_score_normalised,
            penalty=empathy_penalty,
            metadata={
                "empathy_score": empathy_score,
                "context_text": empathy_reason,
                "model_used": OLLAMA_MODEL,
            }
        )

        resolution_result = ParameterResult(
            name="resolution",
            display_name="Resolution Status",
            icon="✅",
            raw_value=float(resolution_score_raw),
            score=resolution_score_normalised,
            penalty=resolution_penalty,
            metadata={
                "status": resolution_status,
                "resolution_score": resolution_score_raw,
                "context_text": resolution_reason,
                "model_used": OLLAMA_MODEL,
            }
        )

        slm_sentiment_result = ParameterResult(
            name="slm_sentiment",
            display_name="SLM True Sentiment",
            icon="🧠",
            raw_value=0.0,          # not a numeric score — used as metadata carrier
            score=0.0,
            penalty=0.0,
            metadata={
                "true_sentiment": overall_sentiment,
                "model_used": OLLAMA_MODEL,
                "context_text": f"SLM detected: {overall_sentiment}",
            }
        )

        return [empathy_result, resolution_result, slm_sentiment_result]


    except requests.exceptions.ConnectionError:
        logger.error("SLM: Ollama not reachable at %s — is it running?", OLLAMA_URL)
    except requests.exceptions.Timeout:
        logger.error("SLM: Ollama request timed out after %ds", OLLAMA_TIMEOUT)
    except requests.exceptions.HTTPError as e:
        logger.error("SLM: Ollama returned HTTP error: %s", e)
    except json.JSONDecodeError as e:
        logger.error("SLM: Failed to parse JSON from model response: %s | Raw: %s", e, raw_text[:200])
    except (KeyError, ValueError, TypeError) as e:
        logger.error("SLM: Unexpected field error in parsed response: %s", e)

    # ── Fallback: return neutral scores for all three parameters ─────────────
    logger.warning("SLM: Falling back to neutral scores for empathy, resolution, and sentiment")
    return [_neutral_empathy(), _neutral_resolution(), _neutral_slm_sentiment()]
