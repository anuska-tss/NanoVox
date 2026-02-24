from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import logging
import json
import whisper
import tempfile
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

from modules import talk_ratio_analyzer, sentiment_analyzer, empathy_analyzer, resolution_analyzer
from scoring_engine import calculate_score
from parameter_registry import get_available_parameters, load_profile_config, get_default_weights

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NanoVox API",
    description="Call Intelligence Dashboard API",
    version="1.0.0"
)

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store Whisper model
whisper_model = None

# Global variable for VADER analyzer
vader_analyzer = None

# Thread pool for running analyzers concurrently
_executor = ThreadPoolExecutor(max_workers=4)


@app.on_event("startup")
async def load_models():
    """Load ML models at startup"""
    global whisper_model, vader_analyzer

    logger.info("loading models...")

    # Load Whisper
    logger.info("Loading Whisper tiny model...")
    whisper_model = whisper.load_model("tiny")
    logger.info("Whisper model loaded!")

    # Load VADER Sentiment
    logger.info("Initializing VADER sentiment analyzer...")
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    logger.info("VADER analyzer initialized!")


def _run_analyzers(transcript: list, profile_config: dict) -> list:
    """
    Run all 4 analyzers and return their results.
    Each analyzer is independent — if one fails, the others still return.
    """
    results = []

    # 1. Talk Ratio
    try:
        results.append(talk_ratio_analyzer.analyze(transcript, profile_config))
    except Exception as e:
        logger.error(f"Talk ratio analyzer failed: {e}")

    # 2. Sentiment (needs VADER instance)
    try:
        results.append(sentiment_analyzer.analyze(transcript, profile_config, vader_analyzer))
    except Exception as e:
        logger.error(f"Sentiment analyzer failed: {e}")

    # 3. Empathy
    try:
        results.append(empathy_analyzer.analyze(transcript, profile_config))
    except Exception as e:
        logger.error(f"Empathy analyzer failed: {e}")

    # 4. Resolution
    try:
        results.append(resolution_analyzer.analyze(transcript, profile_config))
    except Exception as e:
        logger.error(f"Resolution analyzer failed: {e}")

    return results


def analyze_call_insights(transcript_segments: list) -> Dict:
    """
    Legacy insights function — kept for backward compatibility.
    Produces the same response shape the frontend currently expects.
    """
    if not transcript_segments:
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "key_points": [],
            "action_items": [],
            "summary": "No audio transcribed.",
            "customer_frustration": 0.0,
            "agent_empathy": 5.0,
            "call_resolution": False
        }

    # Customer frustration via VADER
    customer_segments = [s for s in transcript_segments if s["speaker"] == "Customer"]
    customer_frustration_score = 0.0
    if customer_segments and vader_analyzer:
        compound_scores = []
        for seg in customer_segments:
            scores = vader_analyzer.polarity_scores(seg["text"])
            compound = scores['compound']
            if compound < -0.05:
                compound_scores.append(abs(compound) * 10.0)
            else:
                compound_scores.append(0.0)
        if compound_scores:
            customer_frustration_score = sum(compound_scores) / len(compound_scores)

    # Agent empathy (simple heuristic)
    agent_texts = [s["text"].lower() for s in transcript_segments if s["speaker"] == "Agent"]
    empathy_keywords = ['sorry', 'apologize', 'understand', 'help', 'assist', 'thank', 'appreciate', 'please']
    agent_empathy_score = 5.0
    if agent_texts:
        match_count = sum(1 for text in agent_texts if any(k in text for k in empathy_keywords))
        if len(agent_texts) > 0:
            empathy_ratio = match_count / len(agent_texts)
            agent_empathy_score = min(10.0, 2.0 + (empathy_ratio * 8.0))

    # Resolution status
    is_resolved = False
    if transcript_segments:
        last_segments = transcript_segments[-3:]
        combined_last_text = " ".join(s["text"].lower() for s in last_segments)
        resolution_keywords = ['thank you', 'thanks', 'great', 'buh-bye', 'bye', 'helped', 'fixed', 'works now']
        if any(k in combined_last_text for k in resolution_keywords):
            is_resolved = True

    overall_sentiment = "neutral"
    if customer_frustration_score > 6.0:
        overall_sentiment = "negative"
    elif customer_frustration_score < 3.0:
        overall_sentiment = "positive"

    return {
        "sentiment": overall_sentiment,
        "sentiment_score": round(customer_frustration_score, 2),
        "key_points": [],
        "action_items": [],
        "summary": "Automated summary unavailable (Offline Mode)",
        "customer_frustration": round(customer_frustration_score, 2),
        "agent_empathy": round(agent_empathy_score, 2),
        "call_resolution": is_resolved
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "message": "NanoVox API is running"}


@app.get("/api/parameters/available")
async def get_parameters():
    """Return all available analysis parameters for dynamic UI generation."""
    return {"parameters": get_available_parameters()}


