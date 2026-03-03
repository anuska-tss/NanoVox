from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
import logging
import json
import io
import whisper
import tempfile
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

from modules import talk_ratio_analyzer, sentiment_analyzer, empathy_analyzer, resolution_analyzer
from scoring_engine import calculate_score
from parameter_registry import get_available_parameters, load_profile_config, get_default_weights
from database import init_db, save_call, get_history, get_call_detail, get_stats
from report_generator import generate_report

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

    # Initialize SQLite database
    init_db()
    logger.info("Database initialized!")


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


class TestAnalysisRequest(BaseModel):
    """
    Request body for the /api/test-analysis endpoint.

    Allows direct scoring-engine testing without an audio file.
    The transcript segments must match the format produced by Whisper +
    the speaker-attribution step:

        [
          {"speaker": "Agent",    "start": 0.0,  "end": 5.2,  "text": "..."},
          {"speaker": "Customer", "start": 5.4,  "end": 10.1, "text": "..."}
        ]

    Weights should sum to 100 and use the canonical parameter names
    (talk_ratio, sentiment, empathy, resolution).
    """
    transcript: List[dict]
    weights: Optional[Dict[str, float]] = None
    profile: Optional[str] = "complaints"


@app.post("/api/test-analysis")
async def test_analysis(request: TestAnalysisRequest) -> Dict:
    """
    Run the full scoring pipeline on a manually supplied transcript.

    Bypasses Whisper transcription entirely — useful for:
      • Unit-testing the scoring engine with controlled inputs
      • Validating complaints vs sales profile weight differences
      • Debugging analyzer logic without an audio file

    Body:
        transcript: list of {speaker, start, end, text} dicts
        weights:    optional custom weights (overrides profile defaults)
        profile:    'complaints' | 'sales'  (default: 'complaints')
    """
    logger.info(
        f"🧪 /api/test-analysis hit — "
        f"{len(request.transcript)} segments, profile='{request.profile}'"
    )

    if not request.transcript:
        return {"error": "transcript must not be empty"}

    try:
        profile_config = load_profile_config(request.profile or "complaints")

        # Run all four analyzers against the supplied transcript
        loop = asyncio.get_event_loop()
        analyzer_results = await loop.run_in_executor(
            _executor, _run_analyzers, request.transcript, profile_config
        )

        # Use supplied weights → profile defaults → built-in defaults
        scoring_weights = (
            request.weights
            if request.weights
            else profile_config.get("weights", get_default_weights(request.profile or "complaints"))
        )

        call_score = calculate_score(
            analyzer_results,
            scoring_weights,
            profile_config["name"]
        )

        result = call_score.model_dump()
        result["analyzer_results"] = [r.model_dump() for r in analyzer_results]
        result["scoring_weights_used"] = scoring_weights
        result["profile_used"] = profile_config["name"]
        result["segment_count"] = len(request.transcript)

        logger.info(f"Test analysis complete: {call_score.final_score}/100")
        return result

    except Exception as e:
        logger.error(f"Test analysis failed: {e}", exc_info=True)
        return {"error": str(e), "message": "Test analysis failed"}


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

        # ── Global Weighted Voting Speaker Attribution ──
        def identify_speakers(whisper_segments: list) -> list:
            """
            Global Weighted Voting System for speaker attribution.
            Instead of labeling each segment independently, this:
            1. Groups segments into two alternating speakers (0 and 1)
            2. Scores each speaker globally using signal libraries
            3. Applies structural bonuses (Anchor, Closer)
            4. Maps the higher-scoring speaker to 'Agent'
            """
            if not whisper_segments:
                return []

            # ── Signal Libraries ──
            AGENT_SIGNALS = [
                'speaking', 'calling from', 'timeline', 'decision maker',
                'budget', 'our solution', 'calendar', 'invite', 'meeting',
                'contract', 'agreement', 'certainly', 'my pleasure',
                'absolutely', 'welcome', 'helping', 'demonstration',
                'benefits', 'features', 'integration',
            ]

            CUSTOMER_SIGNALS = [
                'calling about', 'problem with', 'expensive', 'too much',
                'fix this', 'broken', 'frustrated', 'can it do',
                'not interested', 'help me', 'looking for', 'does it have',
                'comparison', 'budget constraints',
            ]

            # ── Step 1: Assign alternating speaker IDs ──
            # In a conversation, speakers typically alternate turns
            speaker_ids = []
            current_id = 0
            for i, seg in enumerate(whisper_segments):
                if i == 0:
                    speaker_ids.append(current_id)
                else:
                    # Check for a natural speaker change via pause gap
                    gap = seg["start"] - whisper_segments[i - 1]["end"]
                    if gap > 0.3:
                        # Likely a speaker change if there's a pause
                        current_id = 1 - current_id
                    # else: same speaker continues (no flip)
                    speaker_ids.append(current_id)

            # ── Step 2: Score each speaker globally ──
            scores = {0: 0, 1: 0}

            for i, seg in enumerate(whisper_segments):
                text_lower = seg["text"].lower()
                sid = speaker_ids[i]

                # Count agent signal matches
                for signal in AGENT_SIGNALS:
                    if signal in text_lower:
                        scores[sid] += 1

                # Count customer signal matches (add to the OTHER speaker's agent score)
                for signal in CUSTOMER_SIGNALS:
                    if signal in text_lower:
                        # Customer signals REDUCE this speaker's agent likelihood
                        scores[sid] -= 1

            # ── Step 3: Apply structural weights ──
            # Anchor bonus: first speaker gets +12 (agent usually initiates)
            anchor_id = speaker_ids[0]
            scores[anchor_id] += 12

            # Closer bonus: last speaker gets +6
            closer_id = speaker_ids[-1]
            scores[closer_id] += 6

            # ── Step 4: Global assignment ──
            if scores[0] >= scores[1]:
                speaker_map = {0: "Agent", 1: "Customer"}
            else:
                speaker_map = {0: "Customer", 1: "Agent"}

            logger.info(
                f"Speaker attribution: ID0={scores[0]} pts, ID1={scores[1]} pts | "
                f"Mapping: 0→{speaker_map[0]}, 1→{speaker_map[1]}"
            )

            # ── Build labeled transcript ──
            transcript = []
            for i, seg in enumerate(whisper_segments):
                transcript.append({
                    "speaker": speaker_map[speaker_ids[i]],
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })

            return transcript

        transcript = identify_speakers(result["segments"])

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

        # ── Step 5: Save to database ──
        try:
            call_id = save_call(
                filename=file.filename,
                file_size_bytes=file_size_bytes,
                response=response,
                weights=locals().get('scoring_weights')
            )
            response["call_id"] = call_id
            logger.info(f"Call saved to database with ID {call_id}")
        except Exception as e:
            logger.error(f"Failed to save call to database: {e}", exc_info=True)
            # Don't fail the request if DB save fails

        return response

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info("Temporary file cleaned up")


@app.get("/api/history")
async def api_history(limit: int = 10, offset: int = 0) -> List[Dict]:
    """Get recent analyzed calls, most recent first."""
    return get_history(limit=limit, offset=offset)


@app.get("/api/history/{call_id}")
async def api_call_detail(call_id: int) -> Dict:
    """Get full detail for a specific analyzed call."""
    result = get_call_detail(call_id)
    if result is None:
        return {"error": "Call not found"}
    return result


@app.get("/api/stats")
async def api_stats() -> Dict:
    """Get aggregate stats across all analyzed calls."""
    return get_stats()


@app.get("/api/report/{call_id}")
async def api_report(call_id: int):
    """Generate and stream a PDF report for a specific analyzed call."""
    call_data = get_call_detail(call_id)
    if call_data is None:
        return {"error": "Call not found"}

    try:
        pdf_bytes = generate_report(call_data)
        filename = call_data.get("filename", "report").rsplit('.', 1)[0]
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="NanoVox_{filename}_report.pdf"'
            }
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        return {"error": f"Report generation failed: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
