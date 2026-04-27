from fastapi import FastAPI, File, UploadFile, Form, HTTPException
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
from pydantic import BaseModel, Field

from modules import talk_ratio_analyzer, sentiment_analyzer, slm_analyzer
from utils.config_loader import load_config, get_max_upload_size_bytes
from utils.logger import LoggerFactory, get_logger
from scoring_engine import calculate_score
from parameter_registry import get_available_parameters, load_profile_config, get_default_weights
from database import init_db, save_call, get_history, get_call_detail, get_stats
from report_generator import generate_report
from models import ParameterResult, TranscriptSegment, CallSummary, Stats

logger = get_logger(__name__)

# Load configuration from backend_config.json
config = load_config()
MAX_UPLOAD_SIZE = get_max_upload_size_bytes()

# Initialize centralized logging with daily rotation
log_config = config['logging']
LoggerFactory.setup(
    log_dir="logs",
    log_level=log_config['level'],
    retention_days=7  # Keep last 7 days of logs
)
logger = get_logger(__name__)

app = FastAPI(
    title="NanoVox API",
    description="Call Intelligence Dashboard API",
    version="1.0.0"
)

# CORS middleware to allow frontend requests (loaded from config)
cors_config = config['cors']
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config['allowed_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store Whisper model
whisper_model = None

# Global variable for VADER analyzer
vader_analyzer = None

# Thread pool for running analyzers concurrently (configured from backend_config.json)
thread_config = config['threading']
_executor = ThreadPoolExecutor(max_workers=thread_config['max_workers'])


@app.on_event("startup")
async def load_models():
    """Load ML models at startup"""
    global whisper_model, vader_analyzer

    logger.info("loading models...")

    # Load Whisper (configured from backend_config.json)
    ml_config = config['ml_models']
    whisper_name = ml_config['whisper_model']
    logger.info(f"Loading Whisper {whisper_name} model...")
    whisper_model = whisper.load_model(whisper_name)
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
    Run all analyzers and return their results.
    Each analyzer is independent — if one fails, the others still return.

    Pipeline:
      1. Talk Ratio    — phase-aware time-based analysis (keyword-free)
      2. Sentiment     — VADER compound score with tiered frustration penalty
      3. Empathy       — phi3.5 via Ollama
      4. Resolution    — phi3.5 via Ollama
      5. SLM Sentiment — phi3.5 true sentiment (sarcasm-aware override)

    After collecting results, the SLM Sentiment Override rule is applied:
      - If SLM says Negative but VADER scored > 40  → force VADER score to 15
      - If SLM says Positive  but VADER scored < 50  → force VADER score to 85
    This corrects VADER blindspots with sarcasm and indirect negative language.
    """
    logger.info(f"🧪 [DEBUG] _run_analyzers triggered with {len(transcript)} segments")
    results = []

   
    # 1. Talk Ratio
    try:
        results.append(talk_ratio_analyzer.analyze(transcript, profile_config))
        logger.info("🧪 [DEBUG] Talk ratio analyzer finished")
    except Exception as e:
        logger.error(f"Talk ratio analyzer failed: {e}")

    # 2. Sentiment (needs VADER instance)
    try:
        results.append(sentiment_analyzer.analyze(transcript, profile_config, vader_analyzer))
        logger.info("🧪 [DEBUG] Sentiment analyzer finished")
    except Exception as e:
        logger.error(f"Sentiment analyzer failed: {e}")

    # 3 + 4 + 5. Empathy + Resolution + SLM Sentiment via SLM (single Ollama call)
    # If Ollama is unreachable, slm_analyzer returns neutral fallback scores internally.
    try:
        slm_results = slm_analyzer.analyze(transcript, profile_config)
        results.extend(slm_results)
        logger.info(f"🧪 [DEBUG] SLM analyzer returned {len(slm_results)} results")
    except Exception as e:
        logger.error(f"SLM analyzer failed entirely: {e} — pipeline continues without empathy/resolution", exc_info=True)

    logger.info(f"🧪 [DEBUG] All analyzers finished, collected {len(results)} results before SLM override")

    # ── SLM Sentiment Override ────────────────────────────────────────────────
    # Find the VADER sentiment result and SLM sentiment result by name
    vader_result    = next((r for r in results if r.name == "sentiment"), None)
    slm_sent_result = next((r for r in results if r.name == "slm_sentiment"), None)

    if vader_result and slm_sent_result:
        slm_sentiment = slm_sent_result.metadata.get("true_sentiment", "Neutral")
        vader_score   = vader_result.score

        if slm_sentiment == "Negative" and vader_score > 40.0:
            logger.warning(
                f"SLM Override: VADER={vader_score:.1f} but SLM=Negative — "
                f"forcing VADER score to 15.0"
            )
            vader_result.score   = 15.0
            vader_result.penalty = 85.0
            vader_result.metadata["slm_override"]    = True
            vader_result.metadata["override_reason"] = (
                "SLM detected underlying negative context/sarcasm"
            )

        elif slm_sentiment == "Positive" and vader_score < 50.0:
            logger.warning(
                f"SLM Override: VADER={vader_score:.1f} but SLM=Positive — "
                f"forcing VADER score to 85.0"
            )
            vader_result.score   = 85.0
            vader_result.penalty = 15.0
            vader_result.metadata["slm_override"]    = True
            vader_result.metadata["override_reason"] = (
                "SLM detected genuinely positive sentiment underscored by VADER"
            )
        else:
            vader_result.metadata["slm_override"] = False
            logger.info(
                f"SLM Override: no override needed "
                f"(VADER={vader_score:.1f}, SLM={slm_sentiment})"
            )

    return results



@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "message": "NanoVox API is running"}


# @app.get("/api/parameters/available")
# async def get_parameters():
#     """Return all available analysis parameters for dynamic UI generation."""
#     return {"parameters": get_availaebl_parameters()}


@app.get("/api/weights/defaults")
async def get_default_weights_endpoint():
    """Return the default Sales profile weights."""
    return {"weights": get_default_weights()}


class RescoreRequest(BaseModel):
    """Request body for the rescore endpoint."""
    analyzer_results: List[ParameterResult] = Field(..., description="Cached analyzer outputs from a previous analysis")
    weights: Dict[str, float] = Field(..., description="Map of parameter name to weight percentage")

    model_config = {
        "json_schema_extra": {
            "example": {
                "analyzer_results": [
                    {
                        "name": "talk_ratio",
                        "display_name": "Talk Ratio",
                        "icon": "🗣️",
                        "raw_value": 0.65,
                        "score": 85.0,
                        "penalty": 15.0,
                        "metadata": {}
                    }
                ],
                "weights": {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40}
            }
        }
    }


class TestAnalysisRequest(BaseModel):
    """
    Request body for the /api/test-analysis endpoint.
    """
    transcript: List[TranscriptSegment] = Field(..., description="List of speaker segments")
    weights: Optional[Dict[str, float]] = Field(None, description="Optional custom weights")
    profile: Optional[str] = Field("complaints", description="The analysis profile to use")

    model_config = {
        "json_schema_extra": {
            "example": {
                "transcript": [
                    {"speaker": "Agent", "start": 0.0, "end": 5.0, "text": "Thank you for calling SkyWays Premium Support. My name is David. How can I assist you today?"},
                    {"speaker": "Customer", "start": 5.5, "end": 18.0, "text": "David, I am absolutely furious. I just got an email saying my flight to London tonight is cancelled."},
                    {"speaker": "Agent", "start": 18.5, "end": 26.0, "text": "I am so incredibly sorry to hear that. Let me pull up your itinerary immediately."},
                ],
                "weights": {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40},
                "profile": "complaints"
            }
        }
    }


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
        # Convert Pydantic models to dicts so analyzers can access them via keys
        transcript_dicts = [s.model_dump() for s in request.transcript]

        logger.info(f"🧪 [DEBUG] Calling _run_analyzers via executor with {len(transcript_dicts)} dicts")
        try:
            loop = asyncio.get_event_loop()
            analyzer_results = await loop.run_in_executor(
                _executor, _run_analyzers, transcript_dicts, profile_config
            )
            logger.info(f"🧪 [DEBUG] Executor returned analyzer_results (count={len(analyzer_results)})")
            for idx, res in enumerate(analyzer_results):
                logger.info(f"🧪 [DEBUG] Result {idx}: {res.name} (penalty={res.penalty})")
        except Exception as e:
            logger.error(f"🧪 [DEBUG] Executor failed with exception: {e}", exc_info=True)
            raise

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
        results = request.analyzer_results
        call_score = calculate_score(results, request.weights, "Sales")
        return call_score.model_dump()
    except Exception as e:
        logger.error(f"Rescore failed: {e}", exc_info=True)
        return {"error": str(e), "message": "Rescoring failed"}


@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(..., description="Audio file to analyze (.wav, .mp3, .m4a)"),
    weights: Optional[str] = Form(None, description="Optional JSON string of custom weights", example='{"talk_ratio":5,"sentiment":35,"empathy":20,"resolution":40}')
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

    if file_size_bytes > MAX_UPLOAD_SIZE:
        logger.error(f"File too large: {file_size_bytes} bytes")
        raise HTTPException(
            status_code=413,
            detail=f"File is too large ({file_size_bytes / (1024 * 1024):.1f}MB). Maximum allowed is 50MB."
        )

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
                    # Check for a natural speaker change via pause gap (configured from backend_config.json)
                    speaker_config = config['speaker_detection']
                    gap = seg["start"] - whisper_segments[i - 1]["end"]
                    if gap > speaker_config['pause_gap_seconds']:
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
            # Anchor bonus: first speaker gets bonus (agent usually initiates)
            speaker_config = config['speaker_detection']
            anchor_id = speaker_ids[0]
            scores[anchor_id] += speaker_config['anchor_bonus_points']

            # Closer bonus: last speaker gets bonus
            closer_id = speaker_ids[-1]
            scores[closer_id] += speaker_config['closer_bonus_points']

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

        # ── Step 2: Minimal insights stub (legacy field retained for API compatibility) ──
        insights = {
            "sentiment": "neutral", "sentiment_score": 0.0,
            "key_points": [], "action_items": [],
            "summary": "",
            "customer_frustration": 0.0, "agent_empathy": 0.0,
            "call_resolution": False
        }

        # ── Step 3: New parameter-based scoring ──
        analysis = None
        try:
            profile_name = config['profiles']['default']
            profile_config = load_profile_config(profile_name)

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


@app.get("/api/history", response_model=List[CallSummary])
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


@app.get("/api/stats", response_model=Stats)
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
    server_config = config['server']
    uvicorn.run(app, host=server_config['host'], port=server_config['port'])