@app.get("/api/weights/defaults")
async def get_default_weights_endpoint():
    """Return the default Sales profile weights."""
    return {"weights": get_default_weights()}


class RescoreRequest(BaseModel):
    """Request body for the rescore endpoint."""
    analyzer_results: List[dict]
    weights: Dict[str, float]


@app.post("/api/rescore")
async def rescore(request: RescoreRequest) -> Dict:
    """
    Recalculate the final score with new weights.
    Uses cached analyzer results — no re-analysis needed.
    """
    from models import ParameterResult

    try:
        results = [ParameterResult(**r) for r in request.analyzer_results]
        call_score = calculate_score(results, request.weights, "Sales")
        return call_score.model_dump()
    except Exception as e:
        logger.error(f"Rescore failed: {e}", exc_info=True)
        return {"error": str(e), "message": "Rescoring failed"}


@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    weights: Optional[str] = Form(None)
) -> Dict:
    """
    Analyze an audio file: transcribe + run parameter scoring.

    Args:
        file: Audio file (.wav, .mp3, etc.)
        weights: Optional JSON string of custom weights, e.g. '{"talk_ratio":10,"sentiment":20,"empathy":10,"resolution":60}'
    """
    logger.info("\n" + "🔥"*40)
    logger.info("🔥 /ANALYZE ENDPOINT HIT - REQUEST RECEIVED 🔥")
    logger.info("🔥"*40)
    logger.info(f"Received file: {file.filename} ({file.content_type})")

    # Parse custom weights if provided
    custom_weights = None
    if weights:
        try:
            custom_weights = json.loads(weights)
            logger.info(f"Custom weights: {custom_weights}")
        except json.JSONDecodeError:
            logger.warning(f"Invalid weights JSON: {weights}")

    # Read file content
    contents = await file.read()
    file_size_bytes = len(contents)
    logger.info(f"File size: {file_size_bytes} bytes ({file_size_bytes / 1024:.2f} KB)")

    # Save to temporary file for Whisper processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(contents)
        temp_file_path = temp_file.name

    try:
        # ── Step 1: Transcribe with Whisper ──
        logger.info("Starting transcription...")
        result = whisper_model.transcribe(temp_file_path)
        logger.info("Transcription complete!")

        # Heuristic speaker attribution
        def attribute_speaker(segment_text: str, segment_index: int, previous_speaker: str) -> str:
            text_lower = segment_text.lower()

            complaint_keywords = ['problem', 'issue', 'angry', 'frustrated', 'complaint',
                                 'upset', 'disappointed', 'terrible', 'awful', 'bad']
            if any(keyword in text_lower for keyword in complaint_keywords):
                return "Customer"

            agent_keywords = ['help', 'assist', 'sorry', 'apologize', 'understand',
                            'resolve', 'fix', 'support', 'service', 'thank you for']
            if any(keyword in text_lower for keyword in agent_keywords):
                return "Agent"

            if segment_index == 0:
                return "Agent"
            else:
                return "Customer" if previous_speaker == "Agent" else "Agent"

        # Build transcript with speaker attribution
        transcript = []
        previous_speaker = None

        for idx, segment in enumerate(result["segments"]):
            speaker = attribute_speaker(segment["text"], idx, previous_speaker)
            transcript.append({
                "speaker": speaker,
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })
            previous_speaker = speaker

        # ── Step 2: Legacy insights (backward compatibility) ──
        try:
            insights = analyze_call_insights(transcript)
        except Exception as e:
            logger.error(f"Legacy insights failed: {e}")
            insights = {
                "sentiment": "neutral", "sentiment_score": 0.0,
                "key_points": [], "action_items": [],
                "summary": "Analysis failed.",
                "customer_frustration": 0.0, "agent_empathy": 5.0,
                "call_resolution": False
            }

        # ── Step 3: New parameter-based scoring ──
        analysis = None
        try:
            profile_config = load_profile_config("sales")

            # Run analyzers (using thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            analyzer_results = await loop.run_in_executor(
                _executor, _run_analyzers, transcript, profile_config
            )

            # Use custom weights if provided, otherwise profile defaults
            scoring_weights = custom_weights if custom_weights else profile_config["weights"]

            # Score with weights
            call_score = calculate_score(
                analyzer_results,
                scoring_weights,
                profile_config["name"]
            )

            analysis = call_score.model_dump()
            # Include raw analyzer results for frontend rescoring
            analysis["analyzer_results"] = [r.model_dump() for r in analyzer_results]
            logger.info(f"Parameter scoring complete: {call_score.final_score}/100")

        except Exception as e:
            logger.error(f"Parameter scoring failed: {e}", exc_info=True)
            analysis = {"error": str(e), "message": "Parameter scoring unavailable"}

        # ── Build response ──
        response = {
            "filename": file.filename,
            "file_size_bytes": file_size_bytes,
            "transcription": {
                "text": result["text"].strip(),
                "transcript": transcript
            },
            "insights": insights,
            "analysis": analysis
        }

        return response

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info("Temporary file cleaned up")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
