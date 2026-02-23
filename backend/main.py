from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import logging
import whisper
import tempfile
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NanoVox API",
    description="Call Intelligence Dashboard API",
    version="0.3.0"
)

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store Whisper model
whisper_model = None


# Global variable for sentiment pipeline
sentiment_pipeline = None

# Global variable for sentiment analyzer
vader_analyzer = None

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


def analyze_call_insights(transcript_segments: list) -> Dict:
    """
    Analyze call using VADER for sentiment and heuristics for other metrics.
    
    Returns structured insights.
    """
    logger.info("="*80)
    logger.info("STARTING VADER SENTIMENT ANALYSIS")
    logger.info("="*80)
    
    if not transcript_segments:
        logger.warning("No transcript segments provided")
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "key_points": [],
            "action_items": [],
            "summary": "No audio transcribed."
        }

    # 1. Calculate Customer Frustration (using VADER)
    # Filter customer segments
    customer_segments = [s for s in transcript_segments if s["speaker"] == "Customer"]
    
    customer_frustration_score = 0.0
    if customer_segments:
        logger.info(f"Analyzing {len(customer_segments)} customer segments for frustration...")
        
        compound_scores = []
        for seg in customer_segments:
            text = seg["text"]
            scores = vader_analyzer.polarity_scores(text)
            compound = scores['compound']
            
            # Logic: If compound is negative, it contributes to frustration.
            # Compound is -1.0 to 1.0.
            # We map -1.0 (Most Negative) -> 10.0 (High Frustration)
            # We map 0.0 or positive -> 0.0 (No Frustration)
            
            if compound < -0.05: # Threshold for 'negative' in VADER
                # Map -0.05...-1.0 to 0...10 implies: abs(compound) * 10
                frustration = abs(compound) * 10.0
                compound_scores.append(frustration)
            else:
                compound_scores.append(0.0)
        
        # Average frustration across all customer segments
        if compound_scores:
            customer_frustration_score = sum(compound_scores) / len(compound_scores)
        
        logger.info(f"Customer frustration score: {customer_frustration_score:.2f}/10")
    else:
        logger.info("No customer segments found. Defaulting frustration to 0.")

    # 2. Calculate Agent Empathy
    # Simple heuristic: count empathy words in Agent segments
    agent_texts = [s["text"].lower() for s in transcript_segments if s["speaker"] == "Agent"]
    empathy_keywords = ['sorry', 'apologize', 'understand', 'help', 'assist', 'thank', 'appreciate', 'please']
    
    agent_empathy_score = 5.0 # Base score
    if agent_texts:
        match_count = 0
        total_words = 0
        for text in agent_texts:
            total_words += len(text.split())
            if any(k in text for k in empathy_keywords):
                match_count += 1
        
        # Boost score based on density of empathetic utterances
        # if 30% of utterances have empathy words -> +5 points
        if len(agent_texts) > 0:
             empathy_ratio = match_count / len(agent_texts)
             agent_empathy_score = 2.0 + (empathy_ratio * 8.0) # Min 2, Max 10
             agent_empathy_score = min(10.0, agent_empathy_score)
        
        logger.info(f"Agent empathy score: {agent_empathy_score:.2f}/10 (matches: {match_count}/{len(agent_texts)})")

    # 3. Determine Resolution Status
    # Check last few segments for resolution keywords
    is_resolved = False
    if transcript_segments:
        last_segments = transcript_segments[-3:] # Look at last 3 interaction turns
        combined_last_text = " ".join([s["text"].lower() for s in last_segments])
        resolution_keywords = ['thank you', 'thanks', 'great', 'buh-bye', 'bye', 'helped', 'fixed', 'works now']
        
        if any(k in combined_last_text for k in resolution_keywords):
            is_resolved = True
    
    logger.info(f"Call resolution status: {is_resolved}")

    # 4. Map to Legacy API Structure
    # Map frustration to sentiment label
    overall_sentiment = "neutral"
    if customer_frustration_score > 6.0:
        overall_sentiment = "negative"
    elif customer_frustration_score < 3.0:
        overall_sentiment = "positive"
        
    return {
        "sentiment": overall_sentiment,
        "sentiment_score": round(customer_frustration_score, 2), # Using frustration as the main metric
        "key_points": [], # Cannot generate without LLM
        "action_items": [], # Cannot generate without LLM
        "summary": "Automated summary unavailable (Offline Mode)",
        # Extra fields (optional, helpful if frontend adapts)
        "customer_frustration": round(customer_frustration_score, 2),
        "agent_empathy": round(agent_empathy_score, 2),
        "call_resolution": is_resolved
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "message": "NanoVox API is running"}


@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)) -> Dict:
    """
    Analyze an audio file and return transcription with segments.
    
    Uses Whisper tiny model for ASR.
    """
    logger.info("\n" + "🔥"*40)
    logger.info("🔥 /ANALYZE ENDPOINT HIT - REQUEST RECEIVED 🔥")
    logger.info("🔥"*40)
    logger.info(f"Received file: {file.filename} ({file.content_type})")
    
    # Read file content
    contents = await file.read()
    file_size_bytes = len(contents)
    logger.info(f"File size: {file_size_bytes} bytes ({file_size_bytes / 1024:.2f} KB)")
    
    # Save to temporary file for Whisper processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(contents)
        temp_file_path = temp_file.name
    
    try:
        # Transcribe with Whisper
        logger.info("Starting transcription...")
        result = whisper_model.transcribe(temp_file_path)
        logger.info("Transcription complete!")
        
        # Heuristic speaker attribution
        def attribute_speaker(segment_text: str, segment_index: int, previous_speaker: str) -> str:
            """
            Attribute speaker using heuristic rules:
            1. First segment is Agent
            2. Speakers alternate by default
            3. Complaint keywords -> Customer
            4. Help/apology keywords -> Agent
            """
            text_lower = segment_text.lower()
            
            # Complaint keywords indicate Customer
            complaint_keywords = ['problem', 'issue', 'angry', 'frustrated', 'complaint', 
                                 'upset', 'disappointed', 'terrible', 'awful', 'bad']
            if any(keyword in text_lower for keyword in complaint_keywords):
                return "Customer"
            
            # Help/apology keywords indicate Agent
            agent_keywords = ['help', 'assist', 'sorry', 'apologize', 'understand', 
                            'resolve', 'fix', 'support', 'service', 'thank you for']
            if any(keyword in text_lower for keyword in agent_keywords):
                return "Agent"
            
            # Default: alternate speakers
            if segment_index == 0:
                return "Agent"  # First segment is Agent
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
        
        # Analyze call insights with VADER
        logger.info("\n" + "="*80)
        logger.info("INVOKING VADER FOR CALL INSIGHTS")
        logger.info("="*80)
        
        try:
            insights = analyze_call_insights(transcript)
            logger.info("="*80)
            logger.info("VADER ANALYSIS COMPLETED SUCCESSFULLY")
            logger.info("="*80)
        except Exception as e:
            logger.error(f"Insights analysis failed: {str(e)}")
            insights = {
                "error": str(e),
                "message": "Call insights unavailable.",
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "key_points": [],
                "action_items": [],
                "summary": "Analysis failed."
            }
        
        # Build response
        response = {
            "filename": file.filename,
            "file_size_bytes": file_size_bytes,
            "transcription": {
                "text": result["text"].strip(),
                "transcript": transcript  # Changed from "segments" to "transcript"
            },
            "insights": insights
        }
        
        return response
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            logger.info("Temporary file cleaned up")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
